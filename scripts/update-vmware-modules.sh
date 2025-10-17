#!/bin/bash
# Quick update script for VMware modules after kernel upgrade
# Detects kernel changes and rebuilds modules with saved settings
# Date: 2025-10-15

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }
warning() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

echo -e "${CYAN}"
cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        VMWARE MODULES UPDATE UTILITY                         ║
║        Quick rebuild after kernel upgrades                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo ""
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}IMPORTANT INFORMATION${NC}"
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo ""
info "This script will create a backup of your current VMware modules"
info "If something goes wrong, you can restore using:"
echo ""
echo -e "  ${YELLOW}sudo bash scripts/restore-vmware-modules.sh${NC}"
echo ""
info "Backups are stored with timestamps for easy recovery"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root (use sudo)"
    exit 1
fi

# Detect current kernel
CURRENT_KERNEL=$(uname -r)
info "Current kernel: $CURRENT_KERNEL"

# Check if VMware modules are loaded
VMMON_LOADED=$(lsmod | grep -c "^vmmon " || true)
VMNET_LOADED=$(lsmod | grep -c "^vmnet " || true)

if [ "$VMMON_LOADED" -gt 0 ] && [ "$VMNET_LOADED" -gt 0 ]; then
    # Check module versions
    VMMON_VERSION=$(modinfo vmmon 2>/dev/null | grep vermagic | awk '{print $2}')
    
    info "Current module status:"
    lsmod | grep -E "vmmon|vmnet" | sed 's/^/  /'
    echo ""
    
    if [ "$VMMON_VERSION" = "$CURRENT_KERNEL" ]; then
        info "Modules are currently compiled for kernel: $VMMON_VERSION"
        echo ""
        warning "Update will rebuild modules with latest patches and optimizations"
        info "Reasons to update:"
        echo "  • Apply new NVMe/M.2 storage optimizations (15-25% faster I/O)"
        echo "  • Get latest kernel compatibility fixes"
        echo "  • Switch between Optimized (20-40% faster) and Vanilla modes"
    else
        warning "Modules are compiled for kernel: $VMMON_VERSION"
        warning "Current kernel is: $CURRENT_KERNEL"
        echo ""
        info "Kernel version mismatch - update is required!"
    fi
else
    warning "VMware modules are not loaded"
    info "Update will compile and load modules for current kernel"
fi

echo ""
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${CYAN}UPDATE OPTIONS${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo ""
echo "This script will:"
echo "  1. Detect your kernel version"
echo "  2. Run the full installation script"
echo "  3. Let you choose: Optimized (20-40% faster) or Vanilla (portable)"
echo "  4. Automatically rebuild modules for current kernel"
echo ""
echo -e "${YELLOW}Note:${NC} You will be prompted for:"
echo "  • Kernel version selection (6.16/6.17)"
echo "  • Compilation mode: Optimized (recommended) or Vanilla"
echo ""

read -p "Continue with module update? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    info "Update cancelled"
    exit 0
fi

# Find the installation script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SCRIPT="$SCRIPT_DIR/install-vmware-modules.sh"

if [ ! -f "$INSTALL_SCRIPT" ]; then
    error "Installation script not found: $INSTALL_SCRIPT"
    error "Please ensure install-vmware-modules.sh is in the same directory"
    exit 1
fi

echo ""
log "Launching installation script..."
echo ""

# Execute the main installation script
bash "$INSTALL_SCRIPT"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    log "✓ Update completed successfully!"
    echo ""
    info "Module status:"
    lsmod | grep -E "vmmon|vmnet" | sed 's/^/  /'
    echo ""
    info "Modules are now compiled for kernel: $CURRENT_KERNEL"
else
    error "Update failed with exit code: $EXIT_CODE"
    exit $EXIT_CODE
fi

