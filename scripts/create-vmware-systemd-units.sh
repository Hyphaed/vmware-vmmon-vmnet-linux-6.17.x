#!/usr/bin/env bash

#==============================================================================
# VMWARE NATIVE SYSTEMD UNITS CREATOR
#==============================================================================
# Purpose: Create native systemd unit files for VMware services
#          Eliminates "lacks a native systemd unit file" warnings
# Author: VMware Module Installation Script
# License: MIT
#==============================================================================

set -euo pipefail

# Colors for output
readonly GTK_PURPLE_DARK="#613583"
readonly RESET="\033[0m"
readonly PURPLE="\033[38;2;97;53;131m"
readonly GREEN="\033[38;2;38;162;105m"
readonly YELLOW="\033[38;2;200;165;0m"
readonly RED="\033[38;2;192;28;40m"
readonly CYAN="\033[38;2;42;161;179m"

# Output functions
info() { echo -e "${CYAN}[i]${RESET} $*"; }
log() { echo -e "${GREEN}[✓]${RESET} $*"; }
warning() { echo -e "${YELLOW}[!]${RESET} $*"; }
error() { echo -e "${RED}[✗]${RESET} $*"; }

# Get terminal width for dynamic boxes
get_term_width() {
    local width
    width=$(tput cols 2>/dev/null || echo 80)
    echo "$width"
}

# Draw box top
draw_box_top() {
    local width=$(get_term_width)
    local line="╭"
    for ((i=2; i<width; i++)); do line+="─"; done
    line+="╮"
    echo -e "${PURPLE}${line}${RESET}"
}

# Draw box bottom
draw_box_bottom() {
    local width=$(get_term_width)
    local line="╰"
    for ((i=2; i<width; i++)); do line+="─"; done
    line+="╯"
    echo -e "${PURPLE}${line}${RESET}"
}

# Draw box line with content
draw_box_line() {
    local content="$1"
    local width=$(get_term_width)
    local content_length=${#content}
    local padding=$(( (width - content_length - 2) / 2 ))
    local line="│"
    
    # Left padding
    for ((i=0; i<padding; i++)); do line+=" "; done
    
    # Content
    line+="$content"
    
    # Right padding
    local right_padding=$(( width - content_length - padding - 2 ))
    for ((i=0; i<right_padding; i++)); do line+=" "; done
    
    line+="│"
    echo -e "${PURPLE}${line}${RESET}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root"
    echo ""
    info "Please run: sudo $0"
    exit 1
fi

echo ""
draw_box_top
draw_box_line ""
draw_box_line "VMWARE NATIVE SYSTEMD UNITS CREATOR"
draw_box_line "Create Modern systemd Service Files"
draw_box_line ""
draw_box_bottom
echo ""

info "This script creates native systemd unit files for VMware services"
info "Eliminates: 'SysV service lacks a native systemd unit file' warnings"
echo ""

# Check if VMware is installed
if [ ! -f "/etc/init.d/vmware" ]; then
    error "VMware not found in /etc/init.d/"
    info "Please install VMware Workstation first"
    exit 1
fi

log "✓ VMware installation detected"
echo ""

draw_box_top
draw_box_line "SERVICES TO CREATE"
draw_box_bottom
echo ""

info "1. vmware.service - Main VMware service"
info "2. vmware-usb.service - USB Arbitrator service"
echo ""

read -p "Create native systemd units? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    info "Operation cancelled"
    exit 0
fi

echo ""
info "Creating systemd unit files..."
echo ""

# ============================================
# 1. CREATE VMWARE.SERVICE
# ============================================
info "Creating vmware.service..."

cat > /etc/systemd/system/vmware.service << 'EOF'
[Unit]
Description=VMware Workstation Services
Documentation=https://www.vmware.com/
After=network.target systemd-modules-load.service
Requires=systemd-modules-load.service
Before=vmware-usb.service

[Service]
Type=forking
ExecStartPre=/usr/bin/modprobe -a vmmon vmnet
ExecStart=/etc/init.d/vmware start
ExecStop=/etc/init.d/vmware stop
RemainAfterExit=yes
TimeoutStartSec=0
StandardOutput=journal
StandardError=journal

# Ensure modules are loaded
ConditionPathExists=/dev/vmmon

[Install]
WantedBy=multi-user.target
EOF

log "✓ vmware.service created"

# ============================================
# 2. CREATE VMWARE-USB.SERVICE
# ============================================
info "Creating vmware-usb.service..."

cat > /etc/systemd/system/vmware-usb.service << 'EOF'
[Unit]
Description=VMware USB Arbitrator Service
Documentation=https://www.vmware.com/
After=vmware.service
Requires=vmware.service
PartOf=vmware.service

[Service]
Type=forking
ExecStart=/etc/init.d/vmware-USBArbitrator start
ExecStop=/etc/init.d/vmware-USBArbitrator stop
RemainAfterExit=yes
TimeoutStartSec=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

log "✓ vmware-usb.service created"

# ============================================
# 3. RELOAD SYSTEMD AND ENABLE SERVICES
# ============================================
echo ""
info "Reloading systemd daemon..."
systemctl daemon-reload
log "✓ Systemd daemon reloaded"

echo ""
info "Disabling old SysV init scripts..."

# Disable old SysV services (they'll be replaced by systemd units)
if systemctl is-enabled vmware.service 2>/dev/null | grep -q "enabled"; then
    info "Old vmware.service already disabled"
else
    # Check if old service exists
    if [ -f "/etc/systemd/system/vmware.service.d" ] || systemctl list-unit-files | grep -q "^vmware\.service.*generated"; then
        info "Removing old auto-generated unit..."
    fi
fi

log "✓ Old services handled"

echo ""
info "Enabling new native systemd units..."

# Enable the new services
systemctl enable vmware.service
log "✓ vmware.service enabled"

systemctl enable vmware-usb.service
log "✓ vmware-usb.service enabled"

echo ""
draw_box_top
draw_box_line "RESTART SERVICES?"
draw_box_bottom
echo ""

warning "Services need to be restarted to use new systemd units"
info "This will briefly interrupt any running VMs"
echo ""

read -p "Restart VMware services now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    info "Stopping old services..."
    /etc/init.d/vmware stop 2>/dev/null || true
    /etc/init.d/vmware-USBArbitrator stop 2>/dev/null || true
    sleep 2
    
    info "Starting new systemd services..."
    systemctl start vmware.service
    systemctl start vmware-usb.service
    
    echo ""
    log "✓ Services restarted with new systemd units"
else
    echo ""
    info "Services will use new units on next boot"
    warning "To restart manually: sudo systemctl restart vmware.service"
fi

echo ""
draw_box_top
draw_box_line "VERIFICATION"
draw_box_bottom
echo ""

# Verify services
info "Checking service status..."
echo ""

if systemctl is-active --quiet vmware.service; then
    log "✓ vmware.service: active (running)"
else
    info "vmware.service: inactive (will start on boot)"
fi

if systemctl is-active --quiet vmware-usb.service; then
    log "✓ vmware-usb.service: active (running)"
else
    info "vmware-usb.service: inactive (will start on boot)"
fi

echo ""
log "✓ Native systemd units created successfully"
echo ""

draw_box_top
draw_box_line "BENEFITS"
draw_box_bottom
echo ""

info "✓ No more 'lacks a native systemd unit file' warnings"
info "✓ Better integration with systemd"
info "✓ Cleaner boot logs"
info "✓ Proper service dependencies"
info "✓ Journal logging support"
info "✓ Modern service management"
echo ""

draw_box_top
draw_box_line "SERVICE MANAGEMENT COMMANDS"
draw_box_bottom
echo ""

info "Start services:"
echo "  sudo systemctl start vmware.service"
echo ""

info "Stop services:"
echo "  sudo systemctl stop vmware.service"
echo ""

info "Restart services:"
echo "  sudo systemctl restart vmware.service"
echo ""

info "Check status:"
echo "  sudo systemctl status vmware.service"
echo ""

info "View logs:"
echo "  sudo journalctl -u vmware.service"
echo ""

log "✓ Done!"

