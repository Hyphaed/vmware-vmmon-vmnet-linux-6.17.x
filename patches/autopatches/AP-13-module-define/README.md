# AP-13 — vmmon/vmnet: Module Identity Defines in `Makefile.kernel`

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## What this patch fixes

VMware's kernel module source uses preprocessor defines (`-DVMMON` and
`-DVMNET`) as module identity flags throughout the code. These defines guard
code sections that must only compile for one specific module. For example:

```c
#ifdef VMMON
/* vmmon-specific initialization */
#endif

#ifdef VMNET
/* vmnet-specific networking code */
#endif
```

In well-formed VMware source tarballs, both `Makefile.kernel` files include
these defines in their `CC_OPTS` or `ccflags-y` lines. However, some source
variants (third-party rebuilds, community overlays, or older tarballs) omit
one or both of these defines from `Makefile.kernel`.

**When the define is missing:**
- Code conditionally compiled with `#ifdef VMMON` may be silently disabled
- Wrong code paths may be activated
- Symbol conflicts between vmmon and vmnet may occur
- Build may fail with undefined references to module-specific functions

The fix adds the missing identity define as a `CC_OPTS += -DVMMON` or
`CC_OPTS += -DVMNET` line immediately after the `ccflags-y :=` assignment.

**Status of the 6.16.x community overlay:**
- `vmmon-only/Makefile.kernel`: already has `CC_OPTS += -DVMMON -DVMCORE` on
  line 21 — no fix needed
- `vmnet-only/Makefile.kernel`: does NOT have `-DVMNET` — fix applied

---

## Which kernel versions require it

**All kernel versions.** This is a build-system correctness fix, not a
kernel API compatibility fix. Applied whenever the define is absent.

---

## Which VMware source versions need it

- The community 6.16.x overlay: vmnet needs `-DVMNET` added
- VMware Workstation Pro 25H2u1: may or may not need it — script checks

---

## How the script applies it

Function: `_autopatch_module_define()` in `vmware_module_builder.py`

The function iterates over both modules:
1. Reads `Makefile.kernel` for the module
2. Checks if `-DVMMON` (or `-DVMNET`) is already present (idempotency)
3. Locates the `ccflags-y :=` anchor line
4. Inserts `CC_OPTS += -DVMMON` (or `-DVMNET`) immediately after it

---

## Manual application

For vmmon (if `-DVMMON` is missing from `vmmon-only/Makefile.kernel`):

Add after the `ccflags-y :=` line:
```makefile
# Module identity define
CC_OPTS += -DVMMON
```

For vmnet (if `-DVMNET` is missing from `vmnet-only/Makefile.kernel`):

```bash
patch -p2 < /path/to/patches/autopatches/AP-13-module-define/AP-13-module-define.patch
```

Or add after `ccflags-y :=` in `vmnet-only/Makefile.kernel`:
```makefile
# Module identity define
CC_OPTS += -DVMNET
```

---

## Attribution

**Author:** Ferran Duarri (© 2026). Original patch written for this project.

This patch was created after investigating `Makefile.kernel:38: *** missing
separator. Stop.` build failures reported by community users, which turned out
to have multiple contributing causes. One of them was missing module identity
defines (`-DVMMON`/`-DVMNET`) in some source variants. This patch ensures
both are always present regardless of the VMware source version being compiled.
