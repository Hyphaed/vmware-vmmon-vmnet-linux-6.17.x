#!/bin/bash
# Script automatizado para instalar módulos VMware en kernel 6.17.x
# Autor: Hyphaed
# Licencia: GPL v2

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }
warning() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

echo -e "${CYAN}"
cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     VMware Modules Installer for Linux Kernel 6.17.x        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    error "Este script debe ejecutarse como root"
    echo "Ejecuta: sudo bash $0"
    exit 1
fi

# Detectar kernel actual
CURRENT_KERNEL=$(uname -r)
KERNEL_MAJOR=$(echo $CURRENT_KERNEL | cut -d. -f1)
KERNEL_MINOR=$(echo $CURRENT_KERNEL | cut -d. -f2)

log "Kernel detectado: $CURRENT_KERNEL"

# Verificar que es kernel 6.17.x
if [ "$KERNEL_MAJOR" != "6" ] || [ "$KERNEL_MINOR" != "17" ]; then
    warning "Este script está diseñado para kernel 6.17.x"
    warning "Tu kernel es $CURRENT_KERNEL"
    read -p "¿Deseas continuar de todos modos? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        info "Instalación cancelada"
        exit 0
    fi
fi

# Verificar que VMware está instalado
if [ ! -d "/usr/lib/vmware/modules/source" ]; then
    error "VMware Workstation no está instalado"
    error "Instala VMware Workstation primero"
    exit 1
fi

log "VMware Workstation detectado"

# Verificar kernel headers
if [ ! -d "/lib/modules/$CURRENT_KERNEL/build" ]; then
    error "Kernel headers no instalados"
    info "Instala los headers con:"
    echo "  Ubuntu/Debian: sudo apt install linux-headers-\$(uname -r)"
    echo "  Fedora/RHEL: sudo dnf install kernel-devel"
    echo "  Arch: sudo pacman -S linux-headers"
    exit 1
fi

log "Kernel headers encontrados"

# Verificar herramientas de compilación
if ! command -v gcc &> /dev/null; then
    error "GCC no está instalado"
    info "Instala build-essential o equivalent"
    exit 1
fi

if ! command -v make &> /dev/null; then
    error "Make no está instalado"
    info "Instala build-essential o equivalent"
    exit 1
fi

log "Herramientas de compilación verificadas"

# Crear directorio temporal
WORK_DIR="/tmp/vmware_build_$$"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

info "Directorio de trabajo: $WORK_DIR"

# Extraer módulos originales
log "Extrayendo módulos VMware..."
tar -xf /usr/lib/vmware/modules/source/vmmon.tar
tar -xf /usr/lib/vmware/modules/source/vmnet.tar

# Clonar repositorio base (6.16.x) si es necesario
info "Descargando parches base..."
if ! git clone --depth 1 https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x.git 2>/dev/null; then
    warning "No se pudo clonar repositorio base, continuando sin parches 6.16"
else
    # Aplicar parches base de 6.16
    REPO_SOURCE="$WORK_DIR/vmware-vmmon-vmnet-linux-6.16.x/modules/17.6.4/source"
    if [ -d "$REPO_SOURCE" ]; then
        info "Aplicando parches base (6.16)..."
        
        # Aplicar parches vmmon
        [ -f "$REPO_SOURCE/vmmon-only/Makefile" ] && cp -f "$REPO_SOURCE/vmmon-only/Makefile" "$WORK_DIR/vmmon-only/"
        [ -f "$REPO_SOURCE/vmmon-only/linux/driver.c" ] && cp -f "$REPO_SOURCE/vmmon-only/linux/driver.c" "$WORK_DIR/vmmon-only/linux/"
        [ -f "$REPO_SOURCE/vmmon-only/linux/hostif.c" ] && cp -f "$REPO_SOURCE/vmmon-only/linux/hostif.c" "$WORK_DIR/vmmon-only/linux/"
        
        # Aplicar parches vmnet
        [ -f "$REPO_SOURCE/vmnet-only/Makefile" ] && cp -f "$REPO_SOURCE/vmnet-only/Makefile" "$WORK_DIR/vmnet-only/"
        [ -f "$REPO_SOURCE/vmnet-only/Makefile.kernel" ] && cp -f "$REPO_SOURCE/vmnet-only/Makefile.kernel" "$WORK_DIR/vmnet-only/"
        [ -f "$REPO_SOURCE/vmnet-only/driver.c" ] && cp -f "$REPO_SOURCE/vmnet-only/driver.c" "$WORK_DIR/vmnet-only/"
        [ -f "$REPO_SOURCE/vmnet-only/smac_compat.c" ] && cp -f "$REPO_SOURCE/vmnet-only/smac_compat.c" "$WORK_DIR/vmnet-only/"
        
        log "Parches base aplicados"
    fi
fi

# Aplicar parches específicos para 6.17
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
info "Aplicando parches específicos para kernel 6.17..."

if [ -f "$SCRIPT_DIR/apply-patches-6.17.sh" ]; then
    bash "$SCRIPT_DIR/apply-patches-6.17.sh" "$WORK_DIR/vmmon-only" "$WORK_DIR/vmnet-only"
else
    error "Script de parches no encontrado: $SCRIPT_DIR/apply-patches-6.17.sh"
    exit 1
fi

# Compilar vmmon
log "Compilando vmmon..."
cd "$WORK_DIR/vmmon-only"
make clean 2>/dev/null || true
if ! make VM_UNAME=$CURRENT_KERNEL -j$(nproc); then
    error "Error compilando vmmon"
    exit 1
fi
log "vmmon compilado exitosamente"

# Compilar vmnet
log "Compilando vmnet..."
cd "$WORK_DIR/vmnet-only"
make clean 2>/dev/null || true
if ! make VM_UNAME=$CURRENT_KERNEL -j$(nproc); then
    error "Error compilando vmnet"
    exit 1
fi
log "vmnet compilado exitosamente"

# Instalar módulos
log "Instalando módulos..."
mkdir -p "/lib/modules/$CURRENT_KERNEL/misc/"
cp "$WORK_DIR/vmmon-only/vmmon.ko" "/lib/modules/$CURRENT_KERNEL/misc/"
cp "$WORK_DIR/vmnet-only/vmnet.ko" "/lib/modules/$CURRENT_KERNEL/misc/"

# Actualizar dependencias
info "Actualizando dependencias de módulos..."
depmod -a $CURRENT_KERNEL

# Cargar módulos
info "Cargando módulos..."
modprobe vmmon 2>/dev/null || true
modprobe vmnet 2>/dev/null || true

# Verificar instalación
echo ""
log "Verificando instalación..."
echo ""

if lsmod | grep -q vmmon; then
    log "vmmon cargado correctamente"
else
    warning "vmmon no está cargado"
fi

if lsmod | grep -q vmnet; then
    log "vmnet cargado correctamente"
else
    warning "vmnet no está cargado"
fi

echo ""
info "Módulos instalados en:"
ls -lh /lib/modules/$CURRENT_KERNEL/misc/vm*.ko 2>/dev/null | sed 's/^/  /'

# Limpiar
cd /
rm -rf "$WORK_DIR"

echo ""
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✓ INSTALACIÓN COMPLETADA${NC}"
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo ""

info "Siguiente paso:"
echo "  1. Reinicia VMware Workstation"
echo "  2. Inicia una máquina virtual para verificar"
echo ""

log "¡Módulos VMware instalados para kernel $CURRENT_KERNEL!"
