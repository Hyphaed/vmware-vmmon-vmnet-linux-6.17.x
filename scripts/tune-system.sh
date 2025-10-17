#!/bin/bash
# VMware System Optimizer - Standalone Script
# Wrapper for Python-based system tuning
# Can be run independently at any time

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
HYPHAED_GREEN='\033[38;2;176;213;106m'

# Detectar directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Skip banner if called with --auto-confirm (already shown in wizard)
if [ "$1" != "--auto-confirm" ]; then
    echo -e "${HYPHAED_GREEN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║       VMware WORKSTATION SYSTEM OPTIMIZER                   ║
║          Tune Your System for Best Performance               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    echo ""
    echo -e "${YELLOW}This tool will optimize your Linux system for VMware Workstation:${NC}"
    echo ""
    echo "  • GRUB boot parameters (IOMMU, hugepages, mitigations)"
    echo "  • Kernel parameters (memory, network, scheduler)"
    echo "  • CPU governor (performance mode)"
    echo "  • I/O scheduler (NVMe/SSD optimization)"
    echo "  • Install performance packages"
    echo ""
    echo -e "${YELLOW}All changes are backed up automatically.${NC}"
    echo ""
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}✗ This script must be run as root (use sudo)${NC}"
    echo ""
    exit 1
fi

# Determine which Python to use (prefer conda environment)
MINIFORGE_DIR="$HOME/.miniforge3"
ENV_NAME="vmware-optimizer"

# If running with sudo, use the actual user's home directory
if [ -n "$SUDO_USER" ]; then
    MINIFORGE_DIR="/home/$SUDO_USER/.miniforge3"
fi

if [ -f "$MINIFORGE_DIR/envs/$ENV_NAME/bin/python" ]; then
    echo -e "${GREEN}[i]${NC} Using conda environment Python"
    PYTHON_CMD="$MINIFORGE_DIR/envs/$ENV_NAME/bin/python"
elif command -v python3 &>/dev/null; then
    echo -e "${YELLOW}[!]${NC} Using system Python (conda environment not found)"
    PYTHON_CMD="python3"
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "Please install Python 3 first"
    exit 1
fi

# Run Python optimizer
OPTIMIZER_SCRIPT="$SCRIPT_DIR/tune_system.py"

if [ ! -f "$OPTIMIZER_SCRIPT" ]; then
    echo -e "${RED}✗ Optimizer script not found: $OPTIMIZER_SCRIPT${NC}"
    exit 1
fi

# Make executable
chmod +x "$OPTIMIZER_SCRIPT"

# Run optimizer
echo -e "${GREEN}Launching system optimizer...${NC}"
echo ""

# Pass --auto-confirm flag if first argument is provided
if [ "$1" = "--auto-confirm" ]; then
    "$PYTHON_CMD" "$OPTIMIZER_SCRIPT" --auto-confirm
else
    "$PYTHON_CMD" "$OPTIMIZER_SCRIPT"
fi
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ System optimization completed successfully!${NC}"
    echo ""
else
    echo ""
    echo -e "${YELLOW}System optimization exited with code: $EXIT_CODE${NC}"
    echo ""
fi

exit $EXIT_CODE

