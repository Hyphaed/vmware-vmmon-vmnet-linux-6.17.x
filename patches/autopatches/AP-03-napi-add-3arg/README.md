# AP-03 — vmnet: `netif_napi_add` 4-arg to 3-arg Fix (kernel >= 6.1)

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## What this patch fixes

Linux 6.1 removed the `weight` (quota) parameter from `netif_napi_add()`,
reducing it from 4 arguments to 3. The old signature was:

```c
void netif_napi_add(struct net_device *dev, struct napi_struct *napi,
                    int (*poll)(struct napi_struct *, int), int weight);
```

The new signature (kernel >= 6.1) is:

```c
void netif_napi_add(struct net_device *dev, struct napi_struct *napi,
                    int (*poll)(struct napi_struct *, int));
```

VMware's `vmnet-only/compat_netdevice.h` defines `compat_netif_napi_add` as
a 4-argument macro. On kernel >= 6.1 this causes:

```
bridge.c: error: too many arguments to function 'netif_napi_add'
hub.c: error: too many arguments to function 'netif_napi_add'
```

The fix appends a version-guarded block after the existing compat definitions
that:
1. Undefines the old 4-arg `compat_netif_napi_add`
2. Redefines it to call 3-arg `netif_napi_add`, silently dropping the `quota`
   argument (the kernel no longer uses it)

---

## Which kernel versions require it

Kernel **>= 6.1**.

---

## Which VMware source versions need it

Sources where `compat_netif_napi_add` is still defined as a 4-argument macro.
This covers:
- VMware Workstation 17.6.x (pre-25H2u1) — always needs it
- The community 6.16.x overlay (`patches/upstream/6.16.x/`) — still has 4-arg

The script probes the source before applying: if the 4-arg form is absent or
already patched (contains `[autopatch]` marker), the patch is skipped.

---

## How the script applies it

Function: `_autopatch_napi_add_compat()` in `vmware_module_builder.py`

The function:
1. Reads `vmnet-only/compat_netdevice.h`
2. Checks for the 4-arg form in the source
3. Checks if it is already fixed (idempotency marker `[autopatch]`)
4. If needed, appends the override block before the closing `#endif` of the
   include guard, or at end of file if no closing guard is found

---

## Manual application

```bash
patch -p2 < /path/to/patches/autopatches/AP-03-napi-add-3arg/AP-03-napi-add-3arg.patch
```

Or manually add before `#endif /* __COMPAT_NETDEVICE_H__ */` at the end of
`vmnet-only/compat_netdevice.h`:

```c
/* [autopatch] kernel 6.1+ dropped the weight param from netif_napi_add */
#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 1, 0)
#  ifdef compat_netif_napi_add
#    undef compat_netif_napi_add
#  endif
#  define compat_netif_napi_add(dev, napi, poll, quota) \
       netif_napi_add((dev), (napi), (poll))
#endif
```

---

## Attribution

**Author:** Ferran Duarri (© 2026). Original patch written for this project.

This fix addresses a kernel API change in Linux 6.1 that causes build failures
when compiling VMware modules. Community-reported build failures on kernel 6.1+
(including those from users of the community 6.16.x overlay) informed the need
for this patch.

---

## References

- See also: [AP-05](../AP-05-napi-single-parm/README.md) — companion patch that
  adds `VMW_NETIF_SINGLE_NAPI_PARM` detection in `Makefile.kernel`
- Linux 6.1 netif_napi_add change: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=d64b5e85a3b
- Upstream 6.16.x community patches: [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x)
