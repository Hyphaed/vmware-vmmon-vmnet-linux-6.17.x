# Patches for Kernel 6.17.x

This directory contains the patch files needed to make VMware Workstation modules compatible with Linux kernel 6.17.x.

## Patch Files

### vmmon-6.17.patch
Patches for the `vmmon` (Virtual Machine Monitor) module.

**Changes:**
- Modifies `Makefile.kernel` to disable objtool validation
- Removes unnecessary return statements in `common/phystrack.c`
- Fixes void function returns in `common/task.c`

### vmnet-6.17.patch
Patches for the `vmnet` (Virtual Network) module.

**Changes:**
- Modifies `Makefile.kernel` to disable objtool validation for problematic files

## How to Apply Patches

### Automated (Recommended)

Use the provided script:
```bash
bash ../scripts/apply-patches-6.17.sh /path/to/vmmon-only /path/to/vmnet-only
```

### Manual Application

1. Extract VMware modules:
```bash
tar -xf /usr/lib/vmware/modules/source/vmmon.tar
tar -xf /usr/lib/vmware/modules/source/vmnet.tar
```

2. Apply patches:
```bash
cd vmmon-only
patch -p1 < /path/to/vmmon-6.17.patch

cd ../vmnet-only
patch -p1 < /path/to/vmnet-6.17.patch
```

3. Compile:
```bash
cd vmmon-only
make
sudo make install

cd ../vmnet-only
make
sudo make install
```

## Patch Details

### Objtool Bypass

The main change in these patches is adding objtool bypass flags to the Makefile:

```makefile
OBJECT_FILES_NON_STANDARD_common/phystrack.o := y
OBJECT_FILES_NON_STANDARD_common/task.o := y
OBJECT_FILES_NON_STANDARD := y
```

This is necessary because kernel 6.17.x has stricter objtool validation that VMware's proprietary code doesn't pass.

### Return Statement Fixes

Kernel 6.17's objtool also flags unnecessary `return;` statements in void functions:

**Before:**
```c
void SomeFunction(void) {
    // code
    return;  // Unnecessary
}
```

**After:**
```c
void SomeFunction(void) {
    // code
    // Implicit return
}
```

## Creating Patches

If you need to regenerate these patches:

1. Extract clean VMware modules
2. Make a copy for comparison
3. Apply changes
4. Generate diff:

```bash
diff -Naur vmmon-only.orig vmmon-only > vmmon-6.17.patch
diff -Naur vmnet-only.orig vmnet-only > vmnet-6.17.patch
```

## Compatibility

These patches are specifically for:
- **Kernel:** 6.17.x series
- **VMware:** 17.6.4 (may work with other 17.x versions)

For other kernel versions, see:
- 6.16.x: https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x
- 6.18.x: Coming soon (check this repository)

## License

These patches are provided under GPL v2, matching the Linux kernel license.

## Contributing

Found an issue or improvement? Please submit a pull request or open an issue on GitHub.
