#!/bin/bash
# Uninstall VMware modules (vmmon and vmnet)
# Removes custom-compiled modules and restores system to clean state
# Date: 2025-10-17

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'
HYPHAED_GREEN='\033[38;2;176;213;106m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }
warning() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

# Animation
ANIMATION_PID=""
ANIMATION_ENABLED=false
[ -t 1 ] && command -v tput &>/dev/null && ANIMATION_ENABLED=true

start_animation() {
    [ "$ANIMATION_ENABLED" = false ] && return
    local frames=("    ╭─○" "   ╭──○" "  ╭───○" " ╭────○" "╭─────○" "│─────○" "╰─────○" " ╰────○" "  ╰───○" "   ╰──○" "    ╰─○" "    ○─╯" "    ○──╯" "    ○───╯" "    ○────╯" "    ○─────╯" "    ○─────│" "    ○─────╮" "    ○────╮" "    ○───╮" "    ○──╮" "    ○─╮")
    ( local cols=$(tput cols) frame_idx=0 total_frames=${#frames[@]}
      while true; do local x=$((cols - 15)) y=2; tput sc; tput cup $y $x
        echo -ne "${HYPHAED_GREEN}${frames[$frame_idx]}${NC}"; tput cup $((y + 1)) $((x + 1))
        echo -ne "${HYPHAED_GREEN}Hyphaed${NC}"; tput rc; frame_idx=$(( (frame_idx + 1) % total_frames )); sleep 0.1
      done ) &
    ANIMATION_PID=$!
}

stop_animation() {
    [ -n "$ANIMATION_PID" ] && { kill $ANIMATION_PID 2>/dev/null || true; wait $ANIMATION_PID 2>/dev/null || true; ANIMATION_PID=""
    [ "$ANIMATION_ENABLED" = true ] && { local cols=$(tput cols) x=$((cols - 15)) y=2
    tput sc; tput cup $y $x; echo -ne "          "; tput cup $((y + 1)) $x; echo -ne "          "; tput rc; }; }
}

trap stop_animation EXIT

echo -e "${CYAN}"
cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        VMWARE MODULES UNINSTALLER                            ║
║        Remove vmmon and vmnet modules                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

start_animation

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root (use sudo)"
    exit 1
fi

# Detect distribution
if [ -f /etc/fedora-release ]; then
    DISTRO="fedora"
    VMWARE_MOD_DIR="/usr/lib/vmware/modules/source"
elif [ -f /etc/gentoo-release ]; then
    DISTRO="gentoo"
    VMWARE_MOD_DIR="/opt/vmware/lib/vmware/modules/source"
elif [ -f /etc/debian_version ]; then
    DISTRO="debian"
    VMWARE_MOD_DIR="/usr/lib/vmware/modules/source"
else
    DISTRO="unknown"
    VMWARE_MOD_DIR="/usr/lib/vmware/modules/source"
fi

info "Distribution: $DISTRO"
info "VMware module directory: $VMWARE_MOD_DIR"

echo ""
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${RED}WARNING - UNINSTALL MODULES${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo ""

# Check current module status
CURRENT_KERNEL=$(uname -r)
info "Current kernel: $CURRENT_KERNEL"

VMMON_LOADED=$(lsmod | grep -c "^vmmon " || true)
VMNET_LOADED=$(lsmod | grep -c "^vmnet " || true)

if [ "$VMMON_LOADED" -gt 0 ] || [ "$VMNET_LOADED" -gt 0 ]; then
    info "Currently loaded VMware modules:"
    lsmod | grep -E "vmmon|vmnet" | sed 's/^/  /'
    echo ""
else
    warning "No VMware modules are currently loaded"
    echo ""
fi

echo -e "${YELLOW}This will:${NC}"
echo "  1. Unload vmmon and vmnet kernel modules"
echo "  2. Remove compiled modules from /lib/modules/$CURRENT_KERNEL/"
echo "  3. Update module dependencies"
echo ""
echo -e "${RED}Note:${NC} This will NOT remove VMware Workstation itself"
echo -e "${RED}Note:${NC} Backups in $VMWARE_MOD_DIR/backup-* will be preserved"
echo ""

read -p "Are you sure you want to uninstall VMware modules? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    info "Uninstall cancelled"
    exit 0
fi

echo ""
log "Starting uninstall process..."

# Step 1: Unload modules
echo ""
info "Step 1: Unloading modules..."

if [ "$VMNET_LOADED" -gt 0 ]; then
    info "Unloading vmnet..."
    rmmod vmnet 2>/dev/null || warning "Could not unload vmnet (may not be loaded)"
fi

if [ "$VMMON_LOADED" -gt 0 ]; then
    info "Unloading vmmon..."
    rmmod vmmon 2>/dev/null || warning "Could not unload vmmon (may not be loaded)"
fi

log "✓ Modules unloaded"

# Step 2: Remove compiled modules
echo ""
info "Step 2: Removing compiled modules..."

MODULES_REMOVED=0

if [ -f "/lib/modules/$CURRENT_KERNEL/misc/vmmon.ko" ]; then
    info "Removing /lib/modules/$CURRENT_KERNEL/misc/vmmon.ko"
    rm -f "/lib/modules/$CURRENT_KERNEL/misc/vmmon.ko"
    MODULES_REMOVED=$((MODULES_REMOVED + 1))
fi

if [ -f "/lib/modules/$CURRENT_KERNEL/misc/vmnet.ko" ]; then
    info "Removing /lib/modules/$CURRENT_KERNEL/misc/vmnet.ko"
    rm -f "/lib/modules/$CURRENT_KERNEL/misc/vmnet.ko"
    MODULES_REMOVED=$((MODULES_REMOVED + 1))
fi

# Check for modules in other locations
for module in vmmon vmnet; do
    FOUND_MODULES=$(find "/lib/modules/$CURRENT_KERNEL" -name "${module}.ko" 2>/dev/null || true)
    if [ -n "$FOUND_MODULES" ]; then
        echo "$FOUND_MODULES" | while read -r module_path; do
            info "Removing $module_path"
            rm -f "$module_path"
            MODULES_REMOVED=$((MODULES_REMOVED + 1))
        done
    fi
done

if [ $MODULES_REMOVED -gt 0 ]; then
    log "✓ Removed $MODULES_REMOVED module(s)"
else
    warning "No compiled modules found for kernel $CURRENT_KERNEL"
fi

# Step 3: Update module dependencies
echo ""
info "Step 3: Updating module dependencies..."
depmod -a
log "✓ Module dependencies updated"

# Step 4: Verify removal
echo ""
info "Step 4: Verifying removal..."

STILL_LOADED=$(lsmod | grep -E "vmmon|vmnet" || true)
if [ -z "$STILL_LOADED" ]; then
    log "✓ No VMware modules are loaded"
else
    warning "Some modules are still loaded:"
    echo "$STILL_LOADED" | sed 's/^/  /'
fi

STILL_PRESENT=$(find "/lib/modules/$CURRENT_KERNEL" -name "vmmon.ko" -o -name "vmnet.ko" 2>/dev/null || true)
if [ -z "$STILL_PRESENT" ]; then
    log "✓ No compiled modules found in /lib/modules/$CURRENT_KERNEL"
else
    warning "Some module files still exist:"
    echo "$STILL_PRESENT" | sed 's/^/  /'
fi

echo ""
log "✓ Uninstall completed!"
echo ""
info "VMware modules have been removed from kernel $CURRENT_KERNEL"
info "VMware Workstation is still installed but modules are not loaded"
echo ""
echo -e "${YELLOW}To reinstall modules:${NC}"
echo "  sudo bash scripts/install-vmware-modules.sh"
echo ""
echo -e "${YELLOW}To restore from a backup:${NC}"
echo "  sudo bash scripts/restore-vmware-modules.sh"
echo ""

