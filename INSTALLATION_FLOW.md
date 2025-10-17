# VMware Module Installation Flow

## Overview
Complete step-by-step flow of the VMware kernel module compilation wizard with PyTermGUI interface.

## Installation Steps

### 1. Root Privilege Check
**Location**: `install-vmware-modules.sh` (lines 10-31)
- **Check**: Verifies script is running as root/sudo
- **Action**: If not root, displays error message and exits
- **Message**: Shows requirements and proper `sudo` command
- **Exit Code**: 1 if not root

### 2. VMware Status Check
**Location**: `install-vmware-modules.sh` (lines 94-119)
- **Check**: Verifies VMware is not currently running
- **Action**: If running, lists processes and exits with instructions
- **Requirement**: All VMware applications must be closed before compilation

### 3. Interactive Wizard (PyTermGUI)
**Location**: `vmware_wizard.py`
- **Interface**: GTK4-styled terminal UI with keyboard navigation
- **Width**: 90% of terminal width
- **Height**: 30% of terminal height

#### Step 1: Welcome Screen
- Displays 5-step installation overview
- Shows keyboard navigation hints
- **Button**: "Start Installation"

#### Step 2: Kernel Detection (Automatic)
- Detects all installed kernels
- Filters for 6.16.x and 6.17.x versions
- Checks for kernel headers
- Auto-selects current kernel with headers
- **Fallback**: First supported kernel if current not available

#### Step 3: Hardware Detection (Background)
**Location**: `detect_hardware.py`
- Runs in background during wizard
- Analyzes CPU, virtualization, storage, memory, GPU
- Generates optimization recommendations
- **Output**: `/tmp/vmware_hw_capabilities.json`
- **Permission handling**: Uses PID-based filename if permission denied

#### Step 4: Optimization Mode Selection (User Choice)
- **Optimized Mode**:
  - Hardware-specific optimizations
  - VT-x/EPT enhancements
  - AVX-512 SIMD (if available)
  - Branch prediction hints
  - Cache alignment
  - 30-45% performance improvement
  
- **Vanilla Mode**:
  - Standard kernel-compatible build
  - Maximum portability
  - Generic x86_64 optimizations
  - Recommended for module portability

- **UI Elements**:
  - Detailed comparison table
  - Hardware-based recommendation
  - Two buttons for selection
  - Keyboard navigation (Tab/Arrow keys)

#### Step 5: Configuration Export
- Saves selected options to `/tmp/vmware_wizard_config.sh`
- **Exported Variables**:
  - `WIZARD_COMPLETED=true`
  - `SELECTED_KERNELS`
  - `TARGET_KERNEL_VERSION`
  - `OPTIMIZATION_MODE` (optimized/vanilla)

### 4. Hardware Detection Reuse
**Location**: `install-vmware-modules.sh` (lines 640-653)
- **Check**: If wizard ran and JSON exists, reuse it
- **Skip**: Full hardware detection if already done by wizard
- **Extract**: Optimization score, recommended mode, CPU features
- **Benefit**: No duplicate detection, faster workflow

### 5. Distribution Detection
- Identifies Linux distribution (Ubuntu/Fedora/Gentoo)
- Determines package manager and paths
- Sets VMware module directory

### 6. System Verification
- Checks kernel headers installation
- Verifies compiler availability (GCC/Clang)
- Confirms VMware installation
- Lists loaded VMware modules

### 7. Patch Application
**Vanilla Mode**: Basic kernel compatibility patches only
**Optimized Mode**: All patches including:
- `vmmon-vtx-ept-optimizations.patch` - VT-x/EPT enhancements
- `vmmon-performance-opts.patch` - Branch hints, cache alignment
- `vmnet-optimizations.patch` - Network module optimizations

### 8. Module Compilation
**Location**: `install-vmware-modules.sh` (lines 1828-1908)

#### vmmon Compilation
```bash
cd vmmon-only
make clean
make -j$(nproc) VMWARE_OPTIMIZE=1 [additional flags]
```
- **Output**: `vmmon.ko`
- **Log**: `vmware_build_*.log.vmmon`
- **Flags** (Optimized mode):
  - `VMWARE_OPTIMIZE=1`
  - `ARCH_FLAGS="-march=native -mtune=native"`
  - `HAS_VTX_EPT=1` (if hardware supports)
  - `HAS_AVX512=1` (if CPU has AVX-512)
  - `HAS_NVME=1` (if NVMe detected)

#### vmnet Compilation
```bash
cd vmnet-only
make clean
make -j$(nproc) [same optimization flags]
```
- **Output**: `vmnet.ko`
- **Log**: `vmware_build_*.log.vmnet`

### 9. Module Installation
**Location**: `install-vmware-modules.sh` (lines 1915-2009)

1. **Unload current modules**:
   ```bash
   modprobe -r vmnet vmmon
   rmmod vmnet vmmon
   ```

2. **Copy new modules**:
   ```bash
   cp vmmon.ko /lib/modules/$(uname -r)/misc/
   cp vmnet.ko /lib/modules/$(uname -r)/misc/
   ```

3. **Update dependencies**:
   ```bash
   depmod -a
   ```

4. **Update initramfs** (distribution-specific):
   - Ubuntu/Debian: `update-initramfs -u`
   - Fedora/RHEL: `dracut -f`
   - Arch: `mkinitcpio -P`
   - Gentoo: `genkernel --install initramfs`

5. **Load new modules**:
   ```bash
   modprobe vmmon
   modprobe vmnet
   ```

### 10. Wayland Session Fix (Optional)
**Location**: `install-vmware-modules.sh` (lines 2011-2088)
- **Check**: If running Wayland session
- **Prompt**: Ask user if they want to apply Wayland fix
- **Action**: Patches VMware binaries for Wayland compatibility
- **Files**: `vmware`, `vmware-modconfig`
- **Backup**: Creates `.original` copies before patching

### 11. System Tuning Offer (Optional)
**Location**: `install-vmware-modules.sh` (lines 2183-2257)
- **Script**: `tune_system.py` (PyTermGUI wizard)
- **Optimizations**:
  - GRUB parameters (intel_iommu, hugepages, transparent_hugepages)
  - CPU governor (performance mode)
  - I/O scheduler optimization
  - Kernel parameters (swappiness, dirty ratios, writeback)
  - VMware-specific settings
  - Performance packages (tuned, cpufrequtils)
- **Note**: Requires reboot to take full effect
- **Can run later**: `sudo bash scripts/tune-system.sh`

### 12. Reboot Recommendation
**Location**: `install-vmware-modules.sh` (lines 2259-2274)
- **When**: If system tuning was applied
- **Reason**: GRUB parameters, hugepages, IOMMU require reboot
- **Next Steps**:
  1. Reboot system
  2. Start VMware
  3. Test virtual machines

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - all steps completed |
| 1 | Error - root check failed, VMware running, kernel not found, compilation failed, etc. |
| 130 | Cancelled by user (Ctrl+C) |

## Configuration Files

### Wizard Output
- **Path**: `/tmp/vmware_wizard_config.sh`
- **Format**: Bash source file
- **Lifetime**: Until next wizard run

### Hardware Detection
- **Path**: `/tmp/vmware_hw_capabilities.json` or `/tmp/vmware_hw_capabilities_<PID>.json`
- **Format**: JSON
- **Contents**: CPU features, optimization recommendations, hardware capabilities
- **Lifetime**: Until manual deletion or reboot

## Logs

### Main Installation Log
- **Path**: `scripts/vmware_build_YYYYMMDD_HHMMSS.log`
- **Contents**: Complete installation transcript with timestamps

### Compilation Logs
- **vmmon**: `scripts/vmware_build_*.log.vmmon`
- **vmnet**: `scripts/vmware_build_*.log.vmnet`
- **Contents**: Full `make` output including optimization flags

## Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Move to next button/field |
| Shift+Tab | Move to previous button/field |
| Arrow Keys | Navigate menu items |
| Enter | Activate button/confirm selection |
| Space | Toggle selection |
| 1/2/3 | Quick select numbered options |
| Ctrl+C | Cancel installation |

## Recovery

### Restore Original Modules
```bash
sudo bash scripts/restore-vmware-modules.sh
```

### Clean Build Artifacts
```bash
rm -rf /tmp/vmware_build_*
rm /tmp/vmware_wizard_config.sh
rm /tmp/vmware_hw_capabilities*.json
```

### Check Module Status
```bash
lsmod | grep vm
dmesg | grep vmmon
dmesg | grep vmnet
```

## Performance Verification

### Check Optimization Flags
```bash
# View build log
cat scripts/vmware_build_*.log.vmmon | grep "VMMON\|Optimization"

# Check module info
modinfo vmmon | grep vermagic
modinfo vmnet | grep vermagic
```

### Verify Hardware Detection
```bash
# Check dmesg for vmmon messages
dmesg | grep vmmon

# Look for optimization messages like:
# "VT-x with EPT support detected"
# "AVX-512 support detected"
```

## Troubleshooting

### Wizard Doesn't Start
- **Check**: Python environment activation
- **Verify**: pytermgui is installed
- **Run**: `$HOME/.miniforge3/envs/vmware-optimizer/bin/python -m pip list | grep pytermgui`

### Hardware Detection Fails
- **Fallback**: Wizard continues with basic detection
- **Check**: `/tmp/vmware_hw_capabilities.json` exists
- **Manual**: Run `python scripts/detect_hardware.py`

### Compilation Fails
- **Check**: Kernel headers installed (`dpkg -l | grep linux-headers`)
- **Verify**: Compiler available (`gcc --version`)
- **Review**: Compilation log files

### Modules Won't Load
- **Check**: Secure Boot status (`mokutil --sb-state`)
- **Solution**: Either disable Secure Boot or sign modules
- **Verify**: `dmesg | tail` for error messages

## Future Enhancements

### Planned Features
1. **Real-time Compilation Output in UI**
   - Live log viewer widget in PyTermGUI
   - Progress bar for compilation steps
   - Syntax-highlighted error messages

2. **Multi-Kernel Support**
   - Select multiple kernels simultaneously
   - Batch compilation for all selected kernels
   - Kernel-specific optimization profiles

3. **Benchmark Suite**
   - Automated performance testing
   - Before/after comparison
   - VM startup time measurement
   - I/O throughput testing

4. **Configuration Profiles**
   - Save optimization preferences
   - Quick profile switching
   - Share profiles between systems

