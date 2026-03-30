# AP-01b — vmnet: Objtool Bypass (kernel >= 6.17 / 7.x)

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## What this patch fixes

Linux kernel 6.17 introduced stricter objtool validation. vmnet's `userif.c`
contains assembly or control flow patterns that objtool flags as invalid in
kernel 6.17+, causing build failures like:

```
userif.o: error: objtool: VNetUserIfSetupNotify()+0x...: unreachable instruction
```

The fix adds `OBJECT_FILES_NON_STANDARD` directives to `vmnet/Makefile.kernel`,
telling the kernel build to skip objtool for `userif.o` specifically. All
other compilation checks remain active.

---

## Which kernel versions require it

Kernel **>= 6.17** and kernel **>= 7.x**.

Kernels < 6.17 do not need this patch.

---

## Which VMware source versions need it

Both:
- VMware Workstation 17.6.x (pre-25H2u1)
- VMware Workstation Pro **25H2u1**

This is a kernel-side change, not a VMware source change.

---

## How the script applies it

Function: `_autopatch_objtool_vmnet()` in `vmware_module_builder.py`

The function:
1. Reads `vmnet-only/Makefile.kernel`
2. Locates the anchor at the end of the `$(DRIVER)-y` flat object list
3. Inserts the two `OBJECT_FILES_NON_STANDARD` lines immediately after it
4. Is idempotent — checks for the marker before inserting

---

## Manual application

From inside the extracted `vmnet-only/` directory:

```bash
patch -p2 < /path/to/patches/autopatches/AP-01-objtool-vmnet/AP-01-objtool-vmnet.patch
```

Or manually add after the `$(DRIVER)-y := ...` block in `vmnet-only/Makefile.kernel`:

```makefile
# Disable objtool for files using non-standard asm (kernel 6.17+)
OBJECT_FILES_NON_STANDARD_userif.o := y
OBJECT_FILES_NON_STANDARD := y
```

---

## Attribution

**Author:** Ferran Duarri (© 2026).

This patch was written to address build failures on kernel 6.17+ reported by
community users. It is an original fix for this project, targeting the vmnet
`userif.o` (the vmmon counterpart AP-01a targets `phystrack.o` and `task.o`).
Re-implemented as an idempotent in-memory autopatch working against any VMware
source version.

The underlying community work that made the 6.16.x base source available is
credited to **[ngodn](https://github.com/ngodn)** and
**[64kramsystem](https://github.com/64kramsystem)** — their patches are in
`patches/upstream/6.16.x/`.

---

## References

- See also: [AP-01a](../AP-01-objtool-vmmon/README.md) for the vmmon equivalent
- Upstream 6.16.x community patches: [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x)
- Linux objtool documentation: https://www.kernel.org/doc/html/latest/dev-tools/objtool.html
