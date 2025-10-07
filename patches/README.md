# Patches for Kernel 6.17.x

This directory documents the patches needed to make VMware Workstation modules compatible with Linux kernel 6.17.x.

## Patch Files (For Research/Manual Patching)

This directory contains `.patch` files as reference for researchers or those who want to manually apply patches:

- **vmmon-6.17-makefile.patch** - Adds objtool bypass to vmmon Makefile.kernel
- **vmmon-6.17-phystrack.patch** - Removes unnecessary return statements from phystrack.c
- **vmnet-6.17-makefile.patch** - Adds objtool bypass to vmnet Makefile.kernel

**Note:** These `.patch` files are provided for reference and research purposes. The recommended method is to use the automated script (see below), which handles all patches comprehensively.

### Manual Patching (Alternative Method)

If you prefer to apply patches manually:

```bash
cd vmmon-only
patch -p1 < /path/to/patches/vmmon-6.17-makefile.patch
patch -p1 < /path/to/patches/vmmon-6.17-phystrack.patch

cd ../vmnet-only
patch -p1 < /path/to/patches/vmnet-6.17-makefile.patch
```

## Recommended: Automated Patching

The patches for kernel 6.17.x are best applied automatically using the script:
```bash
../scripts/apply-patches-6.17.sh /path/to/vmmon-only /path/to/vmnet-only
```

This script applies the following modifications:

## vmmon Module Patches

### 1. Makefile.kernel - Disable objtool validation

The script replaces the entire `Makefile.kernel` file to add objtool bypass flags:

```makefile
# Deshabilitar objtool para archivos problemáticos en kernel 6.17+
OBJECT_FILES_NON_STANDARD_common/phystrack.o := y
OBJECT_FILES_NON_STANDARD_common/task.o := y
OBJECT_FILES_NON_STANDARD := y
```

**Why:** Kernel 6.17.x has stricter objtool validation that VMware's proprietary code doesn't pass.

### 2. common/phystrack.c - Remove unnecessary return statements

Removes `return;` statements at lines 324 and 368 in void functions.

**Before:**
```c
void PhysTrack_Test(void) {
    // ... code ...
    return;  // Line 324 - Unnecessary
}

void PhysTrack_Cleanup(void) {
    // ... code ...
    return;  // Line 368 - Unnecessary
}
```

**After:**
```c
void PhysTrack_Test(void) {
    // ... code ...
    // Implicit return
}

void PhysTrack_Cleanup(void) {
    // ... code ...
    // Implicit return
}
```

**Why:** Kernel 6.17's objtool flags unnecessary explicit returns in void functions.

### 3. common/task.c - Remove unnecessary return statements (if present)

Removes any `return;` statements in void functions if they exist.

**Why:** Same as phystrack.c - objtool validation.

## vmnet Module Patches

### 1. Makefile.kernel - Disable objtool validation

Adds objtool bypass flags to the existing Makefile.kernel:

```makefile
# Deshabilitar objtool para archivos problemáticos en kernel 6.17+
OBJECT_FILES_NON_STANDARD_userif.o := y
OBJECT_FILES_NON_STANDARD := y
```

**Why:** Same reason as vmmon - objtool validation bypass.

## Complete Workflow

The recommended installation workflow is:

1. **Extract VMware modules:**
```bash
tar -xf /usr/lib/vmware/modules/source/vmmon.tar
tar -xf /usr/lib/vmware/modules/source/vmnet.tar
```

2. **Apply base patches (6.16.x):**
```bash
# Clone the 6.16.x repository
git clone https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x.git

# Copy patched files from 6.16.x repo
cp vmware-vmmon-vmnet-linux-6.16.x/modules/17.6.4/source/vmmon-only/* vmmon-only/
cp vmware-vmmon-vmnet-linux-6.16.x/modules/17.6.4/source/vmnet-only/* vmnet-only/
```

3. **Apply 6.17.x specific patches:**
```bash
bash scripts/apply-patches-6.17.sh vmmon-only vmnet-only
```

4. **Compile:**
```bash
cd vmmon-only && make && sudo make install
cd ../vmnet-only && make && sudo make install
```

## Automated Installation

For automated installation, use the main installation script:
```bash
sudo bash scripts/install-vmware-modules.sh
```

This script handles all steps automatically:
- Checks prerequisites
- Downloads base patches (6.16.x)
- Applies 6.17.x specific patches
- Compiles and installs modules
- Loads modules and starts VMware services

## Technical Details

### Why These Patches Are Needed

Kernel 6.17.x introduced several changes that break VMware module compilation:

1. **Stricter objtool validation**: The kernel's objtool now performs more thorough validation of object files, catching issues that were previously ignored.

2. **Stack frame validation**: Enhanced checks for proper stack frame setup and teardown.

3. **Return statement validation**: Objtool now flags unnecessary explicit `return;` statements in void functions as potential control flow issues.

### What objtool Does

Objtool is a kernel build-time tool that validates:
- Stack frame correctness
- Control flow integrity
- Proper function entry/exit sequences
- Unannotated indirect jumps

VMware's proprietary code contains patterns that objtool flags as suspicious, even though they work correctly. Rather than modify the proprietary code (which we can't), we disable objtool validation for specific problematic files.

### Why This Is Safe

Disabling objtool for these files is safe because:
1. VMware's code has been tested extensively by Broadcom
2. The code works correctly despite objtool warnings
3. We only disable objtool, not actual compilation checks
4. The modules still undergo all other kernel validation

## Compatibility

These patches are specifically for:
- **Kernel:** 6.17.x series (tested on 6.17.0-5-generic)
- **VMware:** 17.6.4 (may work with other 17.x versions)
- **Based on:** 6.16.x patches from [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x)

For other kernel versions:
- **6.16.x:** https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x
- **6.18.x:** Check this repository for updates

## License

These patches are provided under GPL v2, matching the Linux kernel license.

## Contributing

Found an issue or improvement? Please submit a pull request or open an issue on GitHub.

## References

- [Linux kernel objtool documentation](https://www.kernel.org/doc/html/latest/dev-tools/objtool.html)
- [VMware Workstation for Linux](https://www.vmware.com/products/workstation-for-linux.html)
- [Base 6.16.x patches](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x)