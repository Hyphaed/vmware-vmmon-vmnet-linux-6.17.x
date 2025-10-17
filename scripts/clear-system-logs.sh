#!/usr/bin/env bash
################################################################################
# VMware Module Compiler - System Log Cleaner
# Purpose: Clear all system logs for clean boot log analysis
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# GTK4 Purple theme
HYPHAED_GREEN='\033[38;5;141m'  # Purple for consistency

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

draw_box_top() {
    local width=$(get_term_width)
    printf "╭"
    printf '─%.0s' $(seq 1 $((width - 2)))
    printf "╮\n"
}

draw_box_bottom() {
    local width=$(get_term_width)
    printf "╰"
    printf '─%.0s' $(seq 1 $((width - 2)))
    printf "╯\n"
}

draw_section_header() {
    local title="$1"
    local width=$(get_term_width)
    local title_len=${#title}
    local padding=$(( (width - title_len - 4) / 2 ))
    
    draw_box_top
    printf "│ "
    printf "%${padding}s" ""
    printf "%s" "$title"
    printf "%$((width - title_len - padding - 4))s" ""
    printf " │\n"
    draw_box_bottom
}

################################################################################
# ROOT CHECK
################################################################################

if [ "$EUID" -ne 0 ]; then 
    echo ""
    draw_section_header "❌ ROOT ACCESS REQUIRED"
    echo ""
    error "This script must be run as root to clear system logs"
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
draw_section_header "🧹 SYSTEM LOG CLEANER"
echo ""
info "This script will clear all system logs for clean boot analysis"
echo ""

################################################################################
# CONFIRMATION
################################################################################

warning "This will clear the following logs:"
echo "  • systemd journal (journalctl)"
echo "  • Kernel ring buffer (dmesg)"
echo "  • System log (/var/log/syslog)"
echo "  • Authentication logs (/var/log/auth.log)"
echo "  • VMware build logs (this repo)"
echo ""

read -p "$(echo -e "${YELLOW}Are you sure? Type 'yes' to continue:${NC} ")" CONFIRM
echo ""

if [ "$CONFIRM" != "yes" ]; then
    warning "Operation cancelled"
    exit 0
fi

################################################################################
# CLEAR SYSTEM LOGS
################################################################################

echo ""
draw_section_header "🗑️  CLEARING SYSTEM LOGS"
echo ""

# 1. Clear journalctl
info "Clearing systemd journal..."
journalctl --rotate 2>/dev/null || true
journalctl --vacuum-time=1s 2>/dev/null || true
log "Systemd journal cleared"
echo ""

# 2. Clear dmesg (kernel ring buffer)
info "Clearing kernel ring buffer (dmesg)..."
dmesg -C 2>/dev/null || true
log "Kernel ring buffer cleared"
echo ""

# 3. Clear system logs
info "Clearing /var/log files..."
if [ -f /var/log/syslog ]; then
    > /var/log/syslog
    log "/var/log/syslog cleared"
fi

if [ -f /var/log/kern.log ]; then
    > /var/log/kern.log
    log "/var/log/kern.log cleared"
fi

if [ -f /var/log/auth.log ]; then
    > /var/log/auth.log
    log "/var/log/auth.log cleared"
fi

if [ -f /var/log/messages ]; then
    > /var/log/messages
    log "/var/log/messages cleared"
fi
echo ""

# 4. Clear VMware-specific logs
info "Clearing VMware logs..."
rm -f /var/log/vmware*.log 2>/dev/null || true
log "VMware logs cleared"
echo ""

# 5. Clear this repository's build logs
info "Clearing VMware build logs in this repository..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rm -f "$SCRIPT_DIR"/../vmware_build_*.log 2>/dev/null || true
rm -f "$SCRIPT_DIR"/vmware_build_*.log 2>/dev/null || true
log "Repository build logs cleared"
echo ""

################################################################################
# SUMMARY
################################################################################

echo ""
draw_section_header "✅ ALL LOGS CLEARED"
echo ""

log "System logs have been cleared successfully!"
echo ""
info "On next boot, you will have clean logs to analyze:"
echo ""
echo "  ${GREEN}1.${NC} Boot and let the system initialize"
echo "  ${GREEN}2.${NC} Check for any errors with:"
echo "     ${CYAN}sudo journalctl -b${NC}              # Current boot journal"
echo "     ${CYAN}sudo dmesg | grep -i error${NC}      # Kernel errors"
echo "     ${CYAN}sudo dmesg | grep -i vmmon${NC}      # VMware vmmon messages"
echo "     ${CYAN}sudo dmesg | grep -i vmnet${NC}      # VMware vmnet messages"
echo "     ${CYAN}sudo dmesg | grep -i iommu${NC}      # IOMMU messages"
echo ""
echo "  ${GREEN}3.${NC} If you find any issues, report them and we'll add fixes to the script"
echo ""

info "Recommended: ${YELLOW}Reboot now${NC} to activate IOMMU and test clean boot"
echo ""

