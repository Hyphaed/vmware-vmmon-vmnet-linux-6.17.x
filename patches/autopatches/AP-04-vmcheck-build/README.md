# AP-04 — vmnet: Inject `vm_check_build` into `Makefile.kernel`

SPDX-License-Identifier: GPL-2.0-only
Copyright (C) 2026 Ferran Duarri

---

## What this patch fixes

VMware's vmnet build system defines a helper macro `vm_check_build` that
compile-tests a small C snippet and emits a compiler flag based on whether
the test succeeds or fails. It is used to detect kernel API availability at
build time:

```makefile
ccflags-y += $(call vm_check_build, $(SRCROOT)/netif_trans_update.c, \
             -DVMW_NETIF_TRANS_UPDATE, )
```

**The problem:** `vm_check_build` is defined in `Makefile.normal` (used when
you run `make` directly inside the source tree) but is **absent** from
`Makefile.kernel` (used by the Linux kbuild system when it calls into the
module's directory).

When kbuild processes `Makefile.kernel`, any `$(call vm_check_build, ...)` 
expression silently expands to an empty string because the macro is undefined.
Make does not error on undefined function calls — it just produces nothing.
This causes feature detection to silently fail: flags like
`-DVMW_NETIF_TRANS_UPDATE` and `-DVMW_NETIF_SINGLE_NAPI_PARM` are never set,
leading to wrong code paths being compiled.

The fix injects the `vm_check_build` definition into `Makefile.kernel` before
the first `$(call vm_check_build, ...)` use.

---

## Which kernel versions require it

**All kernel versions.** This is a build-system correctness fix, not a kernel
API compatibility fix. It is always applied.

---

## Which VMware source versions need it

Any VMware source where `Makefile.kernel` references `vm_check_build` without
defining it. This covers:
- VMware Workstation 17.6.x (pre-25H2u1)
- The community 6.16.x overlay (`patches/upstream/6.16.x/`)

**VMware Workstation Pro 25H2u1:** `vmnet-only/Makefile.kernel` does **not**
reference `vm_check_build` at all (the 25H2u1 vmnet Makefile.kernel has no
`$(call vm_check_build, ...)` invocations). The script's AP-04 probe checks
for this and correctly skips the injection for 25H2u1 sources. AP-04 is
effectively a no-op for 25H2u1, and AP-05 directly injects its `vm_check_build`
call alongside the macro definition.

---

## How the script applies it

Function: `_autopatch_vmcheck_build()` in `vmware_module_builder.py`

The function:
1. Reads `vmnet-only/Makefile.kernel`
2. Verifies `vm_check_build` is referenced (`$(call vm_check_build, ...)` present)
3. Verifies `vm_check_build` is NOT yet defined (idempotency check)
4. Detects whether the Makefile uses `ccflags-y` or `EXTRA_CFLAGS` as the
   C flags variable (the probe command uses whichever is active)
5. Inserts the macro definition after the first cflags anchor line

---

## Manual application

```bash
patch -p2 < /path/to/patches/autopatches/AP-04-vmcheck-build/AP-04-vmcheck-build.patch
```

Or manually add the following to `vmnet-only/Makefile.kernel` after the
`ccflags-y :=` line:

```makefile
# vm_check_build: compile-test a C snippet; yields flag2 on success, flag3 on error
vm_check_build = $(shell if $(CC) $(ccflags-y) -Werror -S -o /dev/null -xc $(1) \
    > /dev/null 2>&1; then echo "$(2)"; else echo "$(3)"; fi)
```

---

## Attribution

**Author:** Ferran Duarri (© 2026). Original patch written for this project.

This patch was created after investigating `Makefile.kernel:38: *** missing
separator. Stop.` build failures reported by community users — a symptom of
`$(call vm_check_build, ...)` silently expanding to nothing because the macro
was undefined in the kbuild context. The fix injects the macro definition so
that `vm_check_build`-based feature detection works correctly under kbuild.

---

## References

- See also: [AP-05](../AP-05-napi-single-parm/README.md) — builds on this fix
  to add `VMW_NETIF_SINGLE_NAPI_PARM` detection
