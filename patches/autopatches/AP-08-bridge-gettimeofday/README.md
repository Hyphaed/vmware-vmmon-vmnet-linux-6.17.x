# AP-08 — vmnet: `do_gettimeofday` → `ktime_get_real_ts64` in `bridge.c` (kernel >= 5.0)

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## What this patch fixes

`do_gettimeofday()` was removed from the Linux kernel in version 5.0. It was
replaced by `ktime_get_real_ts64()` which uses `struct timespec64` instead of
the deprecated `struct timeval`.

`vmnet-only/bridge.c` uses `do_gettimeofday()` in three places for debug
timestamp logging:

1. A static `struct timeval vnetTime` variable (line ~74)
2. A `do_gettimeofday(&vnetTime)` call inside `VNetBridgeReceiveFromVNet()`
3. A local `struct timeval now` + `do_gettimeofday(&now)` block inside
   `VNetBridgeReceiveFromDev()`

All three are inside `#if LOGLEVEL >= 4` debug blocks. Since `LOGLEVEL` is
not defined in production builds, these code paths are dead by default —
but the code still needs to compile cleanly. On kernel >= 5.0 without this
fix, the build fails with:

```
bridge.c: error: implicit declaration of function 'do_gettimeofday'
bridge.c: error: storage size of 'vnetTime' isn't known
```

The fix wraps each affected site with a `LINUX_VERSION_CODE < KERNEL_VERSION(5, 0, 0)`
guard, providing both the old and the new implementation. On kernel >= 5.0,
`struct timespec64` and `ktime_get_real_ts64()` are used.

**Note:** This patch is applied conditionally. The script checks if
`do_gettimeofday` is present in `bridge.c` and not already guarded. It is
a probe-driven, idempotent fix.

---

## Which kernel versions require it

Kernel **>= 5.0** (where `do_gettimeofday` was removed).

Since this tool only supports kernel >= 6.16, this patch is effectively
always needed when `do_gettimeofday` is present in the source.

---

## Which VMware source versions need it

- The community 6.16.x overlay (`patches/upstream/6.16.x/vmnet-only/bridge.c`)
  still contains `do_gettimeofday` — this patch is needed.
- **VMware Workstation Pro 25H2u1** `vmnet-only/bridge.c` still contains
  `do_gettimeofday` — this patch is needed.

The script probes the extracted source at runtime and applies the fix only
when `do_gettimeofday` is present and not already guarded (idempotent).

---

## Source differences between 25H2u1 and 6.16.x overlay

In **25H2u1** `bridge.c`, the static `vnetTime` declaration is wrapped
inside an existing `#if LOGLEVEL >= 4` conditional (lines ~73–75):

```c
#if LOGLEVEL >= 4
static struct timeval vnetTime;
#endif
```

In the **6.16.x community overlay**, the same declaration appears as a bare
line (not wrapped in the LOGLEVEL guard).

The script handles both variants:
- For 25H2u1: replaces the entire `#if LOGLEVEL >= 4 ... #endif` block,
  inserting a nested `LINUX_VERSION_CODE` guard inside the LOGLEVEL guard.
- For 6.16.x overlay: replaces the bare `static struct timeval vnetTime;` line.

The resulting output in 25H2u1:
```c
#if LOGLEVEL >= 4
#  if LINUX_VERSION_CODE < KERNEL_VERSION(5, 0, 0)
static struct timeval vnetTime;
#  else
static struct timespec64 vnetTime;
#  endif
#endif
```

---

## How the script applies it

Function: `_autopatch_bridge_gettimeofday()` in `vmware_module_builder.py`

The function:
1. Checks kernel >= 5.0 (returns early otherwise)
2. Checks if `do_gettimeofday` is present in `bridge.c`
3. Checks if it is already guarded (idempotency)
4. Applies three text replacements, with source-variant detection:
   - Static `vnetTime`: tries LOGLEVEL-wrapped form (25H2u1) first, falls
     back to bare form (6.16.x overlay)
   - `do_gettimeofday(&vnetTime)` → conditional call (all occurrences)
   - `struct timeval now; do_gettimeofday(&now);` → conditional block

---

## Manual application

The patch file targets 25H2u1 sources. For 6.16.x overlay sources the
`vnetTime` hunk differs (bare declaration vs LOGLEVEL-wrapped). For reliable
application across both variants, use the script.

```bash
patch -p2 < /path/to/patches/autopatches/AP-08-bridge-gettimeofday/AP-08-bridge-gettimeofday.patch
```

Or manually replace in `vmnet-only/bridge.c` (25H2u1 sources):

```c
/* BEFORE (25H2u1) */
#if LOGLEVEL >= 4
static struct timeval vnetTime;
#endif

/* AFTER */
#if LOGLEVEL >= 4
#  if LINUX_VERSION_CODE < KERNEL_VERSION(5, 0, 0)
static struct timeval vnetTime;
#  else
static struct timespec64 vnetTime;
#  endif
#endif
```

And replace `do_gettimeofday(&vnetTime)` with:
```c
#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 0, 0)
      do_gettimeofday(&vnetTime)
#else
      ktime_get_real_ts64(&vnetTime)
#endif
```

---

## Attribution

**Author:** Ferran Duarri (© 2026). Original patch written for this project.

This fix addresses the removal of `do_gettimeofday()` in kernel 5.0, which
causes a build failure in VMware's `bridge.c` debug paths. The 25H2u1
source variant wraps the affected declaration inside a `#if LOGLEVEL >= 4`
guard, requiring a two-variant replacement approach (handled automatically
by the script).

---

## References

- Linux 5.0 do_gettimeofday removal: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=
- `ktime_get_real_ts64()` documentation: https://www.kernel.org/doc/html/latest/core-api/timekeeping.html
