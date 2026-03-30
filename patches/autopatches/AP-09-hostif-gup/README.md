# AP-09 — vmmon: `get_user_pages_fast` API Check (No Change Needed)

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## Status: No-op — documented for completeness

AP-09 has no `.patch` file because no source change is required.

---

## What was investigated

`vmmon-only/linux/hostif.c` calls `get_user_pages_fast()` to pin guest
physical pages for DMA. Linux 5.9 changed the signature of this function:
the third argument changed from `int write` to `unsigned int gup_flags`.

The concern was that VMware's call might pass an incompatible value.
However, after analysis:

- VMware's call passes `0` as the third argument (read-only mapping)
- `0` is valid for both the old `int write` (0 = read-only) and the new
  `unsigned int gup_flags` (0 = no flags, also read-only)
- `get_user_pages_fast` is still exported in kernel 7.x with the same
  `unsigned int gup_flags` prototype — no further change occurred

The function call is binary-compatible across all affected kernel versions.
No source modification is needed.

---

## How the script handles it

Function: `_autopatch_hostif_gup()` in `vmware_module_builder.py`

The function simply logs an informational message:

```
hostif.c: get_user_pages_fast — API compatible, no fix needed
```

It is called in `apply_all_patches()` as part of the always-applied
structural checks, but it makes no file modifications.

---

## References

- See also: [AP-11](../AP-11-userif-gup/README.md) — same analysis for
  `vmnet/userif.c`
- Linux 5.9 `get_user_pages_fast` change: https://git.kernel.org/linus/
