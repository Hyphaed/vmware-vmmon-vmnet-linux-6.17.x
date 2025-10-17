#!/usr/bin/env bash

#==============================================================================
# OLLAMA SERVICE DISABLER
#==============================================================================
# Purpose: Disable and mask Ollama service to eliminate boot errors
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
draw_box_line "OLLAMA SERVICE DISABLER"
draw_box_line "Stop & Mask Ollama to Eliminate Boot Errors"
draw_box_line ""
draw_box_bottom
echo ""

# Check if Ollama service exists
if ! systemctl list-unit-files | grep -q "ollama.service"; then
    info "Ollama service not found - nothing to do"
    log "✓ No action needed"
    exit 0
fi

info "Checking Ollama service status..."
echo ""

# Get current status
if systemctl is-active --quiet ollama.service; then
    warning "Ollama service is currently RUNNING"
    OLLAMA_RUNNING=true
else
    info "Ollama service is not running"
    OLLAMA_RUNNING=false
fi

if systemctl is-enabled --quiet ollama.service 2>/dev/null; then
    warning "Ollama service is ENABLED (will start at boot)"
    OLLAMA_ENABLED=true
else
    info "Ollama service is not enabled"
    OLLAMA_ENABLED=false
fi

if systemctl is-enabled --quiet ollama.service 2>&1 | grep -q "masked"; then
    log "Ollama service is already MASKED"
    OLLAMA_MASKED=true
else
    info "Ollama service is not masked"
    OLLAMA_MASKED=false
fi

echo ""

# If already masked, nothing to do
if [ "$OLLAMA_MASKED" = true ]; then
    log "✓ Ollama service is already disabled and masked"
    info "No boot errors will occur from Ollama"
    exit 0
fi

# Show what will be done
draw_box_top
draw_box_line "ACTIONS TO BE PERFORMED"
draw_box_bottom
echo ""

if [ "$OLLAMA_RUNNING" = true ]; then
    info "1. Stop Ollama service"
fi

if [ "$OLLAMA_ENABLED" = true ]; then
    info "2. Disable Ollama service (prevent auto-start)"
fi

info "3. Mask Ollama service (prevent any start)"
echo ""

info "This will:"
echo "  • Stop Ollama if running"
echo "  • Prevent Ollama from starting at boot"
echo "  • Eliminate all Ollama boot errors"
echo "  • Keep Ollama installed (can be re-enabled later)"
echo ""

warning "Ollama will NOT start automatically after this"
info "You can manually run Ollama when needed: ollama serve"
echo ""

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    info "Operation cancelled"
    exit 0
fi

echo ""
info "Disabling Ollama service..."
echo ""

# Stop service if running
if [ "$OLLAMA_RUNNING" = true ]; then
    info "Stopping Ollama service..."
    if systemctl stop ollama.service 2>/dev/null; then
        log "✓ Ollama service stopped"
    else
        warning "Could not stop Ollama service (may already be stopped)"
    fi
fi

# Disable service if enabled
if [ "$OLLAMA_ENABLED" = true ]; then
    info "Disabling Ollama service..."
    if systemctl disable ollama.service 2>/dev/null; then
        log "✓ Ollama service disabled"
    else
        warning "Could not disable Ollama service (may already be disabled)"
    fi
fi

# Mask service
info "Masking Ollama service..."
if systemctl mask ollama.service 2>/dev/null; then
    log "✓ Ollama service masked"
else
    error "Failed to mask Ollama service"
    exit 1
fi

echo ""
log "✓ Ollama service successfully disabled and masked"
echo ""

draw_box_top
draw_box_line "VERIFICATION"
draw_box_bottom
echo ""

# Verify masking
if systemctl is-enabled --quiet ollama.service 2>&1 | grep -q "masked"; then
    log "✓ Status: masked"
else
    error "Verification failed - service not masked"
    exit 1
fi

if systemctl is-active --quiet ollama.service; then
    error "Service is still running (unexpected)"
else
    log "✓ Service stopped"
fi

echo ""
log "✓ No Ollama boot errors will occur on next boot"
echo ""

draw_box_top
draw_box_line "HOW TO RE-ENABLE OLLAMA (IF NEEDED)"
draw_box_bottom
echo ""

info "To re-enable Ollama service later:"
echo ""
echo "  sudo systemctl unmask ollama.service"
echo "  sudo systemctl enable ollama.service"
echo "  sudo systemctl start ollama.service"
echo ""

info "Or run Ollama manually when needed:"
echo ""
echo "  ollama serve"
echo ""

log "✓ Done!"

