# AP-02 — vmmon: Remove Bare `return;` in Void Functions (kernel >= 6.17 / 7.x)

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## What this patch fixes

Linux kernel 6.17 tightened objtool's control flow analysis. One of the new
checks flags explicit `return;` statements at the very end of void functions
as "dead code after RET" — because the compiler already emits a `ret`
instruction from the final statement, making a trailing `return;` compile into
an unreachable `ret`.

In VMware's pre-6.16.x `phystrack.c`, two void functions (`PhysTrack_Test`
and `PhysTrack_Cleanup`) end with an explicit bare `return;` before their
closing `}`. On kernel 6.17+ this causes:

```
phystrack.o: error: objtool: PhysTrack_Test()+0x...: unreachable instruction
phystrack.o: error: objtool: PhysTrack_Cleanup()+0x...: unreachable instruction
```

The fix simply removes those redundant `return;` lines. The generated machine
code is identical — only the objtool analysis result changes.

Note: The community 6.16.x overlay (`patches/upstream/6.16.x/vmmon-only/`)
may or may not contain these lines depending on the VMware source version.
The script applies this patch using a regex that scans all void functions and
is fully idempotent.

---

## Which kernel versions require it

Kernel **>= 6.17** and kernel **>= 7.x**.

Kernels < 6.17 accept bare `return;` in void functions without error.

---

## Which VMware source versions need it

Older VMware sources (17.6.x, pre-25H2u1) that still have the bare `return;`
lines. VMware Workstation Pro 25H2u1 may ship sources without them — the
script checks before applying.

---

## How the script applies it

Function: `_autopatch_phystrack_bare_returns()` in `vmware_module_builder.py`

The function:
1. Reads `vmmon-only/common/phystrack.c`
2. Applies regex `\s+return;\n(\s*\})` to find bare returns before closing braces
3. Removes the matched `return;` lines in reverse order (to preserve offsets)
4. Is idempotent — if no bare returns are found, exits cleanly

---

## Manual application

The exact line numbers depend on your VMware source version. Use the script
for reliable application, or locate the affected void functions manually and
remove the bare `return;` line before their closing `}`.

For reference, the affected pattern looks like:

```c
void SomeFunctionName(void) {
    // ... function body ...
    return;  /* <-- remove this line */
}
```

To apply to a specific phystrack.c where the lines match exactly:

```bash
patch -p2 < /path/to/patches/autopatches/AP-02-phystrack-bare-returns/AP-02-phystrack-bare-returns.patch
```

---

## Attribution

**Author:** Ferran Duarri (© 2026).

This patch was written to address build failures on kernel 6.17+ reported by
community users. In this project it is generalized to a regex scan over all
void functions, making it robust against line number differences between VMware
source versions (17.6.x vs 25H2u1).

---

## References

- See also: [AP-01a](../AP-01-objtool-vmmon/README.md) — the companion objtool
  bypass in `Makefile.kernel` (AP-01 and AP-02 are both required for kernel >= 6.17)
- Upstream 6.16.x community patches: [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x)
- Linux objtool documentation: https://www.kernel.org/doc/html/latest/dev-tools/objtool.html
