# AP-01a — vmmon: Objtool Bypass (kernel >= 6.17 / 7.x)

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## What this patch fixes

Linux kernel 6.17 introduced stricter objtool validation. Objtool is a
compile-time tool that validates stack frame correctness, control flow
integrity, and proper function entry/exit sequences in all compiled
object files.

VMware's `vmmon` module contains two files with assembly constructs that
objtool flags as invalid, even though they work correctly at runtime:

- `common/phystrack.c` — uses non-standard stack frame patterns
- `common/task.c` — uses VMware-internal control flow constructs

Without this patch, the kernel build system aborts with objtool errors like:

```
phystrack.o: error: objtool: PhysTrack_Test()+0x...: unreachable instruction
task.o: error: objtool: ...
```

The fix adds `OBJECT_FILES_NON_STANDARD` directives to `vmmon/Makefile.kernel`,
instructing the kernel build to skip objtool validation for these two specific
files. All other compilation checks remain in effect.

This is the standard, documented approach for out-of-tree modules that contain
legitimate but non-standard assembly patterns. See:
https://www.kernel.org/doc/html/latest/dev-tools/objtool.html

---

## Which kernel versions require it

Kernel **>= 6.17** and kernel **>= 7.x** (any 7.x release).

Kernels < 6.17 do not need this patch.

---

## Which VMware source versions need it

Both:
- VMware Workstation 17.6.x (pre-25H2u1) sources
- VMware Workstation Pro **25H2u1** sources

The objtool issue is a kernel-side change, not a VMware source change, so
it affects all VMware source versions on kernel >= 6.17.

---

## How the script applies it

Function: `_autopatch_objtool_vmmon()` in `vmware_module_builder.py`

The function:
1. Reads `vmmon-only/Makefile.kernel`
2. Locates the anchor line ending the `$(DRIVER)-y` object list
3. Inserts the three `OBJECT_FILES_NON_STANDARD` lines immediately after it
4. Is idempotent — checks for the marker before inserting

---

## Manual application

From inside the extracted `vmmon-only/` directory:

```bash
patch -p2 < /path/to/patches/autopatches/AP-01-objtool-vmmon/AP-01-objtool-vmmon.patch
```

Or apply the diff manually by adding these lines after the `$(DRIVER)-y := ...`
block in `vmmon-only/Makefile.kernel`:

```makefile
# Disable objtool for files using non-standard asm (kernel 6.17+)
OBJECT_FILES_NON_STANDARD_common/phystrack.o := y
OBJECT_FILES_NON_STANDARD_common/task.o := y
OBJECT_FILES_NON_STANDARD := y
```

---

## Attribution

**Author:** Ferran Duarri (© 2026).

This patch was written to address build failures on kernel 6.17+ reported by
community users. It is an original fix for this project, re-implemented as an
idempotent in-memory autopatch that works against any VMware source version
(17.6.x or 25H2u1) without requiring fixed line numbers.

The underlying community work that made the 6.16.x base source available is
credited to **[ngodn](https://github.com/ngodn)** and
**[64kramsystem](https://github.com/64kramsystem)** — their patches are in
`patches/upstream/6.16.x/` and are a prerequisite base layer for older VMware
installs.

---

## References

- See also: [AP-01b](../AP-01-objtool-vmnet/README.md) for the vmnet equivalent
- See also: [AP-02](../AP-02-phystrack-bare-returns/README.md) for the companion
  bare `return;` removal in `phystrack.c`
- Upstream 6.16.x community patches: [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x)
- Linux objtool documentation: https://www.kernel.org/doc/html/latest/dev-tools/objtool.html
