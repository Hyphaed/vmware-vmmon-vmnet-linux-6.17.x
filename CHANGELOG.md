# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.3] - 2025-10-15

### Fixed: Tarball Contamination

**Problem:** Step 11 of the installation script was creating tarballs that included compilation artifacts instead of clean source code.

**Impact:**
- Tarballs were 5x larger than necessary

**Solution:**
- Added `make clean` step before creating tarballs
- Added explicit removal of all build artifacts
- Tarballs now contain only clean source code

### Removed
- Removed obsolete `apply-patches-6.17.sh` script
  - Functionality fully integrated into `install-vmware-modules.sh` since v1.0.0
  - All patching is now handled by the main installation script
  - Simplifies repository structure and reduces maintenance overhead

### Added
- Added GitHub Sponsors donation support
  - Created `.github/FUNDING.yml` for GitHub Sponsors integration
  - Added sponsorship section to README.md with donation badge
  - Cash donations are welcomed and appreciated for continued maintenance

### Improved
- Enhanced `test-vmware-modules.sh` documentation in README.md
  - Added comprehensive testing section with script usage
  - Documented all checks performed by the test utility
  - Clarified distinction between quick manual tests and comprehensive script-based tests

## [1.0.2] - 2025-10-11

### Improved
- Enhanced error messages in `install-vmware-modules.sh` for module extraction failures
  - Added detailed warning about broken modules from previous patching attempts
  - Added clear explanation that other internet scripts may have corrupted VMware files
  - Added step-by-step reinstallation instructions directly in error output
  - Users now see immediate guidance when tar extraction fails
  - Emphasizes that manual modifications or previous patches are common causes

## [1.0.1] - 2025-10-11

### Fixed
- Fixed module extraction error handling in `install-vmware-modules.sh` (Issue #4)
  - Added explicit check for existence of vmmon.tar and vmnet.tar before extraction
  - Added proper error handling for tar extraction failures
  - Improved error messages to guide users when tar files are missing or corrupted
  - Added detailed working directory listing on extraction failure for debugging
  - Script now exits gracefully with clear error messages instead of cryptic "Error extracting modules"
  - Added comprehensive troubleshooting entry in TROUBLESHOOTING.md for extraction errors

- Fixed hardcoded log file path in `install-vmware-modules.sh` (Issue #2)
  - Changed from hardcoded `/home/ferran/Documents/Scripts` to dynamic path detection
  - Script now automatically detects its location using `$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)`
  - Log files are now saved in the `scripts/` directory where the script resides
  - Script can now be run from any directory without modification
  - Updated `test-vmware-modules.sh` to use relative path instead of hardcoded path

- Fixed vmmon.ko compilation failure on kernel 6.16.3+ (Issue #3)
  - Added intelligent objtool patch detection
  - Script now automatically detects if kernel version requires objtool patches
  - Kernel 6.16.3+ automatically gets objtool patches even when selecting "6.16" option
  - Fixes objtool errors: "PhysTrack_Add() falls through to next function"
  - Fixes objtool errors: "Task_Switch(): unexpected end of section"

### Added
- Automatic objtool patch detection for kernel 6.16.3 and higher
  - Script checks kernel patch version and applies objtool fixes automatically
  - Works for both user selection "6.16" and "6.17"
  - Displays clear warning when objtool patches are auto-applied
- Enhanced summary output showing objtool patch status (auto-detected vs manual)

### Changed
- Updated README.md with multiple installation options (from scripts directory, from root, or from anywhere)
- Added note about automatic log file location detection
- Updated README.md to document automatic objtool detection feature
- Updated compatibility matrix to reflect kernel 6.16.3+ objtool requirements
- Renumbered installation steps (now 14 steps instead of 13) to include objtool detection phase

## [1.0.0] - 2025-10-09

### Added
- Initial release with support for Linux kernel 6.16.x and 6.17.x
- Interactive kernel version selection during installation
- Automated installation script (`install-vmware-modules.sh`)
- Patch application script (`apply-patches-6.17.sh`)
- Module testing script (`test-vmware-modules.sh`)
- Comprehensive documentation:
  - README.md with installation instructions
  - TECHNICAL.md with technical details
  - TROUBLESHOOTING.md with common issues and solutions
- Support for Ubuntu/Debian and Fedora/RHEL distributions
- Automatic compiler detection (GCC/Clang)
- Objtool patches for kernel 6.17.x
- Module backup functionality

### Features
- Dual kernel support (6.16.x and 6.17.x)
- Interactive installation with kernel version selection
- Smart patching based on kernel version
- Multi-distribution support
- Automatic service restart
- Comprehensive error handling and logging

---

## Issue References

- #2 - Hardcoded log file path preventing automatic method to succeed
- #3 - vmmon.ko was not generated (objtool errors on kernel 6.16.3+)
- #4 - Error extracting modules (missing error handling for tar extraction)
- #5 - Tarballs contain compilation artifacts causing module rebuild issues

