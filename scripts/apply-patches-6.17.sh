#!/bin/bash
# Script para aplicar parches específicos de kernel 6.17
# Soluciona errores de objtool

VMMON_DIR="$1"
VMNET_DIR="$2"

if [ -z "$VMMON_DIR" ] || [ ! -d "$VMMON_DIR" ]; then
    echo "Error: Directorio vmmon-only no especificado o no existe"
    exit 1
fi

if [ -z "$VMNET_DIR" ] || [ ! -d "$VMNET_DIR" ]; then
    echo "Error: Directorio vmnet-only no especificado o no existe"
    exit 1
fi

echo "Aplicando parches para kernel 6.17..."

# Parche 1: Modificar Makefile.kernel para deshabilitar objtool
cat > "$VMMON_DIR/Makefile.kernel" << 'EOF'
#!/usr/bin/make -f
##########################################################
# Copyright (c) 1998-2024 Broadcom. All Rights Reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation version 2 and no later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
##########################################################

CC_OPTS += -DVMMON -DVMCORE

INCLUDE := -I$(SRCROOT)/include -I$(SRCROOT)/include/x86 -I$(SRCROOT)/common -I$(SRCROOT)/linux
ccflags-y := $(CC_OPTS) $(INCLUDE)

obj-m += $(DRIVER).o

$(DRIVER)-y := $(subst $(SRCROOT)/, , $(patsubst %.c, %.o, \
		$(wildcard $(SRCROOT)/linux/*.c $(SRCROOT)/common/*.c \
		$(SRCROOT)/bootstrap/*.c)))

# Deshabilitar objtool para archivos problemáticos en kernel 6.17+
OBJECT_FILES_NON_STANDARD_common/phystrack.o := y
OBJECT_FILES_NON_STANDARD_common/task.o := y
OBJECT_FILES_NON_STANDARD := y

clean:
	rm -rf $(wildcard $(DRIVER).mod.c $(DRIVER).ko .tmp_versions \
		Module.symvers Modules.symvers Module.markers modules.order \
		$(foreach dir,linux/ common/ bootstrap/ \
		./,$(addprefix $(dir),.*.cmd .*.o.flags *.o)))
EOF

echo "✓ Makefile.kernel parcheado"

# Parche 2: Eliminar returns innecesarios en phystrack.c
sed -i '324s/return;$//' "$VMMON_DIR/common/phystrack.c"
sed -i '368s/return;$//' "$VMMON_DIR/common/phystrack.c"

echo "✓ phystrack.c parcheado"

# Parche 3: Verificar si task.c necesita parches
if grep -q "return;" "$VMMON_DIR/common/task.c" 2>/dev/null; then
    # Eliminar returns innecesarios en funciones void
    sed -i '/^void.*{$/,/^}$/ { /^   return;$/d }' "$VMMON_DIR/common/task.c"
    echo "✓ task.c parcheado"
fi

# Parche 4: Parchear Makefile.kernel de vmnet para deshabilitar objtool
# Agregar las líneas de objtool al Makefile.kernel existente
if ! grep -q "OBJECT_FILES_NON_STANDARD" "$VMNET_DIR/Makefile.kernel"; then
    # Buscar la línea con obj-m y agregar después
    sed -i '/^obj-m += \$(DRIVER)\.o/a\\n# Deshabilitar objtool para archivos problemáticos en kernel 6.17+\nOBJECT_FILES_NON_STANDARD_userif.o := y\nOBJECT_FILES_NON_STANDARD := y' "$VMNET_DIR/Makefile.kernel"
    echo "✓ vmnet Makefile.kernel parcheado"
else
    echo "✓ vmnet Makefile.kernel ya tiene parches de objtool"
fi

echo "✓ Parches para kernel 6.17 aplicados exitosamente"
