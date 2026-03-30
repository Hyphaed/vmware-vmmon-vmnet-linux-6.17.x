# AP-11 — vmnet: `userif.c` `get_user_pages_fast` Check (No Change Needed)

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## Status: No-op — documented for completeness

AP-11 has no `.patch` file because no source change is required.

---

## What was investigated

`vmnet-only/userif.c` calls `get_user_pages_fast(addr, 1, FOLL_WRITE, &page)`
to pin a user-space page for network I/O. The call uses `FOLL_WRITE` as the
`gup_flags` argument.

`FOLL_WRITE` was introduced in Linux 4.9 as the replacement for the old
`int write` parameter (where `1` meant write access). VMware's call correctly
uses the `FOLL_WRITE` flag form, which is the right API for kernel >= 4.9.

This call is compatible with all kernel versions this tool supports
(>= 6.16), where `get_user_pages_fast(addr, nr, gup_flags, pages)` is
the standard prototype.

---

## How the script handles it

Function: `_autopatch_userif_gup()` in `vmware_module_builder.py`

The function simply logs an informational message:

```
userif.c: get_user_pages_fast(FOLL_WRITE) — API compatible, no fix needed
```

No file modifications are made.

---

## References

- See also: [AP-09](../AP-09-hostif-gup/README.md) — same analysis for
  `vmmon/linux/hostif.c`
