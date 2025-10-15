# Release v1.0.3 - Critical Tarball Fix

**Release Date:** October 15, 2025

This release fixes a critical bug in the tarball creation process and adds donation support.

## 🐛 Critical Bug Fix

### Fixed: Tarball Contamination (Issue #5)

**Problem:** Step 11 of the installation script was creating tarballs that included compilation artifacts instead of clean source code.

**Impact:** 
- Module rebuilding would fail after kernel upgrades
- Tarballs were 5x larger than necessary

**Solution:**
- Added `make clean` step before creating tarballs
- Added explicit removal of all build artifacts
- Tarballs now contain only clean source code

## 🧹 Repository Cleanup

### Removed Obsolete Scripts

**Removed:** `scripts/apply-patches-6.17.sh`

- This script is no longer needed as all patching functionality has been fully integrated into `install-vmware-modules.sh` since v1.0.0
- Simplifies the repository structure
- Reduces maintenance overhead
- Users only need to run one script: `install-vmware-modules.sh`

### Improved Documentation

- Enhanced testing section in README.md with comprehensive script usage
- Updated repository structure diagram
- Added detailed description of what `test-vmware-modules.sh` checks
- Clarified the all-in-one nature of the installation script

## 💖 New Features

### GitHub Sponsors Support

Added donation support to help maintain and update this project:

- Created `.github/FUNDING.yml` for GitHub Sponsors integration
- Added sponsorship section in README.md with donation badge
- Users can now support the project with cash donations via credit card
- Zero platform fees through GitHub Sponsors (Stripe/PayPal fees still apply)

**Support the project:** Cash donations are welcomed and appreciated for continued kernel compatibility maintenance!

## 📦 Installation

Same installation process as before:

```bash
git clone https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x.git
cd vmware-vmmon-vmnet-linux-6.17.x
sudo bash scripts/install-vmware-modules.sh
```

## 🔄 Upgrade Instructions

If you previously ran v1.0.2 or earlier:

1. Pull the latest changes:
   ```bash
   cd vmware-vmmon-vmnet-linux-6.17.x
   git pull origin main
   ```

2. Run the updated script:
   ```bash
   sudo bash scripts/install-vmware-modules.sh
   ```

This will create clean tarballs that work properly with future kernel upgrades!

## ✅ Compatibility

| Kernel Version | VMware Version | Status | Notes |
|---------------|----------------|--------|-------|
| 6.16.0-6.16.2 | 17.6.4         | ✅ Tested | Uses GitHub patches only |
| 6.16.3-6.16.9 | 17.6.4         | ✅ Tested | Auto-applies objtool patches |
| 6.17.0        | 17.6.4         | ✅ Tested | Additional objtool patches |
| 6.17.1-6.17.5 | 17.6.4         | ✅ Tested | Full objtool support |

## 🙏 Acknowledgments

- Thanks to the user who reported Issue #5 about tarball contamination
- Based on patches from [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x)
- VMware community for continuous support

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed changes.

---

**Support this project:** [![Sponsor](https://img.shields.io/badge/Sponsor-💖-ff69b4)](https://github.com/sponsors/Hyphaed)

