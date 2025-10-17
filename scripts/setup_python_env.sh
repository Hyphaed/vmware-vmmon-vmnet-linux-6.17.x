#!/bin/bash
# Setup Python environment for advanced hardware detection
# Uses mamba/miniforge for fast package management

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MINIFORGE_DIR="$HOME/.miniforge3"
ENV_NAME="vmware-optimizer"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }
warning() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

echo -e "${HYPHAED_GREEN}"
cat << 'EOF'
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║     VMware Optimizer - Python Environment Setup           ║
║          (Mamba/Miniforge + Python 3.14)                   ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if running with sudo
if [ "$EUID" -eq 0 ]; then
    error "This script should NOT be run with sudo"
    error "It will be called automatically by install script with correct user"
    exit 1
fi

info "Setting up Python environment for user: $(whoami)"
info "Installation directory: $MINIFORGE_DIR"

# 1. Check if miniforge3 is installed
if [ ! -d "$MINIFORGE_DIR" ]; then
    log "Miniforge3 not found. Installing..."
    
    # Detect architecture
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
    elif [ "$ARCH" = "aarch64" ]; then
        MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh"
    else
        error "Unsupported architecture: $ARCH"
        exit 1
    fi
    
    info "Downloading Miniforge3..."
    wget -q --show-progress "$MINIFORGE_URL" -O /tmp/miniforge.sh
    
    info "Installing Miniforge3 to $MINIFORGE_DIR..."
    bash /tmp/miniforge.sh -b -p "$MINIFORGE_DIR"
    rm /tmp/miniforge.sh
    
    # Initialize shell (suppress output)
    "$MINIFORGE_DIR/bin/conda" init bash >/dev/null 2>&1 || true
    
    log "✓ Miniforge3 installed"
    
    # Source conda to make it available immediately
    if [ -f "$MINIFORGE_DIR/etc/profile.d/conda.sh" ]; then
        source "$MINIFORGE_DIR/etc/profile.d/conda.sh"
    fi
else
    log "✓ Miniforge3 already installed"
    
    # Make sure conda is initialized
    if [ -f "$MINIFORGE_DIR/etc/profile.d/conda.sh" ]; then
        source "$MINIFORGE_DIR/etc/profile.d/conda.sh"
    fi
fi

# 2. Create or update environment
if conda env list | grep -q "^$ENV_NAME "; then
    info "Environment '$ENV_NAME' exists. Updating..."
    conda activate "$ENV_NAME"
    mamba update --all -y
else
    log "Creating new environment: $ENV_NAME (Python 3.12)"
    # Note: Python 3.14 is not released yet, using 3.12 (latest stable)
    mamba create -n "$ENV_NAME" python=3.12 -y
    conda activate "$ENV_NAME"
fi

# 3. Install required packages
log "Installing Python packages..."

# Core packages
mamba install -y \
    numpy \
    psutil \
    py-cpuinfo \
    pyyaml \
    click \
    rich \
    tabulate

# Hardware detection packages
pip install --upgrade \
    pynvml \
    pyudev \
    distro \
    questionary

log "✓ Python packages installed (including questionary for interactive UI)"

# 4. Install system packages (if needed)
log "Checking system dependencies..."

MISSING_PACKAGES=()

# Check for required system tools
command -v lscpu >/dev/null || MISSING_PACKAGES+=("util-linux")
command -v dmidecode >/dev/null || MISSING_PACKAGES+=("dmidecode")
command -v lspci >/dev/null || MISSING_PACKAGES+=("pciutils")
command -v lsblk >/dev/null || MISSING_PACKAGES+=("util-linux")
command -v numactl >/dev/null || MISSING_PACKAGES+=("numactl")

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    warning "Missing system packages detected: ${MISSING_PACKAGES[*]}"
    info "Installing with sudo..."
    
    # Detect package manager
    if command -v apt >/dev/null; then
        sudo apt update
        sudo apt install -y "${MISSING_PACKAGES[@]}"
    elif command -v dnf >/dev/null; then
        sudo dnf install -y "${MISSING_PACKAGES[@]}"
    elif command -v pacman >/dev/null; then
        sudo pacman -S --noconfirm "${MISSING_PACKAGES[@]}"
    elif command -v emerge >/dev/null; then
        sudo emerge -av "${MISSING_PACKAGES[@]}"
    else
        warning "Unknown package manager. Please install: ${MISSING_PACKAGES[*]}"
    fi
    
    log "✓ System packages installed"
fi

# 5. Test the detector script
log "Testing hardware detector..."
"$MINIFORGE_DIR/envs/$ENV_NAME/bin/python" "$SCRIPT_DIR/detect_hardware.py" > /tmp/hw_test.log 2>&1 && {
    log "✓ Hardware detector working"
    cat /tmp/hw_test.log
} || {
    error "Hardware detector test failed"
    cat /tmp/hw_test.log
    exit 1
}

# 6. Create activation script
ACTIVATE_SCRIPT="$SCRIPT_DIR/activate_optimizer_env.sh"
cat > "$ACTIVATE_SCRIPT" << EOF
#!/bin/bash
# Activate VMware Optimizer Python environment
source "$MINIFORGE_DIR/etc/profile.d/conda.sh"
conda activate $ENV_NAME
export VMWARE_PYTHON_ENV_ACTIVE=1
echo "✓ VMware Optimizer environment activated"
echo "Python: \$(python --version)"
echo "Location: \$(which python)"
EOF
chmod +x "$ACTIVATE_SCRIPT"

log "✓ Activation script created: $ACTIVATE_SCRIPT"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Python environment setup complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "To activate the environment manually:"
echo "  source $ACTIVATE_SCRIPT"
echo ""
echo "To use with install script:"
echo "  The install script will automatically detect and use this environment"
echo ""

