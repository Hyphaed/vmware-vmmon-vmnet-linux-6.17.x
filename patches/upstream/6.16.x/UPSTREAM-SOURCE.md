# Upstream Source: VMware Kernel 6.16.x Patches

## Original Repository

**Source**: [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x)  
**Forked from**: [64kramsystem/vmware-host-modules-fork](https://github.com/64kramsystem/vmware-host-modules-fork)  
**License**: GPL-2.0  
**Copied on**: 2025-10-17  
**Purpose**: Local backup to ensure script continues working if upstream repository becomes unavailable

## What's Included

This directory contains a **complete local copy** of the patched VMware kernel modules for Linux 6.16.x:

### Directory Structure
```
patches/upstream/6.16.x/
├── vmmon-only/           # VMware Virtual Machine Monitor module
│   ├── Makefile          # Build system (EXTRA_CFLAGS → ccflags-y)
│   ├── Makefile.kernel   # Kernel build integration
│   ├── linux/
│   │   ├── driver.c      # Timer API fixes (del_timer_sync → timer_delete_sync)
│   │   └── hostif.c      # MSR API fixes (rdmsrl_safe → rdmsrq_safe)
│   ├── common/           # Common VMware code
│   └── bootstrap/        # Module initialization
│
└── vmnet-only/           # VMware Virtual Networking Driver module
    ├── Makefile          # Build system
    ├── Makefile.kernel   # Kernel build integration
    ├── driver.c          # Module init fixes (init_module → module_init)
    ├── smac_compat.c     # Function prototype fixes
    └── *.c/h             # Network driver implementation
```

## Kernel 6.16.x Compatibility Fixes Applied

| Issue                   | Old Code                  | New Code              | File(s)                    |
| ----------------------- | ------------------------- | --------------------- | -------------------------- |
| **Build System**        | EXTRA_CFLAGS              | ccflags-y             | */Makefile.kernel          |
| **Timer API**           | del_timer_sync()          | timer_delete_sync()   | vmmon/linux/driver.c       |
| **MSR API**             | rdmsrl_safe()             | rdmsrq_safe()         | vmmon/linux/hostif.c       |
| **Module Init**         | init_module()             | module_init()         | vmnet/driver.c             |
| **Function Prototypes** | function()                | function(void)        | vmnet/smac_compat.c        |
| **Module Exit**         | cleanup_module()          | module_exit()         | vmnet/driver.c             |

## Why Local Copy?

### Benefits of Local Patches:
1. **Offline compilation** - No internet required to build modules
2. **Stability** - Protected from upstream repository changes/deletion
3. **Faster builds** - No git clone needed, instant access
4. **Version control** - Patches tracked in this repository
5. **Customization** - Can apply local modifications without affecting upstream

### Fallback Strategy:
Our installation script (`install-vmware-modules.sh`) uses this hierarchy:

```bash
Priority 1: Local patches (patches/upstream/6.16.x/)
Priority 2: GitHub clone (if local unavailable)
Priority 3: Error with helpful message
```

## Usage in Installation Script

The script automatically uses local patches:

```bash
# Check for local patches first
if [ -d "$SCRIPT_DIR/patches/upstream/6.16.x" ]; then
    info "Using local 6.16.x patches"
    PATCH_SOURCE="$SCRIPT_DIR/patches/upstream/6.16.x"
else
    # Fallback to GitHub clone
    info "Downloading patches from GitHub..."
    git clone https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x.git
    PATCH_SOURCE="vmware-vmmon-vmnet-linux-6.16.x/modules/17.6.4/source"
fi
```

## Credits and Attribution

- **Original patches**: ngodn (GitHub)
- **Community effort**: 64kramsystem and contributors
- **Kernel 6.17.x enhancements**: Hyphaed (this repository)
- **License**: GPL-2.0 (maintained from upstream)

## Update Policy

These patches are specific to **kernel 6.16.x**. For kernel 6.17.x:
- We apply **6.16.x patches as base**
- Then apply **additional 6.17.x-specific fixes** (objtool, etc.)
- Plus **our performance optimizations** (hardware detection, compiler flags)

This ensures maximum compatibility and performance across kernel versions.

## Verification

To verify patch integrity:

```bash
# Check files are present
ls -R patches/upstream/6.16.x/

# Compare with upstream (optional)
git clone https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x.git /tmp/verify
diff -r patches/upstream/6.16.x/ /tmp/verify/modules/17.6.4/source/
```

## Maintenance

- **When to update**: If upstream repository adds critical security fixes
- **How to update**: Re-run copy command from upstream repository
- **Testing**: Always test with current kernel before committing updates

---

**Last Updated**: 2025-10-17  
**Upstream Commit**: Latest from master branch  
**Status**: ✅ Verified working on Ubuntu 25.10 + Kernel 6.17.0-5-generic

