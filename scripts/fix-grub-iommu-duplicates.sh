#!/usr/bin/env bash
################################################################################
# VMware Module Compiler - GRUB IOMMU Duplicate Fixer
# Purpose: Remove duplicate IOMMU parameters from GRUB configuration
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# GTK4 Purple theme
HYPHAED_GREEN='\033[38;5;141m'

log() {
    echo -e "${HYPHAED_GREEN}[✓]${NC} $1"
}

info() {
    echo -e "${CYAN}[i]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Dynamic box drawing
get_term_width() {
    tput cols 2>/dev/null || echo 80
}

draw_section_header() {
    local title="$1"
    local width=$(get_term_width)
    local title_len=${#title}
    local padding=$(( (width - title_len - 4) / 2 ))
    
    printf "╭"
    printf '─%.0s' $(seq 1 $((width - 2)))
    printf "╮\n"
    
    printf "│ "
    printf "%${padding}s" ""
    printf "%s" "$title"
    printf "%$((width - title_len - padding - 4))s" ""
    printf " │\n"
    
    printf "╰"
    printf '─%.0s' $(seq 1 $((width - 2)))
    printf "╯\n"
}

################################################################################
# ROOT CHECK
################################################################################

if [ "$EUID" -ne 0 ]; then 
    echo ""
    draw_section_header "❌ ROOT ACCESS REQUIRED"
    echo ""
    error "This script must be run as root to modify GRUB"
    echo ""
    info "Please run: ${GREEN}sudo $0${NC}"
    echo ""
    exit 1
fi

################################################################################
# HEADER
################################################################################

clear
echo ""
draw_section_header "🔧 GRUB IOMMU DUPLICATE FIXER"
echo ""

################################################################################
# CHECK FOR DUPLICATES
################################################################################

if ! [ -f /etc/default/grub ]; then
    error "/etc/default/grub not found"
    exit 1
fi

info "Checking for duplicate IOMMU parameters..."
echo ""

HAS_DUPLICATES=false

if grep -q "intel_iommu=on.*intel_iommu=on" /etc/default/grub; then
    warning "Found duplicate intel_iommu=on parameters"
    HAS_DUPLICATES=true
fi

if grep -q "amd_iommu=on.*amd_iommu=on" /etc/default/grub; then
    warning "Found duplicate amd_iommu=on parameters"
    HAS_DUPLICATES=true
fi

if grep -q "iommu=pt.*iommu=pt" /etc/default/grub; then
    warning "Found duplicate iommu=pt parameters"
    HAS_DUPLICATES=true
fi

# Also check if iommu=pt is missing when intel_iommu=on or amd_iommu=on is present
NEEDS_PT=false
if grep -q "intel_iommu=on" /etc/default/grub && ! grep -q "iommu=pt" /etc/default/grub; then
    warning "Found intel_iommu=on but missing iommu=pt (passthrough mode)"
    NEEDS_PT=true
fi

if grep -q "amd_iommu=on" /etc/default/grub && ! grep -q "iommu=pt" /etc/default/grub; then
    warning "Found amd_iommu=on but missing iommu=pt (passthrough mode)"
    NEEDS_PT=true
fi

if [ "$HAS_DUPLICATES" = false ] && [ "$NEEDS_PT" = false ]; then
    echo ""
    log "No duplicate IOMMU parameters found!"
    info "Your GRUB configuration is clean"
    echo ""
    exit 0
fi

echo ""
info "Current GRUB_CMDLINE_LINUX_DEFAULT:"
grep "GRUB_CMDLINE_LINUX_DEFAULT=" /etc/default/grub | head -1
echo ""

################################################################################
# FIX DUPLICATES
################################################################################

echo ""
draw_section_header "🔨 FIXING DUPLICATES"
echo ""

# Backup
info "Creating backup..."
cp /etc/default/grub /etc/default/grub.backup-fix-$(date +%Y%m%d-%H%M%S)
log "Backup created"
echo ""

# Detect CPU vendor
info "Detecting CPU vendor..."
CPU_VENDOR=$(lscpu | grep "Vendor ID" | awk '{print $3}' | tr '[:upper:]' '[:lower:]')
if [ -z "$CPU_VENDOR" ]; then
    CPU_VENDOR=$(grep -m1 vendor_id /proc/cpuinfo | cut -d: -f2 | tr -d ' ' | tr '[:upper:]' '[:lower:]')
fi

if grep -q "intel" <<< "$CPU_VENDOR"; then
    log "Detected Intel CPU"
elif grep -q "amd" <<< "$CPU_VENDOR"; then
    log "Detected AMD CPU"
fi
echo ""

# Remove all IOMMU parameters
info "Removing all IOMMU parameters..."
# Remove with leading space
sed -i 's/ intel_iommu=on//g' /etc/default/grub
sed -i 's/ amd_iommu=on//g' /etc/default/grub
sed -i 's/ iommu=pt//g' /etc/default/grub
# Remove at beginning (after quote)
sed -i 's/="intel_iommu=on /="/g' /etc/default/grub
sed -i 's/="amd_iommu=on /="/g' /etc/default/grub
sed -i 's/="iommu=pt /="/g' /etc/default/grub
# Remove if only parameter
sed -i 's/="intel_iommu=on"/""/g' /etc/default/grub
sed -i 's/="amd_iommu=on"/""/g' /etc/default/grub
sed -i 's/="iommu=pt"/""/g' /etc/default/grub
log "All IOMMU parameters removed"
echo ""

# Add back once
info "Adding IOMMU parameters back (once)..."
if grep -q "intel" <<< "$CPU_VENDOR"; then
    sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="/&intel_iommu=on iommu=pt /' /etc/default/grub
    log "Intel VT-d parameters added: intel_iommu=on iommu=pt"
elif grep -q "amd" <<< "$CPU_VENDOR"; then
    sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="/&amd_iommu=on iommu=pt /' /etc/default/grub
    log "AMD-Vi parameters added: amd_iommu=on iommu=pt"
fi
echo ""

info "New GRUB_CMDLINE_LINUX_DEFAULT:"
grep "GRUB_CMDLINE_LINUX_DEFAULT=" /etc/default/grub | head -1
echo ""

################################################################################
# UPDATE GRUB
################################################################################

echo ""
draw_section_header "🔄 UPDATING GRUB"
echo ""

info "Updating GRUB configuration..."
update-grub
echo ""
log "GRUB updated successfully!"

################################################################################
# SUMMARY
################################################################################

echo ""
draw_section_header "✅ FIX COMPLETE"
echo ""

log "Duplicate IOMMU parameters have been removed!"
echo ""
info "What changed:"
echo "  • Removed all duplicate intel_iommu=on / amd_iommu=on / iommu=pt"
echo "  • Added them back exactly once"
echo "  • Updated GRUB bootloader"
echo ""
warning "⚠ REBOOT REQUIRED"
info "The changes will take effect after reboot"
echo ""
info "After reboot, verify with:"
echo "  ${CYAN}cat /proc/cmdline | grep -o 'iommu' | wc -l${NC}"
echo "  (Should show: 2 for 'intel_iommu' and 'iommu=pt')"
echo ""

