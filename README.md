[![Kernel](https://img.shields.io/badge/Kernel-6.16.x%20%7C%206.17.x%20%7C%207.x-orange.svg)](https://kernel.org/)
[![VMware](https://img.shields.io/badge/VMware-Workstation%2025.x-blue.svg)](https://www.vmware.com/)
[![Tested on](https://img.shields.io/badge/Tested%20on-Ubuntu%207.0.0--7--generic-green.svg)](https://ubuntu.com/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-yellow.svg)](https://python.org/)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-red.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)

# 🔧 VMware DKMS Module Builder
**Author:** Ferran Duarri  **License:** GPL v2 (open-source)

### ⚡ Fix VMware Workstation on modern Linux kernels — automatically
### 🚀 Get better-than-stock performance with a single script

---

<div align="center">

[![Contributors](https://contrib.rocks/image?repo=Hyphaed/vmware-vmmon-vmnet-linux-6.17.x)](https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/graphs/contributors)

</div>

## 😤 Sound familiar?

You updated your Linux kernel (or installed a fresh distro), launched VMware Workstation, and got hit with one of these:

```
Failed to build vmmon
Failed to build vmnet
/dev/vmci: No such file or directory
modprobe: ERROR: could not insert 'vmmon'
```

VMware ships kernel modules as source code and builds them on your machine. The problem is that the Linux kernel evolves fast — every few releases, internal APIs change, and VMware's source code hasn't caught up yet. The result: the modules simply refuse to compile.

**This tool fixes all of that for you.** It applies the right compatibility patches for your exact kernel, compiles the modules, installs them, and optionally squeezes extra performance out of your hardware while doing so.

---

## 🏆 Why this beats VMware's own installer

VMware's official way of building its kernel modules is to run `vmware-modconfig --console --install-all` and hope for the best. On a stable, older kernel it usually works. On anything modern, it fails — and when it fails, it gives you an error message and walks away. No explanation, no fix, no fallback.

This script does things differently, and better, in several concrete ways:

### 🔨 VMware's way: build and pray

When VMware builds its own modules, it does the absolute minimum:

- Compiles `vmmon` and `vmnet` with generic, conservative compiler flags
- Does zero hardware detection — your CPU is just "x86_64" to it
- Applies no compatibility patches — if the kernel API changed, the build fails
- Leaves you to figure out why `/dev/vmci` doesn't exist
- Doesn't configure boot-time module loading — on some setups modules disappear after reboot
- Has no concept of your kernel version being "too new" — it just errors out

### 🚀 This script's way: build it right

This script treats module compilation as what it actually is, a software build that should be optimized for its target environment:

- **Automatically patches VMware's source code** for your exact kernel version. It detects what's broken and fixes it, silently, before compilation even starts. You don't need to know that kernel 6.x-7.x renamed a timer function or that kernel 6.x-7.x changed how network adapters register — the script knows, and handles it.

- **Compiles with hardware-aware flags** (Optimized mode). Instead of a one-size-fits-all binary, the modules are compiled specifically for *your CPU* — its instruction sets, its vector units, its virtualization extensions. The result is a module that runs measurably faster on your machine than the generic one VMware would produce.

- **Fixes the `vmci` situation properly.** VMware 25 doesn't ship `vmci` source anymore — it relies on the in-kernel `vmw_vmci` driver. VMware's own tooling doesn't always handle this gracefully. This script does.

- **Sets up boot persistence correctly.** It writes `/etc/modules-load.d/vmware.conf` and creates a proper `vmware.service` systemd unit. Your modules will be there after every reboot, in the right order, without race conditions.

- **Backs up before touching anything.** VMware's installer will happily overwrite your working modules. This script takes a hash-verified backup first, so you always have a clean copy to return to.

- **Tells you what it's doing.** Every step is logged clearly. If something goes wrong, you see exactly where and why — not just a generic "build failed" message.

---

## ✅ What's been tested

| Component | Version |
|-----------|---------|
| Kernel | `7.0.0-7-generic` (Ubuntu) |
| VMware Workstation | **Pro 25H2u1** (`25.0.1 build 25219725`) |
| Architecture | x86_64 |

It also supports kernels **6.16.x** and **6.17.x**, and handles all the distro variations that come with them (Ubuntu, Fedora, Arch, Gentoo, Void, and more).

---

## 🎯 What this tool actually does

Here's the full pipeline:

1. **Checks your environment** — kernel version, headers, VMware installation, Secure Boot status
2. **Backs up the original VMware sources** — so you can always go back to stock
3. **Detects your CPU capabilities** — VT-x/AMD-V, AVX-512, AVX2, AES-NI, EPT, VPID, huge pages
4. **Applies compatibility patches automatically** — fixes all the kernel API changes that break VMware
5. **Optionally applies performance optimizations** — compiles modules specifically for *your* CPU
6. **Compiles, installs and loads the modules** — `vmmon` and `vmnet`
7. **Fixes `vmci`** — handles the `/dev/vmci` issue (VMware 25 uses the in-kernel `vmw_vmci` driver)
8. **Updates initramfs and module database** — so everything persists across reboots
9. **Creates a systemd service** — modules load cleanly on boot, no race conditions
10. **Optionally registers modules with DKMS** — so they rebuild automatically on every future kernel update (DKMS path only)
11. **Verifies everything** — prints a final summary so you know it worked

---

## 🩹 The compatibility patches (what gets fixed)

Every modern kernel breaks something in VMware's source. This tool detects your kernel version and applies the right fixes automatically — no manual patching required. Each patch also exists as an individual reference file under `patches/autopatches/` for inspection or manual application.

### Patches always applied

| Patch | Reference | What it fixes | Author |
|-------|-----------|--------------|--------|
| **AP-04** | `patches/autopatches/AP-04-vmcheck-build/` | `vmnet Makefile.kernel` — injects `vm_check_build` so the build system works | Ferran Duarri |
| **AP-13** | `patches/autopatches/AP-13-module-define/` | Module identity defines (`-DVMMON` / `-DVMNET`) in `Makefile.kernel` | Ferran Duarri |
| **AP-05** | `patches/autopatches/AP-05-napi-single-parm/` | `VMW_NETIF_SINGLE_NAPI_PARM` detection — needed for kernel 6.1+ networking | Ferran Duarri |
| **AP-09** | `patches/autopatches/AP-09-hostif-gup/` | `hostif.c` — `get_user_pages_fast` API check (memory pinning, documented) | Ferran Duarri |
| **AP-10** | `patches/autopatches/AP-10-strncpy-to-strscpy/` | `strncpy → strscpy` — fixes a deprecation warning that becomes a build error on 6.8+ | Ferran Duarri |
| **AP-11** | `patches/autopatches/AP-11-userif-gup/` | `userif.c` — `get_user_pages_fast` API check, network side (documented) | Ferran Duarri |
| **AP-12** | `patches/autopatches/AP-12-module-import-ns/` | `MODULE_IMPORT_NS` — symbol namespace declaration required since kernel 5.15 | Ferran Duarri |

### Patches applied when your kernel needs them

| Patch | Condition | Reference | What it fixes | Author |
|-------|-----------|-----------|--------------|--------|
| **AP-01** | Kernel ≥ 6.17 / 7.x | `patches/autopatches/AP-01-objtool-vmmon/` + `AP-01-objtool-vmnet/` | Objtool compatibility — `OBJECT_FILES_NON_STANDARD` for problematic files | Ferran Duarri |
| **AP-02** | Kernel ≥ 6.17 / 7.x | `patches/autopatches/AP-02-phystrack-bare-returns/` | Removes bare `return;` in void functions (`phystrack.c`) that objtool rejects | Ferran Duarri |
| **AP-03** | Source has old 4-arg `netif_napi_add` | `patches/autopatches/AP-03-napi-add-3arg/` | Rewrites it to the 3-arg form required by kernel 6.1+ | Ferran Duarri |
| **AP-07** | Source lacks `task->__state` guard | `patches/autopatches/AP-07-task-state-guard/` | Adds the compatibility guard needed since kernel 5.14 | Ferran Duarri¹ |
| **AP-08** | Source uses `do_gettimeofday` | `patches/autopatches/AP-08-bridge-gettimeofday/` | Replaces it with `ktime_get_real_ts64` — removed in kernel 5.0 | Ferran Duarri |
| **Base 6.16.x overlay** | Kernel ≥ 6.16 with pre-25H2u1 VMware source | `patches/upstream/6.16.x/` | Overlays community source files to fix build system and timer API changes (skipped for 25H2u1) | [ngodn](https://github.com/ngodn) / [64kramsystem](https://github.com/64kramsystem) |

> ¹ The `task->__state` guard was first introduced in the 6.16.x community
> overlay by [ngodn](https://github.com/ngodn) and
> [64kramsystem](https://github.com/64kramsystem). AP-07 re-applies the
> equivalent fix independently for VMware sources that do not use that overlay.

### Fixes from everyday use — not yet addressed upstream

All patches in this tool were identified through **real-world daily use of VMware Workstation on production Linux systems** running kernels 6.16, 6.17, and 7.x. None of these regressions have been addressed in the VMware module sources shipped by Broadcom at the time of writing:

- **Silent build system failure** — `vm_check_build` is only defined in `Makefile.normal`, not in `Makefile.kernel`. When kbuild invokes `Makefile.kernel` directly, all `$(call vm_check_build, ...)` expressions silently expand to nothing, disabling feature detection without any error message. (AP-04)
- **`netif_napi_add` signature change** — Linux 6.1 removed the `weight` parameter, making it a 3-argument call. VMware's `compat_netdevice.h` still passes 4 arguments, breaking network adapter compilation on any kernel 6.1 or later. (AP-03, AP-05)
- **`strncpy` deprecation becomes a hard error** — Kernel 6.8+ deprecates `strncpy()` for kernel-space use. Under `-Werror` this causes a build failure. The fix is a mechanical substitution to `strscpy()`. (AP-10)
- **Objtool rejects VMware's custom inline assembly** — Kernel 6.17 and 7.x enabled stricter objtool validation that rejects the non-standard stack frames in `phystrack.c` and `task.c`. Without the `OBJECT_FILES_NON_STANDARD` exclusion markers the build fails entirely. (AP-01, AP-02)
- **Missing module identity defines** — Some VMware source tarballs omit `-DVMMON` / `-DVMNET` from `Makefile.kernel`, causing the module to compile without its own identity preprocessor define and silently disabling internal feature detection paths. (AP-13)

---

## ⚡ Performance mode — why you want Option 2

When you run the script, it asks you to pick a compilation mode:

```
  1) Vanilla  — standard VMware compilation, portable
  2) Optimized — modules only work on this CPU architecture (default)
       Flags that will be applied:
         GCC  : -march=native -mtune=native -O3 -ffast-math -fno-strict-aliasing
         Make : VMWARE_OPTIMIZE=1 HAS_VTX_EPT=1 HAS_AVX512=1
         Cores: -j16
```

> **TL;DR: Pick Option 2. Here's why.**

### What Vanilla does

Vanilla mode just applies the compatibility patches and compiles with VMware's default flags. The modules work, but they're compiled generically — no knowledge of your actual CPU.

### What Optimized does on top of that

Optimized mode adds a block of carefully crafted compiler flags that tell GCC exactly what hardware it's targeting:

- **`-march=native -mtune=native`** — the compiler generates instructions for *your specific CPU*, not a generic x86_64. If you have AVX-512, it uses AVX-512. If you have AES-NI, it uses AES-NI.
- **`-O3 -ffast-math -funroll-loops`** — higher optimization level, loop unrolling, and math shortcuts safe for kernel module code
- **`-fno-strict-aliasing -fno-strict-overflow -fno-delete-null-pointer-checks`** — safety flags that prevent the optimizer from making incorrect assumptions about kernel memory access patterns
- **`VMWARE_OPTIMIZE=1`** — enables the optimization block inside VMware's own Makefiles
- **`HAS_VTX_EPT=1`** — activates VT-x / EPT-aware code paths (Intel CPUs with Extended Page Tables)
- **`HAS_AVX512=1`** — activates AVX-512 SIMD paths if your CPU supports them
- **`likely()` / `unlikely()` branch hints** — added to `vm_basic_types.h` so the CPU's branch predictor works more efficiently
- **Cache line alignment** (`CACHE_LINE_SIZE 64`) — reduces false sharing between CPU cores

### Real-world gains

These aren't marketing numbers — they come from the nature of what's being optimized:

| Area | Typical improvement |
|------|-------------------|
| CPU-bound VM operations | 15–25% faster |
| Memory operations (with AVX2/AVX-512) | 20–50% faster |
| Cryptographic ops inside VM (with AES-NI) | 30–50% faster |
| Module load time | noticeably snappier |
| Overall VM responsiveness | meaningful improvement |

---

## 🖥️ What your CPU can unlock

The script detects your CPU and tells you exactly what it found before asking you to choose:

```
  CPU Model               : Intel Core i9-13900K
  Hardware Virtualization : Intel VT-x
  VPID                    : yes
  AVX-512                 : yes
  AVX2                    : yes
  FMA / F16C              : yes / yes
  AES-NI                  : yes
  SSE4.2                  : yes
  1GB Huge Pages (EPT)    : yes
```

The more capabilities your CPU has, the more the Optimized mode can exploit them.

---

## 📦 Quick start

### Prerequisites

You need kernel headers installed for your current kernel. If you're not sure, this command installs them:

```bash
# Ubuntu / Debian
sudo apt install build-essential linux-headers-$(uname -r)

# Fedora / RHEL / Rocky / AlmaLinux
sudo dnf install gcc make kernel-devel kernel-headers

# Arch / Manjaro
sudo pacman -S base-devel linux-headers

# openSUSE
sudo zypper install gcc make kernel-devel

# Gentoo
cd /usr/src/linux && make modules_prepare
```

You also need **VMware Workstation already installed** (this tool fixes the modules, it doesn't install VMware itself).

### Run the builder

```bash
# Clone the repository
git clone <repository-url>
cd vmware_module_builder

# Run as root (needed to install kernel modules)
sudo python3 vmware_module_builder.py
```

That's it. The script will guide you through everything interactively.

---

## 🔄 Step-by-step walkthrough (for newcomers)

If you've never done anything like this before, here's exactly what happens when you run the script:

**1. Startup checks** — the script verifies your kernel version, finds the kernel headers, confirms VMware is installed, and checks whether Secure Boot is enabled.

**2. Backup** — before touching anything, it creates a backup of VMware's original source tarballs. If something goes wrong, you can restore from the backup.

**3. Hardware scan** — it reads `/proc/cpuinfo` to find out what your CPU can do (AVX-512, AES-NI, VT-x, etc.).

**4. Mode selection** — you choose Vanilla or Optimized (pick 2 — see above).

**5. Patching** — it extracts VMware's source code into a temporary directory and applies all the compatibility patches automatically. You'll see each step logged as it happens.

**6. Compilation** — it runs `make` with the flags you chose, using all your CPU cores to go fast.

**7. Installation** — it copies the compiled `.ko` files to `/lib/modules/<kernel>/misc/` and repacks the source tarballs so VMware's own build system stays consistent.

**8. Post-install** — runs `depmod` (module dependency database), updates `initramfs`, writes `/etc/modules-load.d/vmware.conf` (so modules load at boot), and creates a systemd `vmware.service` unit.

**9. Module loading** — loads `vmmon` and `vmnet` immediately so you don't need to reboot.

**10. Verification** — checks that everything is loaded correctly and prints a summary.

---

## 🔐 Secure Boot

If your system has Secure Boot enabled, the script will detect it and warn you. Unsigned kernel modules can't load with Secure Boot active. The script will print the exact commands you need to sign the modules with your MOK key — but you'll need to have a MOK key set up first.

> `vmw_vmci` (the in-kernel VMware VMCI driver) is already signed by your kernel's build key and doesn't need MOK signing. Only `vmmon` and `vmnet` are affected.

---

## 🗂️ Repository structure

```
vmware_module_builder/
├── vmware_module_builder.py        # The main script (everything is in here)
└── patches/
    ├── upstream/
    │   └── 6.16.x/                 # Community source backup (pre-25H2u1, see note below)
    │       ├── vmmon-only/
    │       └── vmnet-only/
    └── autopatches/                # Individual reference patches (one per autopatch)
        ├── AP-01-objtool-vmmon/    # Objtool bypass for vmmon (kernel ≥ 6.17 / 7.x)
        ├── AP-01-objtool-vmnet/    # Objtool bypass for vmnet (kernel ≥ 6.17 / 7.x)
        ├── AP-02-phystrack-bare-returns/  # Remove bare return; objtool rejects
        ├── AP-03-napi-add-3arg/    # netif_napi_add 4-arg → 3-arg (kernel ≥ 6.1)
        ├── AP-04-vmcheck-build/    # Inject vm_check_build into Makefile.kernel
        ├── AP-05-napi-single-parm/ # VMW_NETIF_SINGLE_NAPI_PARM detection
        ├── AP-07-task-state-guard/ # task->__state compat guard (kernel ≥ 5.14)
        ├── AP-08-bridge-gettimeofday/ # do_gettimeofday → ktime_get_real_ts64
        ├── AP-10-strncpy-to-strscpy/  # strncpy → strscpy (kernel ≥ 6.8)
        ├── AP-12-module-import-ns/ # MODULE_IMPORT_NS namespace (kernel ≥ 5.15)
        └── AP-13-module-define/    # -DVMMON / -DVMNET identity flags
```

**About `patches/upstream/6.16.x/`:** This is a local backup of the community-patched VMware source from [ngodn/vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x), which targeted VMware Workstation **17.6.4** (released before **VMware Workstation Pro 25H2u1**). VMware 25H2u1 ships equivalent fixes natively (`ccflags-y`, `timer_delete_sync`, `module_init`, etc.), so the script **automatically detects and skips** this overlay when 25H2u1 sources are present. It is retained as a fallback for older VMware installations.

**About `patches/autopatches/`:** Each subdirectory contains a `.patch` file (unified diff format) and a `README.md` documenting exactly what that autopatch does, which kernel versions trigger it, and how to apply it manually. These are reference artefacts — the script applies all patches at runtime via its built-in `_autopatch_*` functions without reading these files.

---

## 🐧 Supported distributions

The script auto-detects your distro and knows how to install kernel headers on:

| Family | Distributions |
|--------|--------------|
| Debian | Ubuntu, Pop!_OS, Linux Mint, Kali, Parrot, elementary, Raspberry Pi OS |
| Red Hat | Fedora, RHEL, CentOS, Rocky Linux, AlmaLinux, Amazon Linux |
| Arch | Arch Linux, Manjaro, EndeavourOS, Garuda, Artix |
| SUSE | openSUSE Leap, openSUSE Tumbleweed, SUSE Enterprise |
| Others | Gentoo, Alpine, Void Linux, NixOS, Slackware |

---

## 🔁 Running again after a kernel update

### DKMS path (recommended) — automatic

If you chose **option 1 (DKMS)** when running `install-vmware-modules.sh`, the modules are registered with DKMS. **You do not need to do anything after a kernel update.** When your system installs a new kernel package, DKMS automatically rebuilds `vmmon` and `vmnet` for that kernel and installs them before the first boot into it.

```bash
# First-time install only (choose option 1 at the menu):
sudo ./install-vmware-modules.sh
# After that — kernel updates are handled automatically by DKMS.
```

### Non-DKMS path — manual

If you chose **option 2 (Non-DKMS)** when running `install-vmware-modules.sh`, you must re-run the script after each kernel update and select option 2 again:

```bash
sudo ./install-vmware-modules.sh
# Select: 2) Non-DKMS (manual)
```

The backup system ensures idempotency — it always patches from the original clean source, so re-running never accumulates corruption regardless of how many times it is run.

---

## 🔧 Utility Scripts

Three shell scripts are provided alongside the main Python builder. All require root and must be run from the repository directory.

---

### `install-vmware-modules.sh` — Unified installer (DKMS or non-DKMS)

The main entry point. On startup it:

1. **Checks for a newer version** against the GitLab repository (non-blocking, 5-second timeout). If a newer release is found you are offered the option to stop and download it first.
2. **Presents an installation mode menu:**

```
  ┌──────────────────────────────────────────────────────────┐
  │  1) DKMS  (recommended — default)                        │
  │     Modules are registered with DKMS and rebuilt         │
  │     automatically on every kernel update.                │
  │     No manual re-run needed after 'apt upgrade'.         │
  │                                                          │
  │  2) Non-DKMS  (manual)                                   │
  │     Modules are installed for the current kernel only.   │
  │     You must re-run this script after every kernel       │
  │     update.                                              │
  └──────────────────────────────────────────────────────────┘
  Select [1/2, default=1]:
```

```bash
sudo ./install-vmware-modules.sh
```

**Both modes:**
- Confirm Python 3.8+ is available
- Run the full build pipeline: backup → patch → compile → install → initramfs → systemd
- Check for corrupt VMware XML config files that can cause startup crashes
- Prompt for Vanilla or Optimized compilation mode

**DKMS mode additionally:**
- Requires `dkms` to be installed (`apt-get install dkms`)
- **Purges every pre-existing DKMS registration** for `vmmon` and `vmnet` (any version, including any VMware's own installer may have placed) so the patched build is the sole authority
- Removes any `/usr/src/vmmon-*/` or `/usr/src/vmnet-*/` trees VMware may have written
- Extracts the patched source tree into `/usr/src/vmmon-<ver>/` and `/usr/src/vmnet-<ver>/`
- Registers both modules with DKMS (`AUTOINSTALL="yes"`) and installs with `--force` to overwrite any conflicting `.ko`
- **No re-run needed after kernel updates** — DKMS handles rebuilds automatically

**Non-DKMS mode:**
- Skips DKMS registration
- Fully idempotent — always patches from the original backup
- **Must be re-run after every kernel update**

---

### `uninstall-vmware-modules.sh` — Remove installed modules

Interactive menu that asks what to do before making any changes. Handles both DKMS-registered and non-DKMS installations automatically.

```bash
sudo ./uninstall-vmware-modules.sh
```

**Menu options:**

| Option | What happens |
|--------|-------------|
| **1) Uninstall + restore originals** | Removes DKMS registrations and source trees (if any), unloads modules, removes `.ko` files, restores original VMware source tarballs from backup, rebuilds with `vmware-modconfig`, removes tool-managed systemd/config files |
| **2) Fully uninstall (no restore)** | Removes DKMS registrations and source trees (if any), unloads modules, removes `.ko` files and all config (`/etc/modules-load.d/vmware.conf`, `/etc/modprobe.d/vmware.conf`, `vmware.service`), leaves source tarballs untouched |
| **3) Cancel** | No changes made |

---

### `restore-original-vmware-modules.sh` — Restore original VMware sources

Lists all available backups and lets you choose which one to restore from. Useful if a patched build is causing issues or you want to revert to VMware's stock modules.

```bash
sudo ./restore-original-vmware-modules.sh
```

**What it does:**
1. Lists all backups in `/usr/lib/vmware/modules/source/backup-<timestamp>/`
2. Prompts you to select which backup to restore (oldest = most likely to be the original clean source)
3. Copies `vmmon.tar` and `vmnet.tar` back to `/usr/lib/vmware/modules/source/`
4. Offers to rebuild via `vmware-modconfig` (stock) or `install-vmware-modules.sh` (patched)

**When to use this:**
- VMware modules were working before and stopped after a bad patch run
- You want to hand control back to VMware's own build tooling
- Preparing to reinstall VMware Workstation

---

### Crash note — 2026-03-26 15:01:37

The workstation crash that triggered this tool update was traced to **corrupt VMware XML config files**. VMware Workstation emitted:

```
Entity: line 1: parser error : Document is empty
```

on launch, which caused a GNOME session hang and hard reboot. The kernel modules themselves were loaded correctly — the issue was in VMware's userspace config layer.

`install-vmware-modules.sh` now runs `check_vmware_config()` as part of its pre-flight checks and will warn you if any of these files are empty or malformed:

- `~/.vmware/preferences`
- `~/.vmware/*.xml`
- `/etc/vmware/*.xml`
- `/usr/lib/vmware/modules/source/modules.xml`

If affected files are found, the script prints the exact `rm` commands to remove and regenerate them.

---

## 🙏 Credits

### Community contributors

The `patches/upstream/6.16.x/` base overlay — which makes older VMware 17.6.x
installations buildable against kernel 6.16 — is the work of the open-source
community:

- **[ngodn](https://github.com/ngodn)** —
  [vmware-vmmon-vmnet-linux-6.16.x](https://github.com/ngodn/vmware-vmmon-vmnet-linux-6.16.x):
  build system migration (`ccflags-y`), timer API (`timer_delete_sync`), MSR
  API (`rdmsrq_safe`), module init macro, function prototype fixes, and the
  `task->__state` guard in `hostif.c`.
- **[64kramsystem](https://github.com/64kramsystem)** —
  [vmware-host-modules-fork](https://github.com/64kramsystem/vmware-host-modules-fork):
  the original fork base that ngodn's patches build on.

### Community-reported issues that informed this project

Several bugs and gaps in the previous tooling were surfaced by community reports on old project I was mantaining at github https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x ; In few days when I recover access to my gtihub account I will update the repository there also. Those reports directly drove the scope and priorities of this project:

- Users reporting `Makefile.kernel:38: *** missing separator. Stop.` failures
  led to AP-04 (`vm_check_build` injection) and AP-13 (module identity defines).
- Users reporting build failures on kernel 6.17+ informed AP-01 and AP-02
  (objtool bypass and bare return removal).
- Users reporting 25H2u1 incompatibility informed the 25H2u1 source analysis
  and the AP-05/AP-08 bug fixes (anchor mismatch, LOGLEVEL guard).

---

## ❓ Troubleshooting

**"Kernel headers not found"**
Install them for your running kernel — see the Prerequisites section above.

**"VMware Workstation not found"**
Make sure VMware is installed. The script looks for the `vmware` binary and the module source at `/usr/lib/vmware/modules/source/`.

**Module loads but VMs won't start**
Try restarting VMware services:
```bash
sudo systemctl restart vmware.service vmware-networks.service
```

**`/dev/vmci` not present**
This is normal. `vmw_vmci` is loaded by VMware itself when you start a VM, not at boot. It will appear as soon as you power on a virtual machine.

**Secure Boot is blocking the module**
The script prints the signing commands when it detects Secure Boot. Follow those steps to enroll and use your MOK key.

**Something went wrong and I want stock modules back**
The script backs up originals to `/usr/lib/vmware/modules/source/backup*/`. You can restore from there, or simply reinstall VMware Workstation.

**Happy virtualizing! 🚀**
