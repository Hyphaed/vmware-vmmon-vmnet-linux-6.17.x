# VMware Workstation Modules for Linux Kernel 6.17.x

[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![Kernel](https://img.shields.io/badge/Kernel-6.17.x-orange.svg)](https://kernel.org/)
[![VMware](https://img.shields.io/badge/VMware-17.6.4-green.svg)](https://www.vmware.com/)

This repository contains patches to make VMware Workstation modules (`vmmon` and `vmnet`) compatible with Linux kernel 6.17.x series.

## 🎯 Purpose

VMware Workstation modules often lag behind the latest kernel releases. This repository provides the necessary patches to compile and run VMware modules on kernel 6.17.x.

## ✨ Features

- **Kernel 6.17.x Support**: Full compatibility with Linux kernel 6.17.x series
- **Objtool Fixes**: Resolves objtool validation errors introduced in newer kernels
- **VMware 17.6.4 Compatible**: Tested with VMware Workstation 17.6.4
- **Easy Installation**: Automated scripts for patching and compilation

## 🔧 What's Fixed

The patches address the following issues specific to kernel 6.17.x:

1. **Objtool validation errors** in `phystrack.c` and `task.c`
2. **Makefile adjustments** to disable objtool for problematic object files
3. **Return statement issues** in void functions
4. **Compatibility with updated kernel APIs**

## 📋 Prerequisites

- Linux kernel 6.17.x headers installed
- VMware Workstation 17.x installed
- Build essentials: `gcc`, `make`, `kernel headers`
- Git (for cloning the repository)

```bash
# Ubuntu/Debian
sudo apt install build-essential linux-headers-$(uname -r) git

# Fedora/RHEL
sudo dnf install gcc make kernel-devel kernel-headers git

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

2. Run the automated installation script:
```bash
sudo bash install-vmware-modules.sh
```

3. Reboot your system (if required)

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
│   ├── vmmon-6.17.patch          # Patch for vmmon module
│   ├── vmnet-6.17.patch          # Patch for vmnet module
│   └── README.md                 # Patch documentation
├── scripts/
│   ├── install-vmware-modules.sh # Automated installation script
│   ├── apply-patches-6.17.sh     # Patch application script
│   └── test-vmware-modules.sh    # Module testing script
├── docs/
│   ├── TROUBLESHOOTING.md        # Common issues and solutions
│   └── TECHNICAL.md              # Technical details about patches
├── LICENSE                        # GPL v2 License
└── README.md                      # This file
```

## 🧪 Testing

After installation, verify that the modules are loaded correctly:

```bash
lsmod | grep vm
```

You should see output similar to:
```
vmnet                  86016  13
vmmon                 122880  0
```

Test VMware Workstation by launching a virtual machine.

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

| Kernel Version | VMware Version | Status |
|---------------|----------------|--------|
| 6.17.0        | 17.6.4         | ✅ Tested |
| 6.17.1        | 17.6.4         | ✅ Tested |
| 6.17.2+       | 17.6.4         | ⚠️ Should work |

## 📝 Technical Details

The main changes in kernel 6.17.x that affect VMware modules:

1. **Enhanced objtool validation**: Kernel 6.17 has stricter objtool checks
2. **Stack validation changes**: New requirements for stack frame setup
3. **Function return handling**: Stricter validation of return statements in void functions

For detailed technical information, see [TECHNICAL.md](docs/TECHNICAL.md).

## 🙏 Acknowledgments

- Based on the excellent work from [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x)
- VMware community for continuous support
- Linux kernel developers

## 📜 License

This project is licensed under the GNU General Public License v2.0 - see the [LICENSE](LICENSE) file for details.

The VMware modules themselves are proprietary software by Broadcom Inc. These patches only modify the open-source components necessary for kernel compatibility.

## ⚠️ Disclaimer

This is an unofficial patch. Use at your own risk. The author is not responsible for any damage to your system.

Always backup your system before applying kernel patches.

## 📧 Contact

- **GitHub**: [@Hyphaed](https://github.com/Hyphaed)
- **Issues**: [Report a bug](https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/issues)
---

**Star ⭐ this repository if it helped you!**
