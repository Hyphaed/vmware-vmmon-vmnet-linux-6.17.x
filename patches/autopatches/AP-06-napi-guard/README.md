# AP-06 — vmnet: `compat_netdevice.h` NAPI Guard (No Separate Patch)

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## Status: No separate patch file

AP-06 is intentionally merged into **AP-03**. There is no standalone `.patch`
file for this entry.

---

## What AP-06 covers

AP-06 originally described a second, related issue in `compat_netdevice.h`:
even when `VMW_NETIF_SINGLE_NAPI_PARM` is set by the Makefile (via AP-05),
the guard in `compat_netdevice.h` that selects the correct
`compat_napi_complete` / `compat_napi_schedule` wrappers does NOT cover the
`compat_netif_napi_add` macro itself for kernel >= 6.1.

**The fix for this is identical to AP-03**: the version-guarded `#if
LINUX_VERSION_CODE >= KERNEL_VERSION(6, 1, 0)` block that AP-03 appends to
`compat_netdevice.h` simultaneously handles both the 4-arg → 3-arg rewrite
and the guard that AP-06 described.

In `vmware_module_builder.py`, `_autopatch_napi_add_compat()` (the AP-03
function) covers the full fix. There is no separate `_autopatch_ap06()`
function.

---

## How the script handles it

The comment in `vmware_module_builder.py` at the AP-06 section (line ~751)
reads:

```python
# (Handled in _autopatch_napi_add_compat — AP-03)
```

---

## References

- See [AP-03](../AP-03-napi-add-3arg/README.md) for the actual patch and
  full explanation
- See [AP-05](../AP-05-napi-single-parm/README.md) for the `VMW_NETIF_SINGLE_NAPI_PARM`
  detection counterpart
