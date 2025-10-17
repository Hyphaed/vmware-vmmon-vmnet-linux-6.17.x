# Release v1.0.4 - Gentoo Support, Hardware Optimizations & Utilities

**Release Date:** October 17, 2025

This major release adds Gentoo Linux support, optional hardware optimizations, and powerful utility scripts for updating and restoring VMware modules.

## 🐧 Gentoo Linux Support

**Full Gentoo compatibility** with proper path handling and workflows:

- Custom VMware paths: `/opt/vmware/lib/vmware/modules/source`
- Gentoo kernel directory detection: `/usr/src/linux-*` or `/usr/src/linux`
- Backups stored in `/tmp/vmware-backup-*` for Gentoo
- Skips tarball creation (modules installed directly to `/lib/modules`)
- Distribution auto-detected first before Fedora/Debian

**Gentoo users** can now use the same installation process as other distributions!

## ⚡ Hardware & VM Performance Optimizations (Optional)

**Conservative, user-controlled optimizations with VM performance enhancements:**

The installation script now detects your hardware and kernel features, offering comprehensive optimization options:

### Detected Information:
- CPU model and architecture
- Available CPU features (AVX2, SSE4.2, AES-NI, etc.)
- Kernel features (6.16+/6.17+ optimizations)
- Memory management capabilities
- DMA optimization support
- Current kernel compiler

### Optimization Levels:

**1) Maximum Performance (Aggressive)**
- Flags: `-O3 -ffast-math -funroll-loops -march=native -mtune=native`
- VM Optimizations: Memory allocation, DMA, Low latency mode
- Highest performance optimizations
- Includes memory allocation & DMA optimizations
- Low latency mode (better for graphics/Wayland)
- **Best for:** Desktop VMs, graphics workloads, Wayland compositing
- ⚠️ Modules will only work on similar CPUs

**2) Native (Recommended for this CPU)**
- Flags: `-O2 -pipe -march=native -mtune=native`
- VM Optimizations: Memory allocation, kernel features
- Balanced performance and safety
- Optimized for your CPU + kernel features
- Memory allocation optimizations included
- **Best choice for most users**
- ⚠️ Modules will only work on similar CPUs

**3) Conservative (Safe, portable)**
- Flags: `-O2 -pipe`
- VM Optimizations: Kernel features only
- Standard optimization + kernel features
- Works on any x86_64 CPU
- Good performance, maximum portability

**4) None (Default kernel flags)**
- Uses same flags as your kernel
- Safest option (Default)

The script will ask you to choose before compilation. **Default is option 4 (no optimizations)** for maximum safety.

### VM Performance Features:
- **Memory Management Optimizations:** Better buffer allocation (benefits graphics rendering)
- **DMA Optimizations:** Improved graphics buffer sharing between host and guest
- **Low Latency Mode:** Reduced operation latency for better responsiveness
- **Modern Kernel Features:** Efficient unaligned memory access, modern MM for 6.16+/6.17+
- **Frame Pointer Optimization:** Performance gain when kernel supports it

These optimizations improve VM performance at the kernel level, which indirectly benefits Wayland compositors and graphics-intensive applications.

## 🔧 New Utility Scripts

### 1. Update Utility (`update-vmware-modules.sh`)

Quick module updates after kernel upgrades:

```bash
sudo bash scripts/update-vmware-modules.sh
```

**Features:**
- Detects current kernel version
- Checks if modules need updating  
- Compares module version vs kernel version
- Automatically runs full installation for new kernel
- Shows before/after module status

**When to use:** After upgrading your Linux kernel

---

### 2. Restore Utility (`restore-vmware-modules.sh`)

Restore VMware modules from automatic backups:

```bash
sudo bash scripts/restore-vmware-modules.sh
```

**Features:**
- Lists all available backups with timestamps
- Shows file sizes and modification dates
- Interactive backup selection (numbered list)
- Shows current state vs backup state
- Safe restore with confirmation prompts
- Verifies backup integrity before restore
- Works with both standard and Gentoo paths

**When to use:** If something goes wrong during installation/update

Backups are created automatically during:
- Initial installation
- Updates

## 🔔 Important Information Banners

Both `install-vmware-modules.sh` and `update-vmware-modules.sh` now show an information banner at startup:

- Informs users that backups will be created
- Shows how to restore using `restore-vmware-modules.sh`
- Increases awareness of safety features

## 📦 Installation

Same installation process, now with more options:

```bash
git clone https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x.git
cd vmware-vmmon-vmnet-linux-6.17.x
sudo bash scripts/install-vmware-modules.sh
```

**New prompts you'll see:**
1. Kernel version selection (6.16 or 6.17)
2. **Hardware optimization level** (Native/Conservative/None)

## 🔄 Update After Kernel Upgrade

```bash
cd vmware-vmmon-vmnet-linux-6.17.x
git pull origin main
sudo bash scripts/update-vmware-modules.sh
```

## 🔙 Restore from Backup

```bash
sudo bash scripts/restore-vmware-modules.sh
```

## ✅ Compatibility

| Distribution | Status | Notes |
|-------------|--------|-------|
| Ubuntu/Debian | ✅ Tested | Full support |
| Fedora/RHEL | ✅ Tested | Full support |
| **Gentoo** | ✅ Tested | **NEW:** Full support with custom paths |

| Kernel Version | VMware Version | Status | Notes |
|---------------|----------------|--------|-------|
| 6.16.0-6.16.2 | 17.6.4         | ✅ Tested | Uses GitHub patches only |
| 6.16.3-6.16.9 | 17.6.4         | ✅ Tested | Auto-applies objtool patches |
| 6.17.0        | 17.6.4         | ✅ Tested | Additional objtool patches |
| 6.17.1+       | 17.6.4         | ✅ Tested | Full objtool support |

## 🙏 Acknowledgments

- Gentoo support based on user patch submission (Issue #6)
- Thanks to the community for testing and feedback
- Based on patches from [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x)
- VMware community for continuous support

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed changes.

---

**Support this project:** [![Sponsor](https://img.shields.io/badge/Sponsor-💖-ff69b4)](https://github.com/sponsors/Hyphaed)

\* Awaiting for Github Sponsors check

