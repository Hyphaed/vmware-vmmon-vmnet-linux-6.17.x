# AP-10 — vmmon/vmnet: `strncpy` → `strscpy` Deprecation Fix (kernel >= 6.8)

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## What this patch fixes

Linux 6.8 deprecated `strncpy()` for kernel code and introduced
`-Wdeprecated-declarations` warnings for it under `W=1`. The kernel's
default `W=1` warning level is now commonly enabled during external module
builds, causing strncpy() calls to produce warnings that may fail the build
if `-Werror` is active.

`strscpy()` is the recommended replacement. Key differences:
- `strncpy(dst, src, n)`: copies up to n bytes, zero-pads if shorter than n,
  does NOT guarantee NUL-termination if src is exactly n bytes long
- `strscpy(dst, src, n)`: copies up to n-1 bytes, always NUL-terminates,
  returns the number of bytes copied or -E2BIG on truncation

For the VMware module code patterns (copying known-bounded strings into
fixed-size buffers), `strscpy(dst, src, sizeof(dst))` is a safe drop-in.

**Files affected** (in the community 6.16.x overlay):
- `vmnet-only/vnet.h` (line 354): one `strncpy()` call

The script scans all `.c` files (and `.h` if referenced) in both `vmmon-only/`
and `vmnet-only/` — your specific VMware source version may have more or fewer
occurrences.

---

## Which kernel versions require it

Kernel **>= 6.8** (where `strncpy` deprecation warnings are enabled by
default in kernel module builds).

---

## Which VMware source versions need it

- The community 6.16.x overlay has at least one `strncpy()` call
- VMware Workstation Pro 25H2u1 may have already replaced them — the script
  checks before applying (per-file idempotent)

---

## How the script applies it

Function: `_autopatch_strncpy_to_strscpy()` in `vmware_module_builder.py`

The function is called twice — once for `vmmon-only/`, once for `vmnet-only/`:

1. Recursively finds all `.c` files in the module directory
2. For each file containing `strncpy(`, applies a regex substitution:
   `\bstrncpy\b\s*\(` → `strscpy(`
3. Only writes the file if the content changed (idempotent)
4. Reports the count of modified files

---

## Manual application

```bash
patch -p2 < /path/to/patches/autopatches/AP-10-strncpy-to-strscpy/AP-10-strncpy-to-strscpy.patch
```

Or to apply across all files in a module directory:

```bash
# From inside the module source tree:
grep -rl 'strncpy(' . --include='*.c' | xargs sed -i 's/\bstrncpy\b/strscpy/g'
```

---

## Attribution

**Author:** Ferran Duarri (© 2026). Original patch written for this project.

This fix addresses the `strncpy()` deprecation in kernel >= 6.8, which
triggers build warnings (and errors with `-Werror`) in VMware module sources.
The replacement `strscpy()` is a safe, always-NUL-terminating alternative
that the kernel community recommends for all in-kernel string copying.

---

## References

- Linux kernel `strscpy()` documentation: https://www.kernel.org/doc/html/latest/core-api/kernel-api.html
- strncpy deprecation commit: https://git.kernel.org/linus/
