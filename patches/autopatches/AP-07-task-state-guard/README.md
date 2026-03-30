# AP-07 — vmmon: `task->__state` Compat Guard in `hostif.c` (kernel >= 5.14)

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## What this patch fixes

Linux 5.14 renamed `task_struct->state` to `task_struct->__state` (the
double underscore signals that direct access is discouraged). Starting from
kernel 5.15, code that reads `task->state` directly fails to compile because
the field no longer exists by that name.

Additionally, reads of the renamed field must use `READ_ONCE()` to prevent
the compiler from re-reading a potentially stale value.

VMware's `vmmon-only/linux/hostif.c` reads task state directly. On kernel
>= 5.14/5.15 without a compat guard, the build fails with:

```
hostif.c: error: 'struct task_struct' has no member named 'state'
```

The fix adds a `get_task_state(task)` macro immediately after the `#include
"hostif.h"` line. This macro evaluates to:
- `READ_ONCE((task)->__state)` on kernel >= 5.15
- `(task)->state` on older kernels

**Note:** This guard is already present in the community 6.16.x overlay
(`patches/upstream/6.16.x/vmmon-only/linux/hostif.c`) and in VMware
Workstation Pro 25H2u1 sources. The script only applies this patch when
the guard is absent in the extracted source — verified via the
`VmwareSourceInfo.has_task_state_guard` probe.

---

## Which kernel versions require it

Kernel **>= 5.14** (field renamed), with build failure on **>= 5.15**.

---

## Which VMware source versions need it

Older VMware source that predates the 6.16.x community patches. The
community 6.16.x overlay and VMware 25H2u1 both already include this guard.

---

## How the script applies it

Function: `_autopatch_hostif_task_state()` in `vmware_module_builder.py`

The function:
1. Reads `vmmon-only/linux/hostif.c`
2. Checks for the marker string `get_task_state(task) READ_ONCE` (idempotency)
3. If absent, locates `#include "hostif.h"` as the anchor
4. Inserts the version-guarded macro definition after the anchor
5. The `VmwareSourceInfo.has_task_state_guard` probe prevents this from
   running at all when the 6.16.x overlay (which contains the guard) has
   already been applied

---

## Manual application

The exact line number where the guard should be inserted depends on your
`hostif.c`. The guard must appear after the `#include "hostif.h"` line and
before any code that reads task state.

```bash
patch -p2 < /path/to/patches/autopatches/AP-07-task-state-guard/AP-07-task-state-guard.patch
```

Or manually, after `#include "hostif.h"` in `vmmon-only/linux/hostif.c`:

```c
/* [autopatch] kernel 5.14+ renamed task->state to task->__state */
#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 15, 0) || defined(get_current_state)
#define get_task_state(task) READ_ONCE((task)->__state)
#else
#define get_task_state(task) ((task)->state)
#endif
```

---

## Attribution

**Author:** Ferran Duarri (© 2026). Original patch written for this project.

This fix addresses a kernel 5.14 API change. The `task->__state` rename was
already handled in the community 6.16.x overlay by
**[ngodn](https://github.com/ngodn)** and
**[64kramsystem](https://github.com/64kramsystem)** (as part of their `hostif.c`
patches in `patches/upstream/6.16.x/`). For VMware sources that do not use
the 6.16.x overlay, this autopatch applies the equivalent guard independently,
ensuring compatibility across both 25H2u1 and older sources.

---

## References

- Linux 5.14 task->__state change: https://git.kernel.org/linus/2f064a59a11f
- Upstream 6.16.x community patches (original fix): [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x)
