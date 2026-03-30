# VMware Module Builder — Patches Directory

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

This directory contains two categories of patch material used by
`vmware_module_builder.py` to build VMware Workstation kernel modules on
modern Linux kernels.

---

## Directory Layout

```
patches/
├── upstream/
│   └── 6.16.x/          # Community source backup (ngodn, pre-VMware 25H2u1)
│       ├── vmmon-only/
│       └── vmnet-only/
└── autopatches/          # Individual reference patches (one per autopatch function)
    ├── AP-01-objtool-vmmon/
    ├── AP-01-objtool-vmnet/
    ├── AP-02-phystrack-bare-returns/
    ├── AP-03-napi-add-3arg/
    ├── AP-04-vmcheck-build/
    ├── AP-05-napi-single-parm/
    ├── AP-06-napi-guard/
    ├── AP-07-task-state-guard/
    ├── AP-08-bridge-gettimeofday/
    ├── AP-09-hostif-gup/
    ├── AP-10-strncpy-to-strscpy/
    ├── AP-11-userif-gup/
    ├── AP-12-module-import-ns/
    └── AP-13-module-define/
```

---

## 1. `upstream/6.16.x/` — Community Source Backup

A local copy of the community-patched VMware kernel module source from
[ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x),
which itself is based on
[64kramsystem/vmware-host-modules-fork](https://github.com/64kramsystem/vmware-host-modules-fork).

**Important:** This source targets VMware Workstation **17.6.4** and was
created **before VMware Workstation Pro 25H2u1** was released.
VMware 25H2u1 already ships equivalent fixes (`ccflags-y`, `timer_delete_sync`,
`module_init`, etc.) in its own tarballs. The script auto-detects this and
**skips the overlay automatically** when 25H2u1 sources are present.

The overlay is only applied when the extracted VMware tarballs are old enough
to lack those fixes (e.g. an older VMware 17.6.x installation).

See `upstream/6.16.x/UPSTREAM-SOURCE.md` for full attribution and details.

---

## 2. `autopatches/` — Individual Reference Patches

Each subdirectory corresponds to one `_autopatch_*` function in
`vmware_module_builder.py`. Every directory contains:

- A `.patch` file in unified diff format showing exactly what the patch
  inserts or replaces.
- A `README.md` explaining the problem, which kernel versions trigger it,
  which VMware source versions are affected, and how to apply it manually.

**These files are reference artefacts.** The script does not read them at
runtime — it applies all patches as in-memory string transformations via its
built-in `_autopatch_*` functions (idempotent, probe-driven). The `.patch`
files exist so that a user can inspect, understand, or manually apply any
individual patch without running the full script.

### Autopatch Index

| ID | Directory | Applied when | What it fixes | Author |
|----|-----------|-------------|--------------|--------|
| AP-01a | `AP-01-objtool-vmmon/` | Kernel ≥ 6.17 / 7.x | `OBJECT_FILES_NON_STANDARD` bypass in vmmon `Makefile.kernel` | Ferran Duarri |
| AP-01b | `AP-01-objtool-vmnet/` | Kernel ≥ 6.17 / 7.x | `OBJECT_FILES_NON_STANDARD` bypass in vmnet `Makefile.kernel` | Ferran Duarri |
| AP-02 | `AP-02-phystrack-bare-returns/` | Kernel ≥ 6.17 / 7.x | Removes bare `return;` at end of void functions in `phystrack.c` | Ferran Duarri |
| AP-03 | `AP-03-napi-add-3arg/` | Source has old 4-arg `netif_napi_add` | Rewrites `compat_netif_napi_add` to 3-arg form for kernel ≥ 6.1 | Ferran Duarri |
| AP-04 | `AP-04-vmcheck-build/` | Always | Injects `vm_check_build` macro into `vmnet/Makefile.kernel` | Ferran Duarri |
| AP-05 | `AP-05-napi-single-parm/` | Kernel ≥ 6.1 | Adds `VMW_NETIF_SINGLE_NAPI_PARM` detection via `vm_check_build` | Ferran Duarri |
| AP-06 | `AP-06-napi-guard/` | (No-op) | Documentation: AP-03 covers the `compat_netdevice.h` guard | — |
| AP-07 | `AP-07-task-state-guard/` | Source lacks guard | `task->__state` compat guard in `hostif.c` for kernel ≥ 5.14 | Ferran Duarri¹ |
| AP-08 | `AP-08-bridge-gettimeofday/` | Source uses `do_gettimeofday` | Replaces with `ktime_get_real_ts64` (removed in kernel 5.0) | Ferran Duarri |
| AP-09 | `AP-09-hostif-gup/` | (No-op) | Documentation: `get_user_pages_fast` API compatible, no change needed | — |
| AP-10 | `AP-10-strncpy-to-strscpy/` | Kernel ≥ 6.8 | `strncpy → strscpy` deprecation fix | Ferran Duarri |
| AP-11 | `AP-11-userif-gup/` | (No-op) | Documentation: `userif.c` `get_user_pages_fast(FOLL_WRITE)` compatible | — |
| AP-12 | `AP-12-module-import-ns/` | Kernel ≥ 5.15 | `MODULE_IMPORT_NS` symbol namespace declaration in `driver.c` | Ferran Duarri |
| AP-13 | `AP-13-module-define/` | Always | Ensures `-DVMMON` / `-DVMNET` identity flags in `Makefile.kernel` | Ferran Duarri |

> ¹ The `task->__state` guard was first introduced in the 6.16.x community
> overlay by [ngodn](https://github.com/ngodn) and
> [64kramsystem](https://github.com/64kramsystem). AP-07 re-applies the
> equivalent fix as a standalone autopatch for VMware sources that do not use
> that overlay.

---

## Credits

All autopatches (AP-01 through AP-13) are authored by **Ferran Duarri**
(© 2026, GPL-2.0-only).

The `upstream/6.16.x/` base overlay is community work:

- **[ngodn](https://github.com/ngodn)** —
  [vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x):
  build system, timer API, MSR API, module init, `task->__state` guard.
- **[64kramsystem](https://github.com/64kramsystem)** —
  [vmware-host-modules-fork](https://github.com/64kramsystem/vmware-host-modules-fork):
  original fork base.

---

## License

All patch files and documentation in this directory are released under the
GNU General Public License, version 2 only (GPL-2.0-only), matching the
Linux kernel license under which these patches are applied.

    Copyright (C) 2026 Ferran Duarri

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; version 2 of the License only.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

The `upstream/6.16.x/` subtree retains the GPL-2.0 license of its original
upstream sources (ngodn / 64kramsystem / VMware).
