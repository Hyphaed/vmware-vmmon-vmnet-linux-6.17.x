#!/bin/bash
# Comprehensive VMware Modules Test Script
# Verifies modules are correctly compiled, loaded, and running

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
HYPHAED_GREEN='\033[38;2;176;213;106m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }
warning() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

echo -e "${HYPHAED_GREEN}"
cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        VMWARE MODULES COMPREHENSIVE TEST SUITE               ║
║         Verification of Installation & Runtime               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Información del sistema
echo -e "${YELLOW}📋 INFORMACIÓN DEL SISTEMA${NC}"
echo "  Kernel: $(uname -r)"
echo "  Compilador: $(cat /proc/version | grep -oP '(?<=\().*?(?=\))' | head -1)"
echo "  VMWare: $(vmware --version 2>/dev/null || echo 'No detectado')"
echo ""

# Verificar módulos cargados
echo -e "${YELLOW}🔍 MÓDULOS CARGADOS${NC}"
if lsmod | grep -q vmmon; then
    echo -e "  ${GREEN}✓${NC} vmmon: $(lsmod | grep vmmon | awk '{print $2}') bytes"
else
    echo -e "  ${RED}✗${NC} vmmon: No cargado"
fi

if lsmod | grep -q vmnet; then
    echo -e "  ${GREEN}✓${NC} vmnet: $(lsmod | grep vmnet | awk '{print $2}') bytes"
else
    echo -e "  ${RED}✗${NC} vmnet: No cargado"
fi
echo ""

# Información de módulos
echo -e "${YELLOW}📦 INFORMACIÓN DE MÓDULOS${NC}"
if modinfo vmmon &>/dev/null; then
    echo "  vmmon:"
    modinfo vmmon | grep -E "filename|version|vermagic" | sed 's/^/    /'
else
    echo -e "  ${RED}✗${NC} vmmon: No encontrado"
fi
echo ""

if modinfo vmnet &>/dev/null; then
    echo "  vmnet:"
    modinfo vmnet | grep -E "filename|version|vermagic" | sed 's/^/    /'
else
    echo -e "  ${RED}✗${NC} vmnet: No encontrado"
fi
echo ""

# Verificar archivos de dispositivo
echo -e "${YELLOW}🔧 DISPOSITIVOS${NC}"
if [ -c /dev/vmmon ]; then
    echo -e "  ${GREEN}✓${NC} /dev/vmmon: $(ls -l /dev/vmmon | awk '{print $1, $3, $4}')"
else
    echo -e "  ${RED}✗${NC} /dev/vmmon: No existe"
fi

if [ -c /dev/vmnet0 ]; then
    echo -e "  ${GREEN}✓${NC} /dev/vmnet0: $(ls -l /dev/vmnet0 | awk '{print $1, $3, $4}')"
else
    echo -e "  ${RED}✗${NC} /dev/vmnet0: No existe"
fi
echo ""

# Servicios VMWare
echo -e "${YELLOW}⚙️  SERVICIOS VMWARE${NC}"
if systemctl is-active --quiet vmware.service; then
    echo -e "  ${GREEN}✓${NC} vmware.service: activo"
else
    echo -e "  ${RED}✗${NC} vmware.service: inactivo"
fi

if systemctl is-active --quiet vmware-USBArbitrator.service; then
    echo -e "  ${GREEN}✓${NC} vmware-USBArbitrator.service: activo"
else
    echo -e "  ${RED}✗${NC} vmware-USBArbitrator.service: inactivo"
fi
echo ""

# Verificar archivos tar
echo -e "${YELLOW}📁 ARCHIVOS FUENTE${NC}"
if [ -f /usr/lib/vmware/modules/source/vmmon.tar ]; then
    SIZE=$(du -h /usr/lib/vmware/modules/source/vmmon.tar | awk '{print $1}')
    echo -e "  ${GREEN}✓${NC} vmmon.tar: $SIZE"
else
    echo -e "  ${RED}✗${NC} vmmon.tar: No encontrado"
fi

if [ -f /usr/lib/vmware/modules/source/vmnet.tar ]; then
    SIZE=$(du -h /usr/lib/vmware/modules/source/vmnet.tar | awk '{print $1}')
    echo -e "  ${GREEN}✓${NC} vmnet.tar: $SIZE"
else
    echo -e "  ${RED}✗${NC} vmnet.tar: No encontrado"
fi
echo ""

# Backups disponibles
echo -e "${YELLOW}💾 BACKUPS DISPONIBLES${NC}"
if [ -d /usr/lib/vmware/modules/source/ ]; then
    BACKUPS=$(ls -d /usr/lib/vmware/modules/source/backup-* 2>/dev/null | wc -l)
    if [ $BACKUPS -gt 0 ]; then
        echo "  Total: $BACKUPS backups"
        ls -d /usr/lib/vmware/modules/source/backup-* 2>/dev/null | tail -3 | sed 's/^/    /'
    else
        echo "  No hay backups"
    fi
else
    echo "  Directorio no encontrado"
fi
echo ""

# Resumen
echo -e "${BLUE}═══════════════════════════════════════${NC}"
MODULES_OK=0
SERVICES_OK=0

lsmod | grep -q vmmon && lsmod | grep -q vmnet && MODULES_OK=1
systemctl is-active --quiet vmware.service && SERVICES_OK=1

if [ $MODULES_OK -eq 1 ] && [ $SERVICES_OK -eq 1 ]; then
    echo -e "${GREEN}✓ ESTADO: TODO CORRECTO${NC}"
    echo ""
    echo "VMWare Workstation está listo para usar"
else
    echo -e "${RED}✗ ESTADO: PROBLEMAS DETECTADOS${NC}"
    echo ""
    if [ $MODULES_OK -eq 0 ]; then
        echo "Solución: Recompila los módulos con:"
        echo "  sudo ./install-vmware-modules.sh"
    fi
    if [ $SERVICES_OK -eq 0 ]; then
        echo "Solución: Reinicia los servicios con:"
        echo "  sudo systemctl restart vmware.service"
    fi
fi
echo -e "${BLUE}═══════════════════════════════════════${NC}"
