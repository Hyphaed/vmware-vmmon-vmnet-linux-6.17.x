#!/bin/bash
# Script para verificar el estado de los módulos VMware
# Autor: Hyphaed

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }
warning() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

echo ""
info "=== Verificación de Módulos VMware ==="
echo ""

CURRENT_KERNEL=$(uname -r)
info "Kernel actual: $CURRENT_KERNEL"
echo ""

# Verificar si los módulos están compilados
info "Verificando archivos de módulos..."
if [ -f "/lib/modules/$CURRENT_KERNEL/misc/vmmon.ko" ]; then
    log "vmmon.ko encontrado"
    ls -lh "/lib/modules/$CURRENT_KERNEL/misc/vmmon.ko" | sed 's/^/  /'
else
    error "vmmon.ko NO encontrado"
fi

if [ -f "/lib/modules/$CURRENT_KERNEL/misc/vmnet.ko" ]; then
    log "vmnet.ko encontrado"
    ls -lh "/lib/modules/$CURRENT_KERNEL/misc/vmnet.ko" | sed 's/^/  /'
else
    error "vmnet.ko NO encontrado"
fi

echo ""

# Verificar si los módulos están cargados
info "Verificando módulos cargados..."
if lsmod | grep -q vmmon; then
    log "vmmon está cargado"
    lsmod | grep vmmon | sed 's/^/  /'
else
    warning "vmmon NO está cargado"
    info "Intenta: sudo modprobe vmmon"
fi

if lsmod | grep -q vmnet; then
    log "vmnet está cargado"
    lsmod | grep vmnet | sed 's/^/  /'
else
    warning "vmnet NO está cargado"
    info "Intenta: sudo modprobe vmnet"
fi

echo ""

# Verificar información de los módulos
info "Información de módulos:"
if lsmod | grep -q vmmon; then
    echo ""
    echo "  === vmmon ==="
    modinfo vmmon 2>/dev/null | grep -E "(filename|version|description|author|license)" | sed 's/^/  /'
fi

if lsmod | grep -q vmnet; then
    echo ""
    echo "  === vmnet ==="
    modinfo vmnet 2>/dev/null | grep -E "(filename|version|description|author|license)" | sed 's/^/  /'
fi

echo ""

# Verificar servicios VMware
info "Verificando servicios VMware..."
if systemctl is-active --quiet vmware 2>/dev/null; then
    log "Servicio vmware está activo"
else
    warning "Servicio vmware no está activo"
    info "Intenta: sudo systemctl start vmware"
fi

echo ""

# Verificar errores en dmesg
info "Verificando errores en dmesg..."
ERRORS=$(dmesg | grep -i vmware | grep -i error | tail -5)
if [ -z "$ERRORS" ]; then
    log "No se encontraron errores recientes"
else
    warning "Errores encontrados:"
    echo "$ERRORS" | sed 's/^/  /'
fi

echo ""

# Resumen
if lsmod | grep -q vmmon && lsmod | grep -q vmnet; then
    echo -e "${GREEN}✓ Módulos VMware funcionando correctamente${NC}"
    echo ""
    log "Puedes iniciar VMware Workstation"
else
    echo -e "${YELLOW}⚠ Algunos módulos no están cargados${NC}"
    echo ""
    warning "Soluciones posibles:"
    echo "  1. Cargar módulos: sudo modprobe vmmon && sudo modprobe vmnet"
    echo "  2. Reiniciar servicios: sudo systemctl restart vmware"
    echo "  3. Recompilar módulos: sudo bash install-vmware-modules.sh"
fi

echo ""
