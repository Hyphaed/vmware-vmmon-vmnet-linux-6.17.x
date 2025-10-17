#!/bin/bash
# Enhanced script to compile VMware modules for kernel 6.16.x and 6.17.x
# Supports Ubuntu, Fedora, and Gentoo
# Uses specific patches according to kernel version
# Optional hardware-specific optimizations
# Date: 2025-10-15

set -e

# Detectar automáticamente el directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="/tmp/vmware_build_$$"
LOG_FILE="$SCRIPT_DIR/vmware_build_$(date +%Y%m%d_%H%M%S).log"

# Will be set after distro detection
BACKUP_DIR=""
VMWARE_MOD_DIR=""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"; }
info() { echo -e "${BLUE}[i]${NC} $1" | tee -a "$LOG_FILE"; }
warning() { echo -e "${YELLOW}[!]${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"; }

# Cleanup function in case of error
cleanup_on_error() {
    error "Error detected. Cleaning up..."
    cd "$HOME"
    rm -rf "$WORK_DIR"
    exit 1
}

trap cleanup_on_error ERR

echo -e "${CYAN}"
cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     VMWARE MODULES COMPILER FOR KERNEL 6.16/6.17            ║
║           (Ubuntu/Fedora/Gentoo Compatible)                  ║
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

# ============================================
# 0. SELECT KERNEL VERSION
# ============================================
echo ""
echo -e "${CYAN}════════════════════════════════════════${NC}"
echo -e "${YELLOW}KERNEL VERSION SELECTION${NC}"
echo -e "${CYAN}════════════════════════════════════════${NC}"
echo ""
echo "This script supports two kernel versions with specific patches:"
echo ""
echo -e "${GREEN}  1)${NC} Kernel 6.16.x"
echo "     • Uses patches from: https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x"
echo "     • Patches: timer_delete_sync(), rdmsrq_safe(), module_init()"
echo ""
echo -e "${GREEN}  2)${NC} Kernel 6.17.x"
echo "     • Uses patches from 6.16.x + additional objtool patches"
echo "     • Additional patches: OBJECT_FILES_NON_STANDARD, returns in void functions"
echo ""
echo -e "${BLUE}Kernel detected on your system:${NC} $(uname -r)"
echo ""

# Ask for kernel version
while true; do
    read -p "Which kernel version do you want to compile for? (1=6.16 / 2=6.17): " KERNEL_CHOICE
    case $KERNEL_CHOICE in
        1)
            TARGET_KERNEL="6.16"
            info "Selected: Kernel 6.16.x"
            break
            ;;
        2)
            TARGET_KERNEL="6.17"
            info "Selected: Kernel 6.17.x"
            break
            ;;
        *)
            warning "Invalid option. Please select 1 or 2."
            ;;
    esac
done

echo ""
log "Configuration: Compiling for kernel $TARGET_KERNEL"
echo ""

# ============================================
# 1. VERIFY SYSTEM
# ============================================
log "1. Verifying system..."

KERNEL_VERSION=$(uname -r)
KERNEL_MAJOR=$(echo $KERNEL_VERSION | cut -d. -f1)
KERNEL_MINOR=$(echo $KERNEL_VERSION | cut -d. -f2)

info "Detected kernel: $KERNEL_VERSION"
info "Version: $KERNEL_MAJOR.$KERNEL_MINOR"

# Detect distribution
if [ -f /etc/gentoo-release ]; then
    DISTRO="gentoo"
    PKG_MANAGER="emerge"
    VMWARE_MOD_DIR="/opt/vmware/lib/vmware/modules/source"
    BACKUP_DIR="/tmp/vmware-backup-$(date +%Y%m%d-%H%M%S)"
    info "Distribution: Gentoo Linux"
elif [ -f /etc/fedora-release ]; then
    DISTRO="fedora"
    PKG_MANAGER="dnf"
    VMWARE_MOD_DIR="/usr/lib/vmware/modules/source"
    BACKUP_DIR="/usr/lib/vmware/modules/source/backup-$(date +%Y%m%d-%H%M%S)"
    info "Distribution: Fedora"
elif [ -f /etc/debian_version ]; then
    DISTRO="debian"
    PKG_MANAGER="apt"
    VMWARE_MOD_DIR="/usr/lib/vmware/modules/source"
    BACKUP_DIR="/usr/lib/vmware/modules/source/backup-$(date +%Y%m%d-%H%M%S)"
    info "Distribution: Debian/Ubuntu"
else
    DISTRO="unknown"
    PKG_MANAGER="unknown"
    VMWARE_MOD_DIR="/usr/lib/vmware/modules/source"
    BACKUP_DIR="/usr/lib/vmware/modules/source/backup-$(date +%Y%m%d-%H%M%S)"
    warning "Unrecognized distribution"
fi

# Warning if there's a mismatch between detected kernel and selection
if [ "$KERNEL_MAJOR" = "6" ]; then
    if [ "$KERNEL_MINOR" = "16" ] && [ "$TARGET_KERNEL" = "6.17" ]; then
        warning "Your kernel is 6.16 but you selected patches for 6.17"
        warning "This may cause compatibility issues"
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    elif [ "$KERNEL_MINOR" = "17" ] && [ "$TARGET_KERNEL" = "6.16" ]; then
        warning "Your kernel is 6.17 but you selected patches for 6.16"
        warning "You may need the 6.17 patches"
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Detect kernel compiler
KERNEL_COMPILER=$(cat /proc/version | grep -oP '(?<=\().*?(?=\))' | grep -Ei 'gcc|clang' | head -1)
if [ -z "$KERNEL_COMPILER" ]; then
    KERNEL_COMPILER=$(cat /proc/version | grep -oP '(?<=\().*?(?=\))' | head -1)
fi
info "Kernel compiler: $KERNEL_COMPILER"

# Determine if using GCC or Clang
if echo "$KERNEL_COMPILER" | grep -qi "clang"; then
    USING_CLANG=true
    CC="clang"
    LD="ld.lld"
    info "Kernel compiled with Clang - using LLVM toolchain"
else
    USING_CLANG=false
    CC="gcc"
    LD="ld"
    info "Kernel compiled with GCC - using GNU toolchain"
fi

# Verify VMware
if ! command -v vmware &> /dev/null; then
    error "VMware Workstation not found"
    exit 1
fi

VMWARE_VERSION=$(vmware --version 2>/dev/null || echo "VMware Workstation (version unknown)")
log "✓ VMware detected"

# Check current modules
info "Currently loaded VMware modules:"
lsmod | grep -E "vmmon|vmnet" | sed 's/^/  /' || warning "No modules loaded"

log "✓ System verification completed"

# ============================================
# 1.5. HARDWARE DETECTION & OPTIMIZATION
# ============================================
echo ""
echo -e "${CYAN}════════════════════════════════════════${NC}"
echo -e "${YELLOW}HARDWARE OPTIMIZATION (OPTIONAL)${NC}"
echo -e "${CYAN}════════════════════════════════════════${NC}"
echo ""

# Detect CPU
CPU_MODEL=$(lscpu | grep "Model name" | cut -d: -f2 | sed 's/^[ \t]*//')
CPU_ARCH=$(lscpu | grep "Architecture" | cut -d: -f2 | sed 's/^[ \t]*//')
CPU_FLAGS=$(grep -m1 flags /proc/cpuinfo | cut -d: -f2)

info "CPU: $CPU_MODEL"
info "Architecture: $CPU_ARCH"

# Detect available optimizations
OPTIM_FLAGS=""
OPTIM_DESC=""

# Check for CPU features
if echo "$CPU_FLAGS" | grep -q "avx2"; then
    OPTIM_FLAGS="$OPTIM_FLAGS -mavx2"
    OPTIM_DESC="$OPTIM_DESC\n  • AVX2 (Advanced Vector Extensions 2)"
fi

if echo "$CPU_FLAGS" | grep -q "sse4_2"; then
    OPTIM_FLAGS="$OPTIM_FLAGS -msse4.2"
    OPTIM_DESC="$OPTIM_DESC\n  • SSE4.2 (Streaming SIMD Extensions)"
fi

# Native architecture optimization
NATIVE_OPTIM="-march=native -mtune=native"

# Conservative safe flags
SAFE_FLAGS="-O2 -pipe"

if [ -n "$OPTIM_FLAGS" ]; then
    echo -e "${GREEN}Hardware-Specific Optimizations Available:${NC}"
    echo -e "$OPTIM_DESC"
    echo ""
    echo -e "${YELLOW}Optimization Options:${NC}"
    echo ""
    echo -e "${GREEN}  1)${NC} Native (Recommended for this CPU)"
    echo "     Flags: $SAFE_FLAGS $NATIVE_OPTIM"
    echo "     • Optimized specifically for your CPU architecture"
    echo "     • Best performance for this system"
    echo "     • Modules will only work on similar CPUs"
    echo ""
    echo -e "${GREEN}  2)${NC} Conservative (Safe, portable)"
    echo "     Flags: $SAFE_FLAGS"
    echo "     • Standard optimization level"
    echo "     • Works on any x86_64 CPU"
    echo "     • Slightly lower performance"
    echo ""
    echo -e "${GREEN}  3)${NC} No optimizations (Default kernel flags)"
    echo "     • Uses same flags as your kernel"
    echo "     • Safest option"
    echo ""
    
    read -p "Select optimization level (1=Native / 2=Conservative / 3=None) [3]: " OPTIM_CHOICE
    OPTIM_CHOICE=${OPTIM_CHOICE:-3}
    
    case $OPTIM_CHOICE in
        1)
            EXTRA_CFLAGS="$SAFE_FLAGS $NATIVE_OPTIM"
            info "Selected: Native optimization for $CPU_MODEL"
            echo -e "${YELLOW}Note:${NC} Modules compiled with these flags may not work on different CPUs"
            ;;
        2)
            EXTRA_CFLAGS="$SAFE_FLAGS"
            info "Selected: Conservative optimization (portable)"
            ;;
        3|*)
            EXTRA_CFLAGS=""
            info "Selected: No additional optimizations (kernel defaults)"
            ;;
    esac
else
    warning "No specific CPU optimizations detected"
    EXTRA_CFLAGS=""
fi

echo ""
log "✓ Hardware detection completed"

# ============================================
# 2. INSTALL DEPENDENCIES
# ============================================
log "2. Verifying dependencies..."

# Verify kernel headers
if [ "$DISTRO" = "fedora" ]; then
    if [ ! -d "/usr/src/kernels/$KERNEL_VERSION" ]; then
        info "Installing kernel-devel..."
        sudo dnf install -y kernel-devel-$KERNEL_VERSION
    fi
    log "✓ Kernel headers found"
    
    # Build tools
    info "Verifying build tools..."
    sudo dnf groupinstall -y "Development Tools" || true
    sudo dnf install -y gcc make git wget tar || true
    
elif [ "$DISTRO" = "debian" ]; then
    if [ ! -d "/lib/modules/$KERNEL_VERSION/build" ]; then
        info "Installing linux-headers..."
        sudo apt update
        sudo apt install -y linux-headers-$KERNEL_VERSION
    fi
    log "✓ Kernel headers found"
    
    # Build tools
    info "Verifying build tools..."
    sudo apt install -y build-essential git wget tar

elif [ "$DISTRO" = "gentoo" ]; then
    if [ ! -d "/usr/src/linux-$KERNEL_VERSION" ] && [ ! -d "/usr/src/linux" ]; then
        warning "Kernel sources not found"
        info "Gentoo users: ensure kernel sources are installed"
    fi
    log "✓ Gentoo: Assuming build tools are available"
fi

log "✓ Build tools verified"

# ============================================
# 3. PREPARE WORKING DIRECTORY
# ============================================
log "3. Preparing working directory..."

# Create unique temporary directory
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"
info "Working directory: $WORK_DIR"

log "✓ Directory prepared"

# ============================================
# 4. EXTRACT ORIGINAL MODULES
# ============================================
log "4. Extracting original VMware modules..."

# Backup current modules
if [ -f "$VMWARE_MOD_DIR/vmmon.tar" ]; then
    info "Creating backup of current modules..."
    sudo mkdir -p "$BACKUP_DIR"
    sudo cp "$VMWARE_MOD_DIR/vmmon.tar" "$BACKUP_DIR/" 2>/dev/null || true
    sudo cp "$VMWARE_MOD_DIR/vmnet.tar" "$BACKUP_DIR/" 2>/dev/null || true
    info "Backup saved to: $BACKUP_DIR"
fi

# Extract modules in current working directory
info "Extracting vmmon.tar..."
if [ ! -f "$VMWARE_MOD_DIR/vmmon.tar" ]; then
    error "vmmon.tar not found at $VMWARE_MOD_DIR/vmmon.tar"
    error "Please verify VMware Workstation is properly installed"
    echo ""
    warning "POSSIBLE CAUSES:"
    echo "  • VMware Workstation not installed correctly"
    echo "  • Previous patching attempts using other scripts may have broken the modules"
    echo "  • Manual modifications to VMware files"
    echo ""
    warning "RECOMMENDED SOLUTION:"
    echo "  1. Completely uninstall VMware Workstation:"
    echo "     sudo vmware-installer -u vmware-workstation"
    echo "  2. Remove leftover files:"
    echo "     sudo rm -rf /usr/lib/vmware /etc/vmware"
    echo "  3. Reinstall VMware Workstation from official download"
    echo "  4. Run this script again"
    echo ""
    exit 1
fi

if ! tar -xf "$VMWARE_MOD_DIR/vmmon.tar" 2>&1 | tee -a "$LOG_FILE"; then
    error "Failed to extract vmmon.tar"
    error "The tar file is corrupted or inaccessible"
    echo ""
    warning "MODULES MAY BE BROKEN!"
    echo "  This often happens due to:"
    echo "  • Previous attempts to patch modules using other scripts from the internet"
    echo "  • Manual modifications to VMware module files"
    echo "  • Corrupted VMware installation"
    echo ""
    warning "RECOMMENDED SOLUTION:"
    echo "  1. Completely uninstall VMware Workstation:"
    echo "     sudo vmware-installer -u vmware-workstation"
    echo "  2. Remove leftover files:"
    echo "     sudo rm -rf /usr/lib/vmware /etc/vmware"
    echo "  3. Reinstall VMware Workstation from official download"
    echo "  4. Run this script again"
    echo ""
    exit 1
fi

info "Extracting vmnet.tar..."
if [ ! -f "$VMWARE_MOD_DIR/vmnet.tar" ]; then
    error "vmnet.tar not found at $VMWARE_MOD_DIR/vmnet.tar"
    error "Please verify VMware Workstation is properly installed"
    echo ""
    warning "POSSIBLE CAUSES:"
    echo "  • VMware Workstation not installed correctly"
    echo "  • Previous patching attempts using other scripts may have broken the modules"
    echo "  • Manual modifications to VMware files"
    echo ""
    warning "RECOMMENDED SOLUTION:"
    echo "  1. Completely uninstall VMware Workstation:"
    echo "     sudo vmware-installer -u vmware-workstation"
    echo "  2. Remove leftover files:"
    echo "     sudo rm -rf /usr/lib/vmware /etc/vmware"
    echo "  3. Reinstall VMware Workstation from official download"
    echo "  4. Run this script again"
    echo ""
    exit 1
fi

if ! tar -xf "$VMWARE_MOD_DIR/vmnet.tar" 2>&1 | tee -a "$LOG_FILE"; then
    error "Failed to extract vmnet.tar"
    error "The tar file is corrupted or inaccessible"
    echo ""
    warning "MODULES MAY BE BROKEN!"
    echo "  This often happens due to:"
    echo "  • Previous attempts to patch modules using other scripts from the internet"
    echo "  • Manual modifications to VMware module files"
    echo "  • Corrupted VMware installation"
    echo ""
    warning "RECOMMENDED SOLUTION:"
    echo "  1. Completely uninstall VMware Workstation:"
    echo "     sudo vmware-installer -u vmware-workstation"
    echo "  2. Remove leftover files:"
    echo "     sudo rm -rf /usr/lib/vmware /etc/vmware"
    echo "  3. Reinstall VMware Workstation from official download"
    echo "  4. Run this script again"
    echo ""
    exit 1
fi

# Verify extraction was successful
if [ ! -d "$WORK_DIR/vmmon-only" ] || [ ! -d "$WORK_DIR/vmnet-only" ]; then
    error "Error extracting modules"
    error "Expected directories vmmon-only and/or vmnet-only not found"
    echo ""
    warning "MODULES MAY BE BROKEN!"
    echo "  This often happens due to:"
    echo "  • Previous attempts to patch modules using other scripts from the internet"
    echo "  • Manual modifications to VMware module files"
    echo "  • Corrupted VMware installation"
    echo ""
    info "Working directory contents:"
    ls -la "$WORK_DIR" | tee -a "$LOG_FILE"
    echo ""
    warning "RECOMMENDED SOLUTION:"
    echo "  1. Completely uninstall VMware Workstation:"
    echo "     sudo vmware-installer -u vmware-workstation"
    echo "  2. Remove leftover files:"
    echo "     sudo rm -rf /usr/lib/vmware /etc/vmware"
    echo "  3. Reinstall VMware Workstation from official download"
    echo "  4. Run this script again"
    echo ""
    exit 1
fi

log "✓ Modules extracted"

# ============================================
# 5. DOWNLOAD PATCHES ACCORDING TO VERSION
# ============================================
log "5. Downloading patches for kernel $TARGET_KERNEL..."

PATCH_DIR="$WORK_DIR/patches"
mkdir -p "$PATCH_DIR"
cd "$PATCH_DIR"

# Download base patches for 6.16
PATCH_REPO="https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x"
info "Downloading base patches from GitHub (6.16.x)..."

if [ -d "vmware-vmmon-vmnet-linux-6.16.x" ]; then
    rm -rf vmware-vmmon-vmnet-linux-6.16.x
fi

git clone --depth 1 "$PATCH_REPO" || {
    error "Error downloading patches from GitHub"
    exit 1
}

log "✓ Base patches downloaded"

# ============================================
# 6. APPLY PATCHES FOR KERNEL 6.16
# ============================================
log "6. Applying base patches (kernel 6.16)..."

cd "$WORK_DIR"

# Find patched files in repository
REPO_SOURCE="$PATCH_DIR/vmware-vmmon-vmnet-linux-6.16.x/modules"

# Find the closest available version
if [ -d "$REPO_SOURCE/17.6.4/source" ]; then
    PATCH_SOURCE="$REPO_SOURCE/17.6.4/source"
elif [ -d "$REPO_SOURCE/17.6.0/source" ]; then
    PATCH_SOURCE="$REPO_SOURCE/17.6.0/source"
elif [ -d "$REPO_SOURCE/17.5.0/source" ]; then
    PATCH_SOURCE="$REPO_SOURCE/17.5.0/source"
else
    # Find any available version
    PATCH_SOURCE=$(find "$REPO_SOURCE" -type d -name "source" | head -1)
fi

if [ -z "$PATCH_SOURCE" ] || [ ! -d "$PATCH_SOURCE" ]; then
    error "Patched files not found in repository"
    exit 1
fi

info "Using patches from: $PATCH_SOURCE"

# Copy patched files from repository (patches for 6.16)
info "Applying patches to vmmon..."
if [ -d "$PATCH_SOURCE/vmmon-only" ]; then
    # Copy all patched files
    cp -rf "$PATCH_SOURCE/vmmon-only/"* "$WORK_DIR/vmmon-only/" 2>/dev/null || true
    log "✓ vmmon patches applied (6.16)"
else
    warning "No patches found for vmmon"
fi

info "Applying patches to vmnet..."
if [ -d "$PATCH_SOURCE/vmnet-only" ]; then
    # Copy all patched files
    cp -rf "$PATCH_SOURCE/vmnet-only/"* "$WORK_DIR/vmnet-only/" 2>/dev/null || true
    log "✓ vmnet patches applied (6.16)"
else
    warning "No patches found for vmnet"
fi

log "✓ Base patches (6.16) applied"

# ============================================
# 7. DETECT IF OBJTOOL PATCHES ARE NEEDED
# ============================================
log "7. Detecting if objtool patches are needed..."

# Check if kernel version is 6.16.3+ or 6.17+
# These kernels have stricter objtool validation
NEED_OBJTOOL_PATCHES=false

if [ "$TARGET_KERNEL" = "6.17" ]; then
    NEED_OBJTOOL_PATCHES=true
    info "Kernel 6.17 selected - objtool patches will be applied"
elif [ "$KERNEL_MAJOR" = "6" ] && [ "$KERNEL_MINOR" = "16" ]; then
    # Check if it's 6.16.3 or higher (which has stricter objtool)
    KERNEL_PATCH=$(echo $KERNEL_VERSION | cut -d. -f3 | cut -d- -f1)
    if [ "$KERNEL_PATCH" -ge 3 ] 2>/dev/null; then
        NEED_OBJTOOL_PATCHES=true
        warning "Kernel 6.16.$KERNEL_PATCH detected - this version has strict objtool validation"
        info "Objtool patches will be applied automatically"
    fi
fi

# ============================================
# 8. APPLY OBJTOOL PATCHES IF NEEDED
# ============================================
if [ "$NEED_OBJTOOL_PATCHES" = true ]; then
    log "8. Applying objtool patches..."
    
    info "These patches disable objtool validation for problematic files..."
    
    # Patch 1: Modify vmmon Makefile.kernel to disable objtool
    info "Patching vmmon/Makefile.kernel..."
    cat > "$WORK_DIR/vmmon-only/Makefile.kernel" << 'EOF'
#!/usr/bin/make -f
##########################################################
# Copyright (c) 1998-2024 Broadcom. All Rights Reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation version 2 and no later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
##########################################################

CC_OPTS += -DVMMON -DVMCORE

INCLUDE := -I$(SRCROOT)/include -I$(SRCROOT)/include/x86 -I$(SRCROOT)/common -I$(SRCROOT)/linux
ccflags-y := $(CC_OPTS) $(INCLUDE)

obj-m += $(DRIVER).o

$(DRIVER)-y := $(subst $(SRCROOT)/, , $(patsubst %.c, %.o, \
		$(wildcard $(SRCROOT)/linux/*.c $(SRCROOT)/common/*.c \
		$(SRCROOT)/bootstrap/*.c)))

# Disable objtool for problematic files in kernel 6.17+
OBJECT_FILES_NON_STANDARD_common/phystrack.o := y
OBJECT_FILES_NON_STANDARD_common/task.o := y
OBJECT_FILES_NON_STANDARD := y

clean:
	rm -rf $(wildcard $(DRIVER).mod.c $(DRIVER).ko .tmp_versions \
		Module.symvers Modules.symvers Module.markers modules.order \
		$(foreach dir,linux/ common/ bootstrap/ \
		./,$(addprefix $(dir),.*.cmd .*.o.flags *.o)))
EOF
    
    log "✓ vmmon/Makefile.kernel patched for 6.17"
    
    # Patch 2: Remove unnecessary returns in phystrack.c
    if [ -f "$WORK_DIR/vmmon-only/common/phystrack.c" ]; then
        info "Patching phystrack.c (removing unnecessary returns)..."
        sed -i '324s/return;$//' "$WORK_DIR/vmmon-only/common/phystrack.c" 2>/dev/null || true
        sed -i '368s/return;$//' "$WORK_DIR/vmmon-only/common/phystrack.c" 2>/dev/null || true
        log "✓ phystrack.c patched"
    fi
    
    # Patch 3: Check if task.c needs patches
    if [ -f "$WORK_DIR/vmmon-only/common/task.c" ]; then
        if grep -q "return;" "$WORK_DIR/vmmon-only/common/task.c" 2>/dev/null; then
            info "Patching task.c (removing unnecessary returns)..."
            sed -i '/^void.*{$/,/^}$/ { /^   return;$/d }' "$WORK_DIR/vmmon-only/common/task.c"
            log "✓ task.c patched"
        fi
    fi
    
    # Patch 4: Patch vmnet Makefile.kernel to disable objtool
    info "Patching vmnet/Makefile.kernel..."
    if ! grep -q "OBJECT_FILES_NON_STANDARD" "$WORK_DIR/vmnet-only/Makefile.kernel"; then
        # Find the line with obj-m and add after it
        sed -i '/^obj-m += \$(DRIVER)\.o/a\\n# Disable objtool for problematic files in kernel 6.17+\nOBJECT_FILES_NON_STANDARD_userif.o := y\nOBJECT_FILES_NON_STANDARD := y' "$WORK_DIR/vmnet-only/Makefile.kernel"
        log "✓ vmnet/Makefile.kernel patched for 6.17"
    else
        info "vmnet/Makefile.kernel already has objtool patches"
    fi
    
    log "✓ Objtool patches applied"
else
    info "8. Objtool patches not needed for this kernel version"
fi

# ============================================
# 9. COMPILE MODULES
# ============================================
log "9. Compiling modules..."

# Configure compilation variables
if [ "$DISTRO" = "fedora" ]; then
    export KERNEL_DIR="/usr/src/kernels/$KERNEL_VERSION"
elif [ "$DISTRO" = "gentoo" ]; then
    # Try versioned kernel directory first, fallback to /usr/src/linux
    if [ -d "/usr/src/linux-$KERNEL_VERSION" ]; then
        export KERNEL_DIR="/usr/src/linux-$KERNEL_VERSION"
    else
        export KERNEL_DIR="/usr/src/linux"
    fi
else
    export KERNEL_DIR="/lib/modules/$KERNEL_VERSION/build"
fi

if [ "$USING_CLANG" = true ]; then
    export CC=clang
    export LD=ld.lld
    export LLVM=1
    info "Using toolchain: Clang/LLVM"
else
    export CC=gcc
    export LD=ld
    info "Using toolchain: GCC/GNU"
fi

# Apply optimization flags if selected
if [ -n "$EXTRA_CFLAGS" ]; then
    export CFLAGS_EXTRA="$EXTRA_CFLAGS"
    export CFLAGS="$EXTRA_CFLAGS"
    info "Applying optimization flags: $EXTRA_CFLAGS"
fi

# Compile vmmon
info "Compiling vmmon..."
cd "$WORK_DIR/vmmon-only"
make clean 2>/dev/null || true

if make -j$(nproc) 2>&1 | tee "$LOG_FILE.vmmon"; then
    if [ -f "vmmon.ko" ]; then
        log "✓ vmmon compiled successfully"
    else
        error "vmmon.ko was not generated"
        cat "$LOG_FILE.vmmon"
        exit 1
    fi
else
    error "Error compiling vmmon"
    cat "$LOG_FILE.vmmon"
    exit 1
fi

# Compile vmnet
info "Compiling vmnet..."
cd "$WORK_DIR/vmnet-only"
make clean 2>/dev/null || true

if make -j$(nproc) 2>&1 | tee "$LOG_FILE.vmnet"; then
    if [ -f "vmnet.ko" ]; then
        log "✓ vmnet compiled successfully"
    else
        error "vmnet.ko was not generated"
        cat "$LOG_FILE.vmnet"
        exit 1
    fi
else
    error "Error compiling vmnet"
    cat "$LOG_FILE.vmnet"
    exit 1
fi

log "✓ Modules compiled successfully"

# ============================================
# 10. INSTALL MODULES
# ============================================
log "10. Installing modules..."

# Unload current modules
info "Unloading current modules..."
sudo modprobe -r vmnet vmmon 2>/dev/null || true
sudo rmmod vmnet 2>/dev/null || true
sudo rmmod vmmon 2>/dev/null || true

# Create misc directory if it doesn't exist
sudo mkdir -p "/lib/modules/$KERNEL_VERSION/misc/"

# Copy new modules
info "Copying vmmon.ko..."
sudo cp "$WORK_DIR/vmmon-only/vmmon.ko" "/lib/modules/$KERNEL_VERSION/misc/"

info "Copying vmnet.ko..."
sudo cp "$WORK_DIR/vmnet-only/vmnet.ko" "/lib/modules/$KERNEL_VERSION/misc/"

# Update module dependencies
info "Updating module dependencies..."
sudo depmod -a

# Load modules
info "Loading modules..."
if sudo modprobe vmmon; then
    log "✓ vmmon loaded"
else
    error "Error loading vmmon"
    dmesg | tail -20
    exit 1
fi

if sudo modprobe vmnet; then
    log "✓ vmnet loaded"
else
    error "Error loading vmnet"
    dmesg | tail -20
    exit 1
fi

log "✓ Modules installed and loaded"

# ============================================
# 11. CREATE TARBALL FOR VMWARE
# ============================================

# Skip tarball creation for Gentoo (modules already installed)
if [ "$DISTRO" = "gentoo" ]; then
    log "11. Gentoo detected - skipping tarball creation"
    info "Modules have been installed directly to /lib/modules"
    echo ""
    log "✓ Gentoo installation completed successfully!"
    exit 0
fi

log "11. Creating tarballs for VMware..."

cd "$WORK_DIR"

# Clean compilation artifacts before creating tarballs
info "Cleaning vmmon build artifacts..."
cd "$WORK_DIR/vmmon-only"
make clean 2>/dev/null || true
# Remove any remaining build artifacts
find . -name "*.o" -o -name "*.ko" -o -name "*.cmd" -o -name "*.mod" -o -name "*.mod.c" -o -name ".*.d" | xargs rm -f 2>/dev/null || true
rm -rf .tmp_versions Module.symvers Modules.symvers Module.markers modules.order 2>/dev/null || true

info "Cleaning vmnet build artifacts..."
cd "$WORK_DIR/vmnet-only"
make clean 2>/dev/null || true
# Remove any remaining build artifacts
find . -name "*.o" -o -name "*.ko" -o -name "*.cmd" -o -name "*.mod" -o -name "*.mod.c" -o -name ".*.d" | xargs rm -f 2>/dev/null || true
rm -rf .tmp_versions Module.symvers Modules.symvers Module.markers modules.order 2>/dev/null || true

cd "$WORK_DIR"

# Create new tarballs (now clean, without build artifacts)
info "Creating vmmon.tar..."
tar -cf vmmon.tar vmmon-only

info "Creating vmnet.tar..."
tar -cf vmnet.tar vmnet-only

# Copy to VMware directory
info "Installing tarballs to VMware..."
sudo cp vmmon.tar "$VMWARE_MOD_DIR/"
sudo cp vmnet.tar "$VMWARE_MOD_DIR/"

log "✓ Tarballs installed (cleaned source code only)"

# ============================================
# 12. RESTART VMWARE SERVICES
# ============================================
log "12. Restarting VMware services..."

# Try to restart services (may fail if not active)
sudo systemctl restart vmware.service 2>/dev/null || sudo /etc/init.d/vmware restart 2>/dev/null || true
sudo systemctl restart vmware-USBArbitrator.service 2>/dev/null || true
sudo systemctl restart vmware-networks.service 2>/dev/null || true

log "✓ Services restarted"

# ============================================
# 13. VERIFY INSTALLATION
# ============================================
log "13. Verifying installation..."

echo ""
info "Loaded modules:"
lsmod | grep -E "vmmon|vmnet" | sed 's/^/  /'

echo ""
info "Module information:"
modinfo vmmon 2>/dev/null | grep -E "filename|version|description" | sed 's/^/  /' || warning "Could not get vmmon info"
echo ""
modinfo vmnet 2>/dev/null | grep -E "filename|version|description" | sed 's/^/  /' || warning "Could not get vmnet info"

echo ""
info "VMware service status:"
systemctl status vmware.service --no-pager -l 2>/dev/null | grep Active | sed 's/^/  /' || warning "VMware service not available"

# ============================================
# 14. CLEANUP
# ============================================
log "14. Cleaning up temporary files..."

cd "$HOME"
rm -rf "$WORK_DIR"
info "Temporary directory removed"

echo ""
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✓ COMPILATION AND INSTALLATION COMPLETED${NC}"
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo ""

info "Summary:"
echo "  • Kernel: $KERNEL_VERSION"
echo "  • Patches applied: Kernel $TARGET_KERNEL"
echo "  • Objtool patches: $([ "$NEED_OBJTOOL_PATCHES" = true ] && echo "YES (auto-detected)" || echo "NO (not needed)")"
echo "  • Distribution: $DISTRO"
echo "  • Compiler: $KERNEL_COMPILER"
echo "  • VMware: $VMWARE_VERSION"
echo "  • Modules: vmmon, vmnet"
echo "  • Backup: $BACKUP_DIR"
echo "  • Log: $LOG_FILE"
echo ""

info "Applied patches:"
echo "  ✓ Build System: EXTRA_CFLAGS → ccflags-y"
echo "  ✓ Timer API: del_timer_sync() → timer_delete_sync()"
echo "  ✓ MSR API: rdmsrl_safe() → rdmsrq_safe()"
echo "  ✓ Module Init: init_module() → module_init()"
echo "  ✓ Module Exit: cleanup_module() → module_exit()"
echo "  ✓ Function Prototypes: function() → function(void)"
echo "  ✓ Source: https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x"

if [ "$NEED_OBJTOOL_PATCHES" = true ]; then
    echo ""
    info "Additional objtool patches (auto-detected):"
    echo "  ✓ Objtool: OBJECT_FILES_NON_STANDARD enabled"
    echo "  ✓ phystrack.c: Unnecessary returns removed"
    echo "  ✓ task.c: Unnecessary returns removed"
    echo "  ✓ vmnet: Objtool disabled for userif.o"
    echo "  ℹ  These patches were automatically applied for kernel $KERNEL_VERSION"
fi

echo ""

warning "IMPORTANT:"
echo "  • Modules are compiled for kernel $KERNEL_VERSION"
echo "  • Patches applied for: Kernel $TARGET_KERNEL (with auto-detected objtool fixes)"
echo "  • If you update the kernel, run this script again"
echo "  • If VMware doesn't start, run: sudo vmware-modconfig --console --install-all"
echo ""

info "To verify VMware works correctly:"
echo "  vmware &"
echo ""

log "Process completed successfully!"