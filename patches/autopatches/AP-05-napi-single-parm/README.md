# AP-05 — vmnet: `VMW_NETIF_SINGLE_NAPI_PARM` Detection in `Makefile.kernel`

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## What this patch fixes

`vmnet-only/compat_netdevice.h` uses the compile-time flag
`VMW_NETIF_SINGLE_NAPI_PARM` to activate the 3-argument form of
`compat_napi_complete` and `compat_napi_schedule`:

```c
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2, 6, 30) || \
    defined VMW_NETIF_SINGLE_NAPI_PARM
#   define compat_napi_complete(dev, napi) napi_complete(napi)
```

This flag is set in `Makefile.normal` via:

```makefile
ccflags-y += $(call vm_check_build, ..., -DVMW_NETIF_SINGLE_NAPI_PARM, )
```

However, `Makefile.kernel` (the file invoked by kbuild) does not set this
flag. The AP-04 fix injects `vm_check_build` into `Makefile.kernel`, but
AP-04 alone does not add the detection call for `VMW_NETIF_SINGLE_NAPI_PARM`.

This patch adds the detection call: it compiles a small probe file
(`netif_napi_add_check.c`) that calls the 3-arg `netif_napi_add`. If the
probe compiles, the kernel has the 3-arg form and `-DVMW_NETIF_SINGLE_NAPI_PARM`
is set. If not, the flag is absent and the older code path is used.

**Dependency:** AP-04 must be applied first (this patch uses `vm_check_build`).

---

## Which kernel versions require it

Kernel **>= 6.1** (where `netif_napi_add` was changed to 3 arguments).

---

## Which VMware source versions need it

Sources where `VMW_NETIF_SINGLE_NAPI_PARM` is not already set in
`Makefile.kernel`. This covers:
- VMware Workstation 17.6.x (pre-25H2u1)
- The community 6.16.x overlay
- **VMware Workstation Pro 25H2u1** — still needs this fix; `Makefile.kernel`
  does not set `VMW_NETIF_SINGLE_NAPI_PARM`

---

## Source differences between 25H2u1 and 6.16.x overlay

| Attribute | 6.16.x community overlay | 25H2u1 official source |
|---|---|---|
| Final `ccflags-y` assignment | `ccflags-y :=` | `ccflags-y +=` |
| `vm_check_build` in Makefile.kernel | absent (needs AP-04 first) | absent (needs AP-04 first) |
| `VMW_NETIF_SINGLE_NAPI_PARM` set | no | no |

The script handles both variants: the anchor search looks for
`ccflags-y :=` **or** `ccflags-y +=` and uses the last matching line as
the insertion point. The injected text is identical for both source variants.

---

## How the script applies it

Function: `_autopatch_vmnet_napi_flag()` in `vmware_module_builder.py`

The function:
1. Checks kernel >= 6.1 (returns early otherwise)
2. Checks if `VMW_NETIF_SINGLE_NAPI_PARM` is already in `Makefile.kernel`
3. Creates `vmnet-only/netif_napi_add_check.c` probe file if absent
4. Inserts the `$(call vm_check_build, ...)` line after the last `ccflags-y`
   assignment in `Makefile.kernel` (matches both `:=` and `+=` forms)

---

## Manual application

Requires AP-04 to be applied first.

```bash
patch -p2 < /path/to/patches/autopatches/AP-05-napi-single-parm/AP-05-napi-single-parm.patch
```

Or manually:

1. Create `vmnet-only/netif_napi_add_check.c`:
```c
/* autopatch probe: detect 3-arg netif_napi_add (kernel 6.1+) */
#include <linux/netdevice.h>
static int dummy_poll(struct napi_struct *n, int b) { return 0; }
void test(struct net_device *dev, struct napi_struct *napi) {
    netif_napi_add(dev, napi, dummy_poll);
}
```

2. Add to `vmnet-only/Makefile.kernel` after the last `ccflags-y +=` line:
```makefile
# Detect 3-arg netif_napi_add (kernel 6.1+ dropped the weight param)
ccflags-y += $(call vm_check_build, $(SRCROOT)/netif_napi_add_check.c,-DVMW_NETIF_SINGLE_NAPI_PARM, )
```

---

## Attribution

**Author:** Ferran Duarri (© 2026). Original patch written for this project.

This patch was created as a companion to AP-04 and AP-03 to complete the NAPI
detection chain: AP-04 defines `vm_check_build`, AP-05 uses it to probe for
3-arg `netif_napi_add`, and AP-03 applies the actual header fix. Without AP-05,
the `VMW_NETIF_SINGLE_NAPI_PARM` flag was silently never set under kbuild,
causing AP-03's fix to have no effect at runtime.

---

## References

- See also: [AP-04](../AP-04-vmcheck-build/README.md) — prerequisite: injects `vm_check_build`
- See also: [AP-03](../AP-03-napi-add-3arg/README.md) — companion fix in `compat_netdevice.h`
