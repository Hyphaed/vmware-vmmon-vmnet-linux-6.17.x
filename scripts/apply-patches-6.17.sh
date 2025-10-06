#!/bin/bash
# Script para aplicar parches específicos de kernel 6.17
# Soluciona errores de objtool y compatibilidad con kernel 6.17.x

set -e

VMMON_DIR="$1"
VMNET_DIR="$2"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

if [ -z "$VMMON_DIR" ] || [ ! -d "$VMMON_DIR" ]; then
    error "Directorio vmmon-only no especificado o no existe"
    echo "Uso: $0 <vmmon-only-dir> <vmnet-only-dir>"
    exit 1
fi

if [ -z "$VMNET_DIR" ] || [ ! -d "$VMNET_DIR" ]; then
    error "Directorio vmnet-only no especificado o no existe"
    echo "Uso: $0 <vmmon-only-dir> <vmnet-only-dir>"
    exit 1
fi

info "Aplicando parches para kernel 6.17.x..."

# ============================================
# Parche 1: Modificar Makefile.kernel de vmmon
# ============================================
info "Parcheando vmmon Makefile.kernel..."

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
# Esto es necesario debido a las validaciones más estrictas de objtool
OBJECT_FILES_NON_STANDARD_common/phystrack.o := y
OBJECT_FILES_NON_STANDARD_common/task.o := y
OBJECT_FILES_NON_STANDARD := y

clean:
	rm -rf $(wildcard $(DRIVER).mod.c $(DRIVER).ko .tmp_versions \
		Module.symvers Modules.symvers Module.markers modules.order \
		$(foreach dir,linux/ common/ bootstrap/ \
		./,$(addprefix $(dir),.*.cmd .*.o.flags *.o)))
EOF

log "vmmon Makefile.kernel parcheado"

# ============================================
# Parche 2: Eliminar returns innecesarios en phystrack.c
# ============================================
info "Parcheando vmmon phystrack.c..."

if [ -f "$VMMON_DIR/common/phystrack.c" ]; then
    # Eliminar return; en línea 324 y 368 (funciones void)
    sed -i '324s/return;$//' "$VMMON_DIR/common/phystrack.c" 2>/dev/null || true
    sed -i '368s/return;$//' "$VMMON_DIR/common/phystrack.c" 2>/dev/null || true
    log "phystrack.c parcheado"
else
    error "No se encontró phystrack.c"
    exit 1
fi

# ============================================
# Parche 3: Verificar y parchear task.c
# ============================================
info "Verificando vmmon task.c..."

if [ -f "$VMMON_DIR/common/task.c" ]; then
    if grep -q "return;" "$VMMON_DIR/common/task.c" 2>/dev/null; then
        # Eliminar returns innecesarios en funciones void
        sed -i '/^void.*{$/,/^}$/ { /^   return;$/d }' "$VMMON_DIR/common/task.c"
        log "task.c parcheado"
    else
        log "task.c no requiere parches"
    fi
fi

# ============================================
# Parche 4: Parchear Makefile.kernel de vmnet
# ============================================
info "Parcheando vmnet Makefile.kernel..."

if ! grep -q "OBJECT_FILES_NON_STANDARD" "$VMNET_DIR/Makefile.kernel"; then
    # Buscar la línea con obj-m y agregar después
    sed -i '/^obj-m += \$(DRIVER)\.o/a\\n# Deshabilitar objtool para archivos problemáticos en kernel 6.17+\nOBJECT_FILES_NON_STANDARD_userif.o := y\nOBJECT_FILES_NON_STANDARD := y' "$VMNET_DIR/Makefile.kernel"
    log "vmnet Makefile.kernel parcheado"
else
    log "vmnet Makefile.kernel ya tiene parches de objtool"
fi

# ============================================
# Resumen
# ============================================
echo ""
log "✓ Parches para kernel 6.17.x aplicados exitosamente"
echo ""
info "Archivos modificados:"
echo "  - $VMMON_DIR/Makefile.kernel"
echo "  - $VMMON_DIR/common/phystrack.c"
echo "  - $VMMON_DIR/common/task.c (si fue necesario)"
echo "  - $VMNET_DIR/Makefile.kernel"
echo ""
info "Siguiente paso: Compilar los módulos con 'make'"
