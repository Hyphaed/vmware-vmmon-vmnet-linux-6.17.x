# AP-12 — vmmon: `MODULE_IMPORT_NS` Symbol Namespace Declaration (kernel >= 5.15)

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## What this patch fixes

Linux 5.15 introduced the concept of symbol namespaces for kernel-exported
symbols via `EXPORT_SYMBOL_NS()`. When a kernel module uses a symbol that
belongs to a namespace, it must declare that it imports the namespace with
`MODULE_IMPORT_NS()`, otherwise:

- On kernels with `CONFIG_MODULE_ALLOW_MISSING_NAMESPACE_IMPORTS=n`: the
  module fails to load entirely
- On kernels with that config enabled (the default in most distros): the
  module loads but generates a kernel taint warning

The fix adds:

```c
MODULE_IMPORT_NS("VMWCORE");
```

before `MODULE_LICENSE()` in `vmmon-only/linux/driver.c`.

**This patch is distribution-specific and conditional.** The script applies
it only when:
1. Kernel >= 5.15
2. The kernel headers directory (`/lib/modules/<ver>/build/include`) contains
   files that use `EXPORT_SYMBOL_NS` (heuristic check via grep)

Most mainstream distro kernels (Ubuntu, Fedora, Arch) do not require this for
out-of-tree VMware modules, but hardened or custom kernels may.

---

## Which kernel versions require it

Kernel **>= 5.15**, and only on kernels with strict namespace import enforcement.

---

## Which VMware source versions need it

Any VMware source that does not already have `MODULE_IMPORT_NS` in
`driver.c`. The script checks for the macro's presence before applying.

---

## How the script applies it

Function: `_autopatch_module_import_ns()` in `vmware_module_builder.py`

The function:
1. Returns early if kernel < 5.15
2. Reads `vmmon-only/linux/driver.c`
3. Checks if `MODULE_IMPORT_NS` is already present (idempotency)
4. Checks if `MODULE_LICENSE` is present (sanity)
5. Checks if the kernel headers use `EXPORT_SYMBOL_NS` (distribution check)
6. If all conditions met, inserts `MODULE_IMPORT_NS("VMWCORE");` immediately
   before `MODULE_LICENSE(`

---

## Manual application

```bash
patch -p2 < /path/to/patches/autopatches/AP-12-module-import-ns/AP-12-module-import-ns.patch
```

Or manually add before `MODULE_LICENSE(` in `vmmon-only/linux/driver.c`:

```c
MODULE_IMPORT_NS("VMWCORE");
```

---

## Attribution

**Author:** Ferran Duarri (© 2026). Original patch written for this project.

This patch handles the kernel 5.15 symbol namespace enforcement for VMware
modules. It is applied conditionally — only when the kernel's headers actually
use `EXPORT_SYMBOL_NS`, ensuring it does not affect distributions that do not
require it.

---

## References

- Linux symbol namespaces documentation:
  https://www.kernel.org/doc/html/latest/core-api/symbol-namespaces.html
- Linux 5.15 MODULE_IMPORT_NS: https://git.kernel.org/linus/
