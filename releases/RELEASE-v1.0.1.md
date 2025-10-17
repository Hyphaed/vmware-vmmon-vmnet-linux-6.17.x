# Release v1.0.1 - Fix Module Extraction Error Handling

**Release Date:** October 11, 2025

## 🐛 Bug Fixes

### Fixed Module Extraction Error (Issue #4)

Users were encountering cryptic "Error extracting modules" messages when the VMware tar files were missing, corrupted, or inaccessible. This release adds comprehensive error handling and diagnostic information.

**What's Fixed:**
- ✅ Added explicit check for existence of `vmmon.tar` and `vmnet.tar` before extraction
- ✅ Added proper error handling for tar extraction failures
- ✅ Improved error messages to guide users when tar files are missing or corrupted
- ✅ Added detailed working directory listing on extraction failure for debugging
- ✅ Script now exits gracefully with clear, actionable error messages
- ✅ Added comprehensive troubleshooting entry in `TROUBLESHOOTING.md`

**Example of improved error messages:**
```
[✗] vmmon.tar not found at /usr/lib/vmware/modules/source/vmmon.tar
[✗] Please verify VMware Workstation is properly installed
```

## 📝 Changes in This Release

### Modified Files:
- `scripts/install-vmware-modules.sh` - Enhanced tar extraction with proper error handling
- `docs/TROUBLESHOOTING.md` - Added "Error extracting modules" troubleshooting section
- `CHANGELOG.md` - Updated with version 1.0.1 release notes

## 🔧 Installation

```bash
git clone https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x.git
cd vmware-vmmon-vmnet-linux-6.17.x
sudo bash scripts/install-vmware-modules.sh
```

## 📋 Compatibility

- **Kernel Support:** 6.16.x and 6.17.x series
- **VMware Version:** 17.6.4 (and compatible versions)
- **Distributions:** Ubuntu/Debian, Fedora/RHEL, Arch Linux
- **Tested On:** Ubuntu 25.10 with kernel 6.17.0-5-generic

## 🙏 Credits

Thanks to the user who reported Issue #4 for helping us improve error handling and user experience!

## 📜 Full Changelog

See [CHANGELOG.md](https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/blob/main/CHANGELOG.md) for complete details.

---

**Installation Issues?** Check our [Troubleshooting Guide](https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/blob/main/docs/TROUBLESHOOTING.md)

