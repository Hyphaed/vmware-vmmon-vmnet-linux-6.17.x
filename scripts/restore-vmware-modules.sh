#!/bin/bash
# Restore script for VMware modules
# Allows restoring from previous backups created during installation/update
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
║        VMWARE MODULES RESTORE UTILITY                        ║
║        Restore from previous backups                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root (use sudo)"
    exit 1
fi

# Detect distribution to find correct paths
if [ -f /etc/gentoo-release ]; then
    DISTRO="gentoo"
    VMWARE_MOD_DIR="/opt/vmware/lib/vmware/modules/source"
    BACKUP_BASE_DIR="/tmp"
elif [ -f /etc/fedora-release ]; then
    DISTRO="fedora"
    VMWARE_MOD_DIR="/usr/lib/vmware/modules/source"
    BACKUP_BASE_DIR="$VMWARE_MOD_DIR"
elif [ -f /etc/debian_version ]; then
    DISTRO="debian"
    VMWARE_MOD_DIR="/usr/lib/vmware/modules/source"
    BACKUP_BASE_DIR="$VMWARE_MOD_DIR"
else
    DISTRO="unknown"
    VMWARE_MOD_DIR="/usr/lib/vmware/modules/source"
    BACKUP_BASE_DIR="$VMWARE_MOD_DIR"
    warning "Unrecognized distribution, using default paths"
fi

info "Distribution: $DISTRO"
info "VMware modules directory: $VMWARE_MOD_DIR"
echo ""

# Check if VMware modules directory exists
if [ ! -d "$VMWARE_MOD_DIR" ]; then
    error "VMware modules directory not found: $VMWARE_MOD_DIR"
    error "Please ensure VMware Workstation is installed"
    exit 1
fi

# Find all backup directories
if [ "$DISTRO" = "gentoo" ]; then
    # Gentoo backups are in /tmp
    BACKUPS=($(ls -d $BACKUP_BASE_DIR/vmware-backup-* 2>/dev/null | sort -r))
else
    # Other distros have backups in VMware module directory
    BACKUPS=($(ls -d $BACKUP_BASE_DIR/backup-* 2>/dev/null | sort -r))
fi

if [ ${#BACKUPS[@]} -eq 0 ]; then
    error "No backups found!"
    echo ""
    info "Backup locations checked:"
    if [ "$DISTRO" = "gentoo" ]; then
        echo "  • /tmp/vmware-backup-*"
    else
        echo "  • $VMWARE_MOD_DIR/backup-*"
    fi
    echo ""
    info "Backups are created automatically when you run:"
    echo "  • install-vmware-modules.sh"
    echo "  • update-vmware-modules.sh"
    exit 1
fi

# Display current state
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}CURRENT STATE${NC}"
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo ""

if [ -f "$VMWARE_MOD_DIR/vmmon.tar" ]; then
    CURRENT_SIZE=$(du -h "$VMWARE_MOD_DIR/vmmon.tar" | awk '{print $1}')
    CURRENT_DATE=$(stat -c %y "$VMWARE_MOD_DIR/vmmon.tar" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)
    info "Current vmmon.tar: $CURRENT_SIZE (modified: $CURRENT_DATE)"
else
    warning "Current vmmon.tar: NOT FOUND"
fi

if [ -f "$VMWARE_MOD_DIR/vmnet.tar" ]; then
    CURRENT_SIZE=$(du -h "$VMWARE_MOD_DIR/vmnet.tar" | awk '{print $1}')
    CURRENT_DATE=$(stat -c %y "$VMWARE_MOD_DIR/vmnet.tar" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)
    info "Current vmnet.tar: $CURRENT_SIZE (modified: $CURRENT_DATE)"
else
    warning "Current vmnet.tar: NOT FOUND"
fi

echo ""

# Display available backups
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}AVAILABLE BACKUPS${NC}"
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo ""

for i in "${!BACKUPS[@]}"; do
    BACKUP_DIR="${BACKUPS[$i]}"
    BACKUP_NAME=$(basename "$BACKUP_DIR")
    
    # Extract timestamp from backup name
    if [ "$DISTRO" = "gentoo" ]; then
        TIMESTAMP=$(echo "$BACKUP_NAME" | sed 's/vmware-backup-//')
    else
        TIMESTAMP=$(echo "$BACKUP_NAME" | sed 's/backup-//')
    fi
    
    # Format timestamp for display
    YEAR=${TIMESTAMP:0:4}
    MONTH=${TIMESTAMP:4:2}
    DAY=${TIMESTAMP:6:2}
    HOUR=${TIMESTAMP:9:2}
    MIN=${TIMESTAMP:11:2}
    SEC=${TIMESTAMP:13:2}
    
    FORMATTED_DATE="$YEAR-$MONTH-$DAY $HOUR:$MIN:$SEC"
    
    # Check if backup contains the required files
    if [ -f "$BACKUP_DIR/vmmon.tar" ] && [ -f "$BACKUP_DIR/vmnet.tar" ]; then
        VMMON_SIZE=$(du -h "$BACKUP_DIR/vmmon.tar" | awk '{print $1}')
        VMNET_SIZE=$(du -h "$BACKUP_DIR/vmnet.tar" | awk '{print $1}')
        echo -e "${GREEN}  $((i+1)))${NC} $FORMATTED_DATE"
        echo "     Path: $BACKUP_DIR"
        echo "     vmmon.tar: $VMMON_SIZE | vmnet.tar: $VMNET_SIZE"
        echo ""
    else
        echo -e "${RED}  $((i+1)))${NC} $FORMATTED_DATE ${RED}(INCOMPLETE)${NC}"
        echo "     Path: $BACKUP_DIR"
        warning "     Missing required files"
        echo ""
    fi
done

echo -e "${GREEN}  0)${NC} Cancel restore"
echo ""

# Prompt for selection
while true; do
    read -p "Select backup to restore (0-${#BACKUPS[@]}): " SELECTION
    
    if [ "$SELECTION" = "0" ]; then
        info "Restore cancelled"
        exit 0
    fi
    
    if [ "$SELECTION" -ge 1 ] && [ "$SELECTION" -le "${#BACKUPS[@]}" ]; then
        SELECTED_BACKUP="${BACKUPS[$((SELECTION-1))]}"
        break
    else
        warning "Invalid selection. Please enter a number between 0 and ${#BACKUPS[@]}"
    fi
done

# Verify selected backup
if [ ! -f "$SELECTED_BACKUP/vmmon.tar" ] || [ ! -f "$SELECTED_BACKUP/vmnet.tar" ]; then
    error "Selected backup is incomplete or corrupted"
    error "Missing vmmon.tar or vmnet.tar"
    exit 1
fi

echo ""
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${RED}WARNING${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo ""
echo "This will restore VMware modules from:"
echo "  $SELECTED_BACKUP"
echo ""
warning "Current modules will be OVERWRITTEN!"
echo ""

read -p "Are you sure you want to continue? (yes/NO): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    info "Restore cancelled"
    exit 0
fi

echo ""
log "Starting restore process..."

# Unload current modules
info "Unloading current VMware modules..."
modprobe -r vmnet 2>/dev/null || true
modprobe -r vmmon 2>/dev/null || true
rmmod vmnet 2>/dev/null || true
rmmod vmmon 2>/dev/null || true

# Restore the backup
info "Restoring vmmon.tar..."
cp "$SELECTED_BACKUP/vmmon.tar" "$VMWARE_MOD_DIR/vmmon.tar"

info "Restoring vmnet.tar..."
cp "$SELECTED_BACKUP/vmnet.tar" "$VMWARE_MOD_DIR/vmnet.tar"

log "✓ Files restored successfully"

# Rebuild modules from restored tarballs (not applicable for Gentoo in this way)
if [ "$DISTRO" != "gentoo" ]; then
    echo ""
    info "Attempting to rebuild and load modules..."
    
    # Try to rebuild using VMware's own tools
    if command -v vmware-modconfig &> /dev/null; then
        info "Running vmware-modconfig..."
        vmware-modconfig --console --install-all 2>&1 | tee /tmp/vmware-restore.log || true
    fi
fi

# Try to load modules
echo ""
info "Attempting to load modules..."

if modprobe vmmon 2>/dev/null; then
    log "✓ vmmon loaded"
else
    warning "Failed to load vmmon"
fi

if modprobe vmnet 2>/dev/null; then
    log "✓ vmnet loaded"
else
    warning "Failed to load vmnet"
fi

# Check final status
echo ""
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}RESTORE COMPLETED${NC}"
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo ""

info "Current module status:"
if lsmod | grep -q vmmon; then
    lsmod | grep vmmon | sed 's/^/  /'
else
    warning "  vmmon: not loaded"
fi

if lsmod | grep -q vmnet; then
    lsmod | grep vmnet | sed 's/^/  /'
else
    warning "  vmnet: not loaded"
fi

echo ""

if lsmod | grep -q "vmmon" && lsmod | grep -q "vmnet"; then
    log "✓ Restore successful - modules are loaded"
    echo ""
    info "You can now start VMware Workstation"
else
    warning "Modules restored but not loaded"
    echo ""
    info "You may need to:"
    echo "  1. Reboot your system"
    echo "  2. Run: sudo vmware-modconfig --console --install-all"
    echo "  3. Run: sudo bash scripts/install-vmware-modules.sh"
fi

echo ""
log "Restore process completed"

