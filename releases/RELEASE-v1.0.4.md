# 🚀 VMware Modules for Linux Kernel 6.16.x/6.17.x - Release v1.0.4

**Release Date:** October 15, 2025

This release adds **Gentoo Linux support** and introduces the **foundation for hardware-specific optimizations** that will be fully realized in v1.0.5.

---

## 🎯 What's New in v1.0.4

### 🐧 Gentoo Linux Support

Full compatibility with Gentoo Linux, respecting its source-based philosophy:

**Gentoo-Specific Features:**
- Custom paths: `/opt/vmware` for VMware installation
- Kernel headers from `/usr/src/linux`
- Portage integration with `emerge` package manager
- Source-based compilation workflow
- Backup location: `/tmp/vmware-backup-*` (follows Gentoo conventions)

**Why Gentoo Matters:**
Gentoo's source-based approach naturally required implementing proper compiler flag handling and optimization options - laying the groundwork for the advanced optimization system coming in v1.0.5.

### 🔧 Initial Optimization Framework

v1.0.4 introduces the **foundation for intelligent optimizations**:

**Basic Compiler Flags:**
- `-O2` / `-O3`: Optimization levels
- `-march=native` / `-mtune=native`: CPU-specific code generation
- `-fno-strict-aliasing`: Safe aliasing for kernel modules
- `-fno-strict-overflow`: Safe overflow handling

**Hardware Detection:**
- SIMD detection: AVX-512, AVX2, SSE4.2
- Kernel feature detection: `CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS`
- Basic CPU flag parsing from `/proc/cpuinfo`

**User Choice:**
- **Optimized mode**: Uses detected CPU features for better performance
- **Vanilla mode**: Standard compilation, portable across CPUs

**Note:** This is a **basic implementation** - comprehensive hardware analysis and automatic flag generation is coming in v1.0.5.

---

## 📦 Installation

### Gentoo Users:

```bash
# Clone repository
git clone https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x.git
cd vmware-vmmon-vmnet-linux-6.17.x

# Run installation (auto-detects Gentoo)
sudo bash scripts/install-vmware-modules.sh
```

The script will automatically:
- Detect Gentoo and use `/opt/vmware` paths
- Use `emerge` for dependencies
- Work with `/usr/src/linux` kernel headers
- Offer optimization choices

### Ubuntu/Debian/Fedora Users:

Same as before - no changes to existing workflows:

```bash
sudo bash scripts/install-vmware-modules.sh
```

---

## ✅ Compatibility

**Supported Distributions:**
- Ubuntu/Debian (unchanged)
- Fedora/RHEL (unchanged)
- **Gentoo** (NEW)

**Supported Kernels:**
- 6.16.0 - 6.16.9
- 6.17.0+

**VMware Workstation:**
- 17.5.x, 17.6.x

---

## 🔜 Preview: Coming in v1.0.5

Work is underway on a **major enhancement** to the optimization system:

**Advanced Python-Based Hardware Detector:**
- Deep CPU analysis with microarchitecture detection
- Automatic compilation flag generation (CFLAGS, LDFLAGS, Make variables)
- Intel VT-x/EPT and AMD-V/NPT comprehensive detection
- NVMe PCIe bandwidth calculation
- GPU detection with VRAM analysis
- Intelligent hardware scoring (0-100) with performance predictions

**Multi-Distribution Expansion:**
- 18+ distributions (Arch, Manjaro, Rocky, AlmaLinux, openSUSE, etc.)
- Distribution family/branch detection
- Distribution-specific strategies and paths

**Mamba/Miniforge Integration:**
- State-of-the-art Python libraries (psutil, pynvml, distro)
- Automatic dependency installation
- Graceful fallback to system Python

**Safety Enhancements:**
- VMware process detection (prevents conflicts)
- Automatic comprehensive testing
- Module verification

**Why wait for v1.0.5?**  
v1.0.4 establishes the foundation with Gentoo support and basic optimization flags. v1.0.5 will build on this with a complete Python-based detection system that generates optimal compilation flags automatically.

---

## 🛠️ Utility Scripts

**Unchanged from previous versions:**

- `install-vmware-modules.sh` - Full installation (now with Gentoo support)
- `update-vmware-modules.sh` - Quick updates after kernel upgrade
- `restore-vmware-modules.sh` - Restore from backups
- `uninstall-vmware-modules.sh` - Remove modules
- `test-vmware-modules.sh` - Module testing

---

## 🐛 Bug Fixes

- Fixed kernel 6.17+ objtool validation errors
- Fixed timer API changes (timer_delete_sync)
- Fixed MSR API changes (rdmsrq_safe)
- Fixed module initialization (module_init/module_exit)
- Updated build system (EXTRA_CFLAGS → ccflags-y)

---

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete technical details.

---

## 🙏 Acknowledgments

- Based on patches from [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x)
- Gentoo support thanks to community requests
- Thanks to early testers on Ubuntu, Fedora, and Gentoo

---

## 📖 Documentation

- **README.md** - Main documentation
- **CHANGELOG.md** - Detailed version history
- **RELEASE-v1.0.4.md** - This file

---

**Questions?** Open an issue on GitHub  
**Stay tuned for v1.0.5** with advanced Python-based hardware detection!

🐧 **Gentoo users - enjoy source-based VMware compilation!**
