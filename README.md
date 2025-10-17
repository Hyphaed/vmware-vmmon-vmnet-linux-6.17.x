# VMware Workstation Modules for Linux Kernel 6.16.x & 6.17.x

[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![Kernel](https://img.shields.io/badge/Kernel-6.16.x%20%7C%206.17.x-orange.svg)](https://kernel.org/)
[![VMware](https://img.shields.io/badge/VMware-17.6.4-green.svg)](https://www.vmware.com/)
[![Gentoo](https://img.shields.io/badge/Gentoo-Supported-purple.svg)](https://www.gentoo.org/)

This repository provides **kernel compatibility patches** and **optional performance optimizations** for VMware Workstation modules (`vmmon` and `vmnet`) on Linux kernel **6.16.x** and **6.17.x** series with support for **Ubuntu, Fedora, and Gentoo**.

## 🎯 Purpose

VMware Workstation modules often lag behind the latest kernel releases. This repository provides:

1. **Kernel Compatibility Patches**: Make VMware modules work with kernel 6.16.x and 6.17.x
2. **Performance Optimizations**: Optional hardware-specific and VM performance enhancements
3. **Interactive Installation**: Terminal-based assistant guides you through:
   - Kernel version selection (6.16 or 6.17)
   - Hardware optimization levels (4 options from safe to aggressive)
   - CPU feature detection (AVX2, SSE4.2, AES-NI)
   - Kernel feature detection (modern MM, DMA optimizations)
   - VM performance enhancements (memory allocation, low latency mode)

## ✨ Features

- **Dual Kernel Support**: Compatible with both Linux kernel 6.16.x and 6.17.x series
- **Interactive Installation**: Prompts you to select target kernel version (6.16 or 6.17) at startup
- **Smart Patching**: Automatically applies appropriate patches based on your selection
- **Intelligent Objtool Detection**: Automatically detects if objtool patches are needed (e.g., kernel 6.16.3+)
- **Objtool Fixes**: Resolves objtool validation errors introduced in newer kernels
- **Multi-Distribution Support**: Works on Ubuntu/Debian, Fedora/RHEL, and Gentoo Linux
- **Hardware Optimizations** (NEW): Optional CPU-specific optimizations (Native/Conservative/None)
- **Compiler Detection**: Auto-detects and uses GCC or Clang toolchain
- **VMware 17.6.4 Compatible**: Tested with VMware Workstation 17.6.4
- **Easy Installation**: Fully automated script for patching and compilation
- **Update Utility** (NEW): Quick module updates after kernel upgrades
- **Restore Utility** (NEW): Restore from previous backups with ease

## 🔧 What's Fixed

### Kernel 6.16.x Patches (from [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x))

1. **Build System**: `EXTRA_CFLAGS` → `ccflags-y`
2. **Timer API**: `del_timer_sync()` → `timer_delete_sync()`
3. **MSR API**: `rdmsrl_safe()` → `rdmsrq_safe()`
4. **Module Init**: `init_module()` → `module_init()` macro
5. **Function Prototypes**: `function()` → `function(void)`

### Kernel 6.16.3+ and 6.17.x Additional Patches (Auto-Detected)

Starting with kernel 6.16.3, stricter objtool validation was introduced. The script automatically detects if these patches are needed:

1. **Objtool validation errors** in `phystrack.c` and `task.c`
2. **Makefile adjustments** to disable objtool for problematic object files (`OBJECT_FILES_NON_STANDARD`)
3. **Return statement issues** in void functions
4. **Enhanced objtool compatibility** for stricter kernel validation

> **Note**: Even if you select "Kernel 6.16", the script will automatically apply objtool patches if you're running kernel 6.16.3 or higher.

## 📋 Prerequisites

- Linux kernel **6.16.x or 6.17.x** headers installed
- VMware Workstation 17.x installed
- Build essentials: `gcc`, `make`, `kernel headers`
- Git (for cloning the repository)

```bash
# Ubuntu/Debian
sudo apt install build-essential linux-headers-$(uname -r) git

# Fedora/RHEL
sudo dnf install gcc make kernel-devel kernel-headers git

# Gentoo
# Ensure kernel sources are installed and configured
emerge -av sys-kernel/gentoo-sources
cd /usr/src/linux && make modules_prepare

# Arch Linux
sudo pacman -S base-devel linux-headers git
```

## 🚀 Quick Start

### Method 1: Automated Script (Recommended)

1. Clone this repository:
```bash
git clone https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x.git
cd vmware-vmmon-vmnet-linux-6.17.x
```

2. Run the automated installation script (from the scripts directory or anywhere):
```bash
# Option A: Run from scripts directory
cd scripts
sudo bash install-vmware-modules.sh

# Option B: Run from repository root
sudo bash scripts/install-vmware-modules.sh

# Option C: Run from anywhere with absolute path
sudo bash /path/to/vmware-vmmon-vmnet-linux-6.17.x/scripts/install-vmware-modules.sh
```

> **Note**: The script automatically detects its location, so log files will be saved in the `scripts/` directory regardless of where you run it from.

3. **Select your kernel version** when prompted:
```
Which kernel version do you want to compile for? (1=6.16 / 2=6.17):
```
   - Choose **1** for kernel 6.16.x
   - Choose **2** for kernel 6.17.x

4. The script will automatically:
   - Download appropriate patches from GitHub
   - Apply kernel-specific fixes
   - Compile and install the modules
   - Load the modules and restart VMware services

5. Reboot your system (if required)

### Method 2: Manual Installation

1. Extract VMware modules:
```bash
cd /tmp
tar -xf /usr/lib/vmware/modules/source/vmmon.tar
tar -xf /usr/lib/vmware/modules/source/vmnet.tar
```

2. Apply the patches:
```bash
cd vmmon-only
patch -p1 < /path/to/vmmon-6.17.patch
cd ../vmnet-only
patch -p1 < /path/to/vmnet-6.17.patch
```

3. Compile and install:
```bash
cd vmmon-only
make
sudo make install
cd ../vmnet-only
make
sudo make install
```

4. Load the modules:
```bash
sudo modprobe vmmon
sudo modprobe vmnet
```

## 📁 Repository Structure

```
vmware-vmmon-vmnet-linux-6.17.x/
├── patches/
│   ├── vmmon-6.17.patch            # Patch for vmmon module
│   ├── vmnet-6.17.patch            # Patch for vmnet module
│   └── README.md                   # Patch documentation
├── scripts/
│   ├── install-vmware-modules.sh   # Full installation with optimizations
│   ├── update-vmware-modules.sh    # Quick update after kernel upgrade
│   ├── restore-vmware-modules.sh   # Restore from backup
│   └── test-vmware-modules.sh      # Module testing utility
├── docs/
│   ├── TROUBLESHOOTING.md          # Common issues and solutions
│   └── TECHNICAL.md                # Technical details about patches
├── LICENSE                          # GPL v2 License
└── README.md                        # This file
```

## 💡 How the Interactive Installation Works

When you run the installation script, it will:

1. **Detect your system**: Automatically identifies your kernel version, distribution (Ubuntu/Debian/Fedora), and compiler (GCC/Clang)

2. **Prompt for kernel version**: Asks you to choose between kernel 6.16.x or 6.17.x patches
   ```
   ════════════════════════════════════════
   KERNEL VERSION SELECTION
   ════════════════════════════════════════
   
   This script supports two kernel versions with specific patches:
   
     1) Kernel 6.16.x
        • Uses patches from: https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x
        • Patches: timer_delete_sync(), rdmsrq_safe(), module_init()
   
     2) Kernel 6.17.x
        • Uses patches from 6.16.x + additional objtool patches
        • Additional patches: OBJECT_FILES_NON_STANDARD, returns in void functions
   
   Kernel detected on your system: 6.16.9-200.fc42.x86_64
   
   Which kernel version do you want to compile for? (1=6.16 / 2=6.17):
   ```

3. **Apply appropriate patches**: 
   - For **6.16**: Downloads and applies patches from the GitHub repository
   - For **6.17**: Applies 6.16 patches + additional objtool fixes
   - **Auto-detection**: If kernel 6.16.3+ is detected, objtool patches are applied automatically

4. **Compile and install**: Automatically compiles, installs, and loads the modules

5. **Verify installation**: Shows loaded modules and service status

## 🧪 Testing

### Quick Manual Test

After installation, verify that the modules are loaded correctly:

```bash
lsmod | grep vm
```

You should see output similar to:
```
vmnet                  86016  13
vmmon                 122880  0
```

### Comprehensive Test Script

Use the included test utility for a complete system check:

```bash
bash scripts/test-vmware-modules.sh
```

This script will verify:
- ✓ Loaded modules (vmmon, vmnet)
- ✓ Module information and versions
- ✓ Device files (/dev/vmmon, /dev/vmnet0)
- ✓ VMware service status
- ✓ Source tarball integrity
- ✓ Available backups

Test VMware Workstation by launching a virtual machine.

## 🔄 Update Modules After Kernel Upgrade

When you upgrade your kernel, VMware modules need to be recompiled. Use the update utility:

```bash
sudo bash scripts/update-vmware-modules.sh
```

The update script will:
- ✓ Detect your current kernel version
- ✓ Check if modules need updating
- ✓ Run the full installation for the new kernel
- ✓ Show before/after module status

## 🔙 Restore from Backup

If something goes wrong, restore from a previous backup:

```bash
sudo bash scripts/restore-vmware-modules.sh
```

The restore script will:
- ✓ List all available backups with timestamps
- ✓ Show file sizes and modification dates
- ✓ Let you choose which backup to restore
- ✓ Safely restore with confirmation prompts

Backups are created automatically during:
- Initial installation (`install-vmware-modules.sh`)
- Updates (`update-vmware-modules.sh`)

## ⚡ Hardware Optimizations (Optional)

During installation, you can choose CPU-specific optimizations:

**1) Native (Recommended for this CPU)**
- Flags: `-O2 -pipe -march=native -mtune=native`
- Best performance for your specific CPU
- Modules won't work on different CPUs

**2) Conservative (Safe, portable)**
- Flags: `-O2 -pipe`
- Standard optimization level
- Works on any x86_64 CPU

**3) None (Default kernel flags)**
- Uses same flags as your kernel
- Safest option

The script will:
- Auto-detect your CPU model and features (AVX2, SSE4.2, etc.)
- Show available optimizations
- Let you choose optimization level
- Apply flags during compilation

**Note**: These are conservative, kernel-safe optimizations. Aggressive flags can cause module instability.

## 🐛 Troubleshooting

### Module compilation fails

**Solution**: Ensure you have the correct kernel headers installed:
```bash
sudo apt install linux-headers-$(uname -r)
```

### Modules don't load

**Solution**: Check dmesg for errors:
```bash
sudo dmesg | grep -i vmware
```

### VMware Workstation doesn't start

**Solution**: Rebuild the modules:
```bash
sudo vmware-modconfig --console --install-all
```

For more troubleshooting tips, see [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## 🔄 Compatibility

| Kernel Version | VMware Version | Status | Notes |
|---------------|----------------|--------|-------|
| 6.16.0-6.16.2 | 17.6.4         | ✅ Tested | Uses GitHub patches only |
| 6.16.3-6.16.9 | 17.6.4         | ✅ Tested | Auto-applies objtool patches (Pop!_OS, Ubuntu) |
| 6.17.0        | 17.6.4         | ✅ Tested | Ubuntu, additional objtool patches |
| 6.17.1+       | 17.6.4         | ✅ Tested | Additional objtool patches |

## 📝 Technical Details

### Kernel 6.16.x Changes

The script uses patches from [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x) which address:

1. **Build system updates**: Migration from `EXTRA_CFLAGS` to `ccflags-y`
2. **Timer API changes**: New `timer_delete_sync()` function
3. **MSR API updates**: New `rdmsrq_safe()` function
4. **Module initialization**: Deprecation of `init_module()` in favor of `module_init()` macro

### Kernel 6.17.x Additional Changes

Kernel 6.17 introduces stricter validation that requires additional patches:

1. **Enhanced objtool validation**: Kernel 6.17 has stricter objtool checks
2. **Stack validation changes**: New requirements for stack frame setup
3. **Function return handling**: Stricter validation of return statements in void functions
4. **Object file validation**: Requires `OBJECT_FILES_NON_STANDARD` flags for certain files

For detailed technical information, see [TECHNICAL.md](docs/TECHNICAL.md).

## 🙏 Acknowledgments

- Based on the excellent work from [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x)
- VMware community for continuous support
- Linux kernel developers

## 💖 Support This Project

If this project saved you hours of troubleshooting and helped you get VMware Workstation running on the latest kernel, consider buying me a coffee! Your support helps maintain this project and keep it updated with new kernel releases.

**Cash donations are welcomed and appreciated!** Every contribution, no matter how small, motivates continued development and support.

[![Sponsor](https://img.shields.io/badge/Sponsor-💖-ff69b4)](https://github.com/sponsors/Hyphaed)

\* Awaiting for Github Sponsors check

## 📜 License

This project is licensed under the GNU General Public License v2.0 - see the [LICENSE](LICENSE) file for details.
The VMware modules themselves are proprietary software by Broadcom Inc. These patches only modify the open-source components necessary for kernel compatibility.

## 📧 Contact

- **GitHub**: [@Hyphaed](https://github.com/Hyphaed)
- **Issues**: [Report a bug](https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/issues)
---

**Star ⭐ this repository if it helped you!**
