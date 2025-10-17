#!/bin/bash
# Activate VMware Optimizer Python environment
source "/home/ferran/.miniforge3/etc/profile.d/conda.sh"
conda activate vmware-optimizer
export VMWARE_PYTHON_ENV_ACTIVE=1
echo "✓ VMware Optimizer environment activated"
echo "Python: $(python --version)"
echo "Location: $(which python)"
