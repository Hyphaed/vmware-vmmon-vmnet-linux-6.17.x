#!/usr/bin/env bash

#==============================================================================
# FIX VMWARE SYSTEMD SERVICES NOW
#==============================================================================
# Purpose: Fix current system to use proper native systemd units
# Author: VMware Module Installation Script
# License: MIT
#==============================================================================

set -euo pipefail

# Colors
readonly PURPLE="\033[38;2;97;53;131m"
readonly GREEN="\033[38;2;38;162;105m"
readonly YELLOW="\033[38;2;200;165;0m"
readonly RED="\033[38;2;192;28;40m"
readonly CYAN="\033[38;2;42;161;179m"
readonly RESET="\033[0m"

info() { echo -e "${CYAN}[i]${RESET} $*"; }
log() { echo -e "${GREEN}[✓]${RESET} $*"; }
warning() { echo -e "${YELLOW}[!]${RESET} $*"; }
error() { echo -e "${RED}[✗]${RESET} $*"; }

# Check root
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root"
    echo ""
    info "Please run: sudo $0"
    exit 1
fi

echo ""
echo -e "${PURPLE}╭────────────────────────────────────────────────────────────╮${RESET}"
echo -e "${PURPLE}│${RESET}  FIX VMWARE SYSTEMD SERVICES                          ${PURPLE}│${RESET}"
echo -e "${PURPLE}╰────────────────────────────────────────────────────────────╯${RESET}"
echo ""

info "This will fix current VMware systemd services"
echo ""

# 1. Fix modprobe path in vmware.service
if [ -f "/etc/systemd/system/vmware.service" ]; then
    info "Fixing modprobe path in vmware.service..."
    MODPROBE_BIN=$(command -v modprobe)
    sed -i "s|ExecStartPre=/usr/bin/modprobe|ExecStartPre=$MODPROBE_BIN|g" /etc/systemd/system/vmware.service
    log "✓ vmware.service fixed (modprobe path: $MODPROBE_BIN)"
fi

# 2. Stop and disable old SysV service
info "Disabling old SysV-generated service..."
systemctl stop vmware-USBArbitrator.service 2>/dev/null || true
systemctl disable vmware-USBArbitrator.service 2>/dev/null || true
log "✓ Old SysV service disabled"

# 3. Reload systemd
info "Reloading systemd..."
systemctl daemon-reload
log "✓ Systemd reloaded"

# 4. Restart services
info "Restarting VMware services with native units..."
systemctl restart vmware.service
systemctl start vmware-usb.service
log "✓ Services restarted"

echo ""
echo -e "${PURPLE}╭────────────────────────────────────────────────────────────╮${RESET}"
echo -e "${PURPLE}│${RESET}  VERIFICATION                                          ${PURPLE}│${RESET}"
echo -e "${PURPLE}╰────────────────────────────────────────────────────────────╯${RESET}"
echo ""

# Verify
if systemctl is-active --quiet vmware.service; then
    log "✓ vmware.service: active (running)"
else
    error "vmware.service: not running"
fi

if systemctl is-active --quiet vmware-usb.service; then
    log "✓ vmware-usb.service: active (running)"
else
    warning "vmware-usb.service: not running (may be normal if USB arbitrator already running)"
fi

echo ""
log "✓ Done! Reboot to see clean boot logs"
echo ""
info "After reboot, no more 'SysV service lacks native unit' warnings"

