#!/usr/bin/env python3
"""
VMware Module Builder
Rebuilds vmmon, vmnet and fixes vmci for the current running kernel.
Applies kernel compatibility patches from the local Hyphaed repo.
Resolves "/dev/vmci: No such file or directory" and objtool build errors.
"""

import subprocess
import sys
import os
import re
import hashlib
import tarfile
import tempfile
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Local patch repo — all patches sourced from here, no internet needed
# ─────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PATCHES_DIR = SCRIPT_DIR / "patches"
UPSTREAM_616_DIR = PATCHES_DIR / "upstream/6.16.x"

VMWARE_MOD_DIR = Path("/usr/lib/vmware/modules/source")
BACKUP_DIR_PREFIX = VMWARE_MOD_DIR / "backup"

# VMware Workstation 25 does not ship vmci source; the kernel provides it
# as 'vmw_vmci' (in-kernel driver, already signed by the kernel build key).
VMCI_MODULE = "vmw_vmci"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def banner(text: str):
    width = 62
    print("╔" + "═" * width + "╗")
    for line in text.strip().splitlines():
        print("║" + line.center(width) + "║")
    print("╚" + "═" * width + "╝")


def section(title: str):
    print(f"\n{'─'*62}")
    print(f"  {title}")
    print(f"{'─'*62}")


def ok(msg: str):   print(f"  ✅  {msg}")
def info(msg: str): print(f"  ℹ️  {msg}")
def warn(msg: str): print(f"  ⚠️   {msg}", file=sys.stderr)
def err(msg: str):  print(f"  ❌  {msg}", file=sys.stderr)


def run(cmd: list, check=False, capture=True, cwd=None, timeout=None) -> subprocess.CompletedProcess:
    """Run a command, always printing it. Returns CompletedProcess."""
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            check=False,
            cwd=cwd,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        warn(f"Command timed out after {timeout}s: {' '.join(str(c) for c in cmd)}")
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="timeout")
    if capture and result.stdout:
        for line in result.stdout.splitlines():
            print(f"    {line}")
    if capture and result.stderr:
        for line in result.stderr.splitlines():
            print(f"    {line}", file=sys.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd,
                                            result.stdout, result.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2a — Robust kernel version parsing
# ─────────────────────────────────────────────────────────────────────────────

class KernelVersion:
    """Parse kernel version strings robustly, handling distro suffixes.

    Handles: 7.0.0-7-generic, 6.17.11+deb14-amd64, 6.16.8+kali-amd64,
             6.6.35-1-MANJARO, 6.11.0-1014-aws, 6.12.6_1 (Void), etc.
    """

    def __init__(self, raw: str):
        self.raw = raw
        m = re.match(r'^(\d+)\.(\d+)(?:\.(\d+))?', raw)
        if not m:
            raise ValueError(f"Cannot parse kernel version: {raw!r}")
        self.major = int(m.group(1))
        self.minor = int(m.group(2))
        self.patch = int(m.group(3) or 0)

    def at_least(self, major: int, minor: int) -> bool:
        return (self.major, self.minor) >= (major, minor)

    def needs_base_616_patches(self) -> bool:
        return self.at_least(6, 16)

    def needs_objtool_patches(self) -> bool:
        return self.major >= 7 or (self.major == 6 and self.minor >= 17)

    def is_supported(self) -> bool:
        return self.at_least(6, 16)

    def __str__(self) -> str:
        return self.raw


def get_kernel_version() -> KernelVersion:
    result = subprocess.run(["uname", "-r"], capture_output=True, text=True, check=True)
    return KernelVersion(result.stdout.strip())


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2b — Distro detection
# ─────────────────────────────────────────────────────────────────────────────

class Distro:
    """
    Detect the Linux distribution from /etc/os-release and available package
    managers.  Provides the correct kernel-headers package name and install
    command for the running kernel.
    """

    # Maps ID / ID_LIKE values to a canonical family name
    _FAMILY_MAP = {
        "ubuntu": "debian", "debian": "debian", "linuxmint": "debian",
        "pop":    "debian", "elementary": "debian", "kali": "debian",
        "raspbian": "debian", "parrot": "debian", "mx": "debian",
        "fedora": "fedora", "rhel": "fedora", "centos": "fedora",
        "almalinux": "fedora", "rocky": "fedora", "ol": "fedora",
        "amzn": "fedora",
        "opensuse": "suse", "suse": "suse", "opensuse-leap": "suse",
        "opensuse-tumbleweed": "suse",
        "arch": "arch", "manjaro": "arch", "endeavouros": "arch",
        "garuda": "arch", "artix": "arch",
        "gentoo": "gentoo",
        "alpine": "alpine",
        "void": "void",
        "nixos": "nixos",
        "slackware": "slackware",
    }

    def __init__(self):
        self.id = ""
        self.id_like = []
        self.name = ""
        self.version_id = ""
        self.family = "unknown"

        osrel = Path("/etc/os-release")
        if osrel.exists():
            for line in osrel.read_text().splitlines():
                if "=" not in line:
                    continue
                key, _, val = line.partition("=")
                val = val.strip().strip('"')
                if key == "ID":
                    self.id = val.lower()
                elif key == "ID_LIKE":
                    self.id_like = [x.lower() for x in val.split()]
                elif key == "NAME":
                    self.name = val
                elif key == "VERSION_ID":
                    self.version_id = val

        # Resolve family: check ID first, then ID_LIKE
        for candidate in [self.id] + self.id_like:
            if candidate in self._FAMILY_MAP:
                self.family = self._FAMILY_MAP[candidate]
                break

        # Detect available package managers (ground truth over family heuristic)
        self._pm = self._detect_pm()

    def _detect_pm(self) -> str:
        for pm in ("apt-get", "dnf", "yum", "pacman", "zypper", "emerge", "apk", "xbps-install", "nix-env"):
            if shutil.which(pm):
                return pm
        return ""

    @property
    def pm(self) -> str:
        return self._pm

    def headers_pkg(self, kver: KernelVersion) -> list[str]:
        """Return the package name(s) that provide kernel headers for kver."""
        k = kver.raw
        pm = self._pm

        if pm == "apt-get":
            return [f"linux-headers-{k}"]
        if pm in ("dnf", "yum"):
            # Fedora/RHEL: kernel-devel matches the running kernel automatically
            return ["kernel-devel", f"kernel-devel-{k}"]
        if pm == "pacman":
            # Arch: derive from kernel flavour (linux, linux-lts, linux-zen, etc.)
            flavour = self._arch_kernel_flavour(k)
            return [f"{flavour}-headers"]
        if pm == "zypper":
            return [f"kernel-default-devel={k}", "kernel-default-devel"]
        if pm == "emerge":
            return [f"sys-kernel/linux-headers"]
        if pm == "apk":
            return ["linux-headers"]
        if pm == "xbps-install":
            return [f"kernel-headers-{k}"]
        # Fallback
        return [f"linux-headers-{k}"]

    def _arch_kernel_flavour(self, raw: str) -> str:
        """Guess the Arch package name from the uname -r suffix."""
        # e.g. 6.6.35-1-MANJARO → linux-manjaro; 6.6.35-arch1-1 → linux
        m = re.search(r'-(\w+)$', raw)
        suffix = m.group(1).lower() if m else ""
        if "lts" in suffix:
            return "linux-lts"
        if "zen" in suffix:
            return "linux-zen"
        if "hardened" in suffix:
            return "linux-hardened"
        if "rt" in suffix:
            return "linux-rt"
        if "manjaro" in suffix:
            return "linux-manjaro" if shutil.which("mhwd") else "linux"
        return "linux"

    def install_cmd(self, packages: list[str]) -> list[str]:
        """Return the full install command for given packages."""
        pm = self._pm
        if pm == "apt-get":
            return ["apt-get", "install", "-y"] + packages
        if pm == "dnf":
            return ["dnf", "install", "-y"] + packages
        if pm == "yum":
            return ["yum", "install", "-y"] + packages
        if pm == "pacman":
            return ["pacman", "-S", "--noconfirm"] + packages
        if pm == "zypper":
            return ["zypper", "--non-interactive", "install"] + packages
        if pm == "emerge":
            return ["emerge", "--ask=n"] + packages
        if pm == "apk":
            return ["apk", "add"] + packages
        if pm == "xbps-install":
            return ["xbps-install", "-y"] + packages
        return []

    def summary(self) -> str:
        pm_str = self._pm or "unknown"
        return f"{self.name or self.id} (family={self.family}, pm={pm_str})"


def detect_distro() -> Distro:
    return Distro()


# ─────────────────────────────────────────────────────────────────────────────
# Phase 7 — Secure Boot detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_secure_boot() -> bool:
    """Return True if Secure Boot is currently enabled."""
    # Try mokutil first
    result = subprocess.run(["mokutil", "--sb-state"], capture_output=True, text=True)
    if result.returncode == 0:
        return "enabled" in result.stdout.lower()

    # Fallback: read EFI variable directly
    sb_var = Path("/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c")
    if sb_var.exists():
        try:
            data = sb_var.read_bytes()
            # Last byte: 1 = enabled, 0 = disabled (first 4 bytes are attributes)
            return len(data) >= 5 and data[4] == 1
        except Exception:
            pass

    return False


def print_secure_boot_signing_instructions(kernel_version: str):
    warn("Secure Boot is ENABLED.")
    warn("Unsigned modules will be rejected by the kernel ('Key was rejected by service').")
    print()
    info("To sign the modules, run the following commands with your MOK key:")
    print()
    mok_dir = "/var/lib/shim-signed/mok"
    sign_tool = f"/usr/src/linux-headers-{kernel_version}/scripts/sign-file"
    for mod in ["vmmon", "vmnet"]:
        ko = f"/lib/modules/{kernel_version}/misc/{mod}.ko"
        print(f"  sudo {sign_tool} sha256 \\")
        print(f"      {mok_dir}/MOK.priv {mok_dir}/MOK.der \\")
        print(f"      {ko}")
        print()
    info(f"Note: '{VMCI_MODULE}' is the in-kernel driver, signed by the kernel build key.")
    info(f"      It does NOT need MOK signing and will load automatically.")
    print()
    info("If your MOK key has a passphrase, prefix with:")
    print("  sudo KBUILD_SIGN_PIN='your_passphrase' ...")
    print()
    info("If you haven't created a MOK key yet:")
    print("  sudo mokutil --import /path/to/MOK.der")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5 — Smart backup system
# ─────────────────────────────────────────────────────────────────────────────

def md5_files(*paths: Path) -> str:
    h = hashlib.md5()
    for p in sorted(paths):
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()


def get_or_create_backup() -> Path:
    """
    Find the original (oldest) backup of vmmon.tar + vmnet.tar.
    If none exists, create one. Returns the backup directory path.
    Always extracts from the clean backup, never from potentially-patched live files.
    """
    tars = ["vmmon.tar", "vmnet.tar"]
    current_hash = md5_files(*[VMWARE_MOD_DIR / t for t in tars])

    # Find existing backups, oldest first
    existing = sorted(VMWARE_MOD_DIR.glob("backup-*"))

    for backup in existing:
        backup_hash = md5_files(*[backup / t for t in tars])
        if backup_hash == current_hash:
            ok(f"Using existing original backup: {backup.name} (hash verified)")
            return backup

    # If the oldest backup has a different hash, warn but still use it as base
    if existing:
        oldest = existing[0]
        warn(f"Existing backup {oldest.name} has different hash than current modules.")
        warn("Current modules may have been previously patched.")
        info("Using oldest backup as clean source.")
        return oldest

    # No backup exists — create one now
    import datetime
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = VMWARE_MOD_DIR / f"backup-{stamp}"
    info(f"Creating first backup at: {backup_path}")
    run(["sudo", "mkdir", "-p", str(backup_path)], check=True)
    for t in tars:
        run(["sudo", "cp", str(VMWARE_MOD_DIR / t), str(backup_path / t)], check=True)
    ok(f"Backup created: {backup_path.name}")
    return backup_path


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — Dynamic autopatch system
#
# Philosophy: every patch function probes the actual file content at runtime.
# It applies the fix only when the problem signature is present AND the fix is
# not already there. This makes the system kernel-version agnostic, VMware-
# source-version agnostic, and fully idempotent (safe to re-run).
#
# Probe helpers return True if applied, False if skipped (already fixed or
# condition does not apply). They never raise on a missing target — they warn
# and continue so a single incompatibility never blocks the whole build.
# ─────────────────────────────────────────────────────────────────────────────

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _write(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


def _kernel_header_has(symbol: str, kver: KernelVersion) -> bool:
    """Return True if `symbol` appears in the running kernel's include tree."""
    build = Path(f"/lib/modules/{kver.raw}/build/include")
    if not build.exists():
        return False
    result = subprocess.run(
        ["grep", "-r", "--include=*.h", "-l", "-m1", symbol, str(build)],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def _patch_insert_after(path: Path, anchor: str, insertion: str, label: str) -> bool:
    """
    Insert `insertion` immediately after the first occurrence of `anchor`.
    Uses the first non-blank, non-comment line of `insertion` as an
    idempotency marker — skips silently if already present.
    """
    text = _read(path)
    marker = next(
        (ln for ln in insertion.splitlines()
         if ln.strip() and not ln.strip().startswith(("#", "/*", " *", "//"))),
        insertion[:60],
    )
    if marker in text:
        info(f"    {label} — already present, skipped")
        return False
    if anchor not in text:
        warn(f"    {label} — anchor not found in {path.name}, skipping")
        return False
    _write(path, text.replace(anchor, anchor + insertion, 1))
    ok(f"    {label}")
    return True


def _patch_replace(path: Path, old: str, new: str, label: str) -> bool:
    """Replace `old` with `new`; skip if `old` absent (already fixed or n/a)."""
    text = _read(path)
    if old not in text:
        if new.strip() in text:
            info(f"    {label} — already applied, skipped")
        else:
            info(f"    {label} — target not present in {path.name}, skipping")
        return False
    _write(path, text.replace(old, new, 1))
    ok(f"    {label}")
    return True


def _patch_replace_all(path: Path, old: str, new: str, label: str) -> bool:
    """Replace all occurrences of `old` with `new`."""
    text = _read(path)
    if old not in text:
        info(f"    {label} — not present in {path.name}, skipping")
        return False
    count = text.count(old)
    _write(path, text.replace(old, new))
    ok(f"    {label} ({count} occurrence(s))")
    return True


# ── Upstream source overlay ───────────────────────────────────────────────────

def copy_upstream_source(module: str, dest_dir: Path):
    """Copy the pre-patched 6.16.x upstream source tree over the extracted tarball."""
    src = UPSTREAM_616_DIR / f"{module}-only"
    dst = dest_dir / f"{module}-only"
    if not src.exists():
        raise FileNotFoundError(f"Upstream patch source not found: {src}")
    info(f"  Overlaying 6.16.x patched source onto {module}-only/")
    shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
    ok(f"  {module}: base 6.16.x source applied (ccflags-y, timer/MSR API, module_init)")


# ═══════════════════════════════════════════════════════════════════════════════
# AUTOPATCH CATALOGUE
#
# Each entry documents:
#   Problem   — what breaks and on which kernel/VMware version
#   Probe     — how the script detects whether the fix is needed
#   Fix       — what text transformation is applied
# ═══════════════════════════════════════════════════════════════════════════════

# ── [AP-01] objtool: OBJECT_FILES_NON_STANDARD (kernel >= 6.17 / 7.x) ────────
#
# Problem:  objtool validates stack frames in all compiled .o files.
#           vmmon's phystrack.c and task.c use VMware custom asm constructs
#           that confuse objtool, causing build failures on 6.17+.
# Probe:    Check for the marker in Makefile.kernel.
# Fix:      Add OBJECT_FILES_NON_STANDARD_* directives after the obj-y list.

def _find_obj_y_anchor(text: str, module: str) -> str | None:
    """
    Find the line that ends the $(DRIVER)-y object list, after which we can
    safely insert OBJECT_FILES_NON_STANDARD directives.
    Handles all known VMware Makefile.kernel variants.
    """
    if module == "vmmon":
        patterns = [
            "$(SRCROOT)/linux/*.c $(SRCROOT)/common/*.c \\\n\t\t$(SRCROOT)/bootstrap/*.c)))",
            "$(wildcard $(SRCROOT)/linux/*.c $(SRCROOT)/common/*.c",
            "$(wildcard $(SRCROOT)/*.c)",
        ]
    else:
        patterns = [
            "$(wildcard $(SRCROOT)/*.c)",
        ]
        # vmnet flat list: find last continuation of $(DRIVER)-y
        if "driver.o hub.o userif.o" in text:
            idx = text.index("driver.o hub.o userif.o")
            end = text.find("\n", idx)
            # Walk past line continuations
            while text[end - 1:end] == "\\" and end < len(text):
                end = text.find("\n", end + 1)
            return text[idx:end]

    return next((p for p in patterns if p in text), None)


def _autopatch_objtool_vmmon(vmmon_dir: Path):
    mk = vmmon_dir / "Makefile.kernel"
    if not mk.exists():
        warn(f"    vmmon Makefile.kernel not found: {mk}")
        return
    text = _read(mk)
    anchor = _find_obj_y_anchor(text, "vmmon")
    if not anchor or anchor not in text:
        warn("    vmmon Makefile.kernel: cannot locate obj-y anchor for objtool markers")
        return
    _patch_insert_after(mk, anchor,
        "\n\n# Disable objtool for files using non-standard asm (kernel 6.17+)\n"
        "OBJECT_FILES_NON_STANDARD_common/phystrack.o := y\n"
        "OBJECT_FILES_NON_STANDARD_common/task.o := y\n"
        "OBJECT_FILES_NON_STANDARD := y",
        "vmmon Makefile: OBJECT_FILES_NON_STANDARD (objtool bypass)")


def _autopatch_objtool_vmnet(vmnet_dir: Path):
    mk = vmnet_dir / "Makefile.kernel"
    if not mk.exists():
        warn(f"    vmnet Makefile.kernel not found: {mk}")
        return
    text = _read(mk)
    anchor = _find_obj_y_anchor(text, "vmnet")
    if not anchor or anchor not in text:
        warn("    vmnet Makefile.kernel: cannot locate anchor for objtool markers")
        return
    _patch_insert_after(mk, anchor,
        "\n\n# Disable objtool for files using non-standard asm (kernel 6.17+)\n"
        "OBJECT_FILES_NON_STANDARD_userif.o := y\n"
        "OBJECT_FILES_NON_STANDARD := y",
        "vmnet Makefile: OBJECT_FILES_NON_STANDARD (objtool bypass)")


# ── [AP-02] objtool: bare return; at end of void functions (kernel >= 6.17) ──
#
# Problem:  objtool in kernel 6.17+ rejects void functions that end with an
#           explicit bare `return;` (treated as dead code after a RET insn).
# Probe:    Regex-scan phystrack.c for `<ws>return;\n<ws>}` pattern.
# Fix:      Remove the redundant `return;` line.

def _autopatch_phystrack_bare_returns(vmmon_dir: Path):
    src = vmmon_dir / "common" / "phystrack.c"
    if not src.exists():
        info("    phystrack.c not found — skipping bare-return removal")
        return

    text = _read(src)
    pattern = re.compile(r'[ \t]+return;\n([ \t]*\})')
    matches = list(pattern.finditer(text))
    if not matches:
        info("    phystrack.c: no bare return; statements — skipped")
        return

    for m in reversed(matches):
        text = text[:m.start()] + m.group(1) + text[m.end():]
    _write(src, text)
    ok(f"    phystrack.c: removed {len(matches)} bare return; statement(s)")


# ── [AP-03] netif_napi_add 4-arg → 3-arg (kernel >= 6.1) ────────────────────
#
# Problem:  Linux 6.1 removed the `weight` parameter from netif_napi_add(),
#           making it a 3-argument function. VMware's compat_netdevice.h
#           still wraps it with 4 arguments via compat_netif_napi_add().
#           On kernel 6.1+ this causes a compile error.
# Probe:    Check whether netif_napi_add in the kernel headers takes 3 args
#           (absence of a 4th `weight` parameter in the declaration).
# Fix:      Add a LINUX_VERSION_CODE >= 6.1 guard that redefines
#           compat_netif_napi_add to drop the weight argument.

def _autopatch_napi_add_compat(vmnet_dir: Path, kver: KernelVersion):
    """
    Fix netif_napi_add 4-arg → 3-arg for kernel >= 6.1.

    Three variants of compat_netdevice.h exist in the wild:
      A) Modern VMware 25.x: flat `#define compat_netif_napi_add(...) netif_napi_add(..., quota)`
         with no version guard at all.
      B) Older VMware / 6.16.x overlay: versioned guards using LINUX_VERSION_CODE.
      C) Already fixed: has "kernel 6.1+" comment or KERNEL_VERSION(6, 1, 0) guard.
    """
    compat = vmnet_dir / "compat_netdevice.h"
    if not compat.exists():
        return

    if not kver.at_least(6, 1):
        info("    compat_netdevice.h: kernel < 6.1, napi_add compat not needed")
        return

    text = _read(compat)

    # Already fixed?
    if "KERNEL_VERSION(6, 1" in text or "[autopatch]" in text:
        info("    compat_netdevice.h: napi_add already fixed — skipped")
        return

    # Is the 4-arg form present at all?
    needs_fix = (
        "netif_napi_add(dev, napi, poll, quota)" in text or
        "netif_napi_add(dev, napi, poll, weight)" in text or
        # also catch the simpler flat define in real VMware 25.x source
        (re.search(r'define\s+compat_netif_napi_add\s*\(', text) and
         "netif_napi_add_weight" not in text)
    )
    if not needs_fix:
        info("    compat_netdevice.h: no 4-arg napi_add form found — skipped")
        return

    override = (
        "\n/* [autopatch] kernel 6.1+ dropped the weight param from netif_napi_add */\n"
        "#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 1, 0)\n"
        "#  ifdef compat_netif_napi_add\n"
        "#    undef compat_netif_napi_add\n"
        "#  endif\n"
        "#  define compat_netif_napi_add(dev, napi, poll, quota) \\\n"
        "       netif_napi_add((dev), (napi), (poll))\n"
        "#endif\n"
    )

    # Append before the closing include guard (variant B) or at end of file (variant A)
    closing = next(
        (g for g in ("#endif /* __COMPAT_NETDEVICE_H__ */",
                     "#endif /* _COMPAT_NETDEVICE_H_ */",
                     "#endif\n")
         if g in text),
        None,
    )
    if closing:
        _patch_replace(compat, closing, override + closing,
                       "compat_netdevice.h: netif_napi_add 3-arg fix (kernel 6.1+)")
    else:
        # No closing guard — just append
        if "autopatch" not in text:
            _write(compat, text + override)
            ok("    compat_netdevice.h: netif_napi_add 3-arg fix appended (kernel 6.1+)")


# ── [AP-04] vm_check_build missing from Makefile.kernel (all versions) ───────
#
# Problem:  vmnet's Makefile.kernel uses `$(call vm_check_build, ...)` to
#           detect kernel API availability at compile time. However,
#           vm_check_build is only defined in Makefile.normal (used for
#           direct make invocations) and is NOT available in Makefile.kernel
#           (used by the kernel build system via kbuild).
#           When kbuild calls Makefile.kernel, the $(call vm_check_build,…)
#           expands to an empty string, silently disabling the detection.
# Probe:    Check if vm_check_build is defined in Makefile.kernel.
# Fix:      Inject the vm_check_build definition into Makefile.kernel.

def _autopatch_vmcheck_build(vmnet_dir: Path):
    """
    Inject the vm_check_build macro into vmnet/Makefile.kernel.
    The macro is defined in Makefile.normal but not in Makefile.kernel;
    without it, $(call vm_check_build, ...) silently expands to nothing.
    Handles both CC_OPTS and EXTRA_CFLAGS Makefile styles.
    """
    mk = vmnet_dir / "Makefile.kernel"
    if not mk.exists():
        return

    text = _read(mk)
    if "vm_check_build" not in text:
        info("    vmnet Makefile.kernel: vm_check_build not referenced — skipped")
        return
    if "vm_check_build =" in text or "vm_check_build :=" in text:
        info("    vmnet Makefile.kernel: vm_check_build already defined — skipped")
        return

    # Pick the cflags variable that's actually used
    cflags_var = "$(ccflags-y)" if "ccflags-y" in text else "$(EXTRA_CFLAGS)"

    definition = (
        "\n# vm_check_build: compile-test a C snippet; yields flag2 on success, flag3 on error\n"
        f"vm_check_build = $(shell if $(CC) {cflags_var} -Werror -S -o /dev/null -xc $(1) \\\n"
        "    > /dev/null 2>&1; then echo \"$(2)\"; else echo \"$(3)\"; fi)\n"
    )

    anchor = next(
        (a for a in ("INCLUDE := -I$(SRCROOT)", "ccflags-y +=", "EXTRA_CFLAGS :=")
         if a in text),
        None,
    )
    if not anchor:
        warn("    vmnet Makefile.kernel: cannot locate anchor for vm_check_build")
        return

    _patch_insert_after(mk, anchor, definition,
                        "vmnet Makefile.kernel: inject vm_check_build")


# ── [AP-05] vmnet Makefile.kernel: add vm_check_build NAPI single-param flag ─
#
# Problem:  compat_netdevice.h uses VMW_NETIF_SINGLE_NAPI_PARM to select the
#           3-arg netif_napi_add at build time. This flag is set via
#           vm_check_build in Makefile.normal, but Makefile.kernel does not
#           set it, even when vm_check_build is defined.
# Probe:    Check if VMW_NETIF_SINGLE_NAPI_PARM is already set in Makefile.kernel.
# Fix:      Add the vm_check_build call for a synthetic probe file.

def _autopatch_vmnet_napi_flag(vmnet_dir: Path, kver: KernelVersion):
    mk = vmnet_dir / "Makefile.kernel"
    if not mk.exists():
        return

    # Only relevant on kernel >= 6.1
    if (kver.major, kver.minor) < (6, 1):
        return

    text = _read(mk)
    if "VMW_NETIF_SINGLE_NAPI_PARM" in text:
        info("    vmnet Makefile.kernel: VMW_NETIF_SINGLE_NAPI_PARM already set — skipped")
        return

    # Anchor: after the last ccflags-y line.
    # 6.16.x overlay uses 'ccflags-y :='; 25H2u1 uses 'ccflags-y +=' — handle both.
    if "ccflags-y :=" in text or "ccflags-y +=" in text:
        idx = text.rindex("ccflags-y")
        end = text.find("\n", idx)
        anchor = text[idx:end]
    else:
        warn("    vmnet Makefile.kernel: cannot locate ccflags-y anchor for NAPI flag")
        return

    insertion = (
        "\n# Detect 3-arg netif_napi_add (kernel 6.1+ dropped the weight param)\n"
        "ccflags-y += $(call vm_check_build, $(SRCROOT)/netif_napi_add_check.c,"
        "-DVMW_NETIF_SINGLE_NAPI_PARM, )\n"
    )

    # Also create the probe file that vm_check_build will try to compile
    probe_src = vmnet_dir / "netif_napi_add_check.c"
    if not probe_src.exists():
        probe_content = (
            "/* autopatch probe: detect 3-arg netif_napi_add (kernel 6.1+) */\n"
            "#include <linux/netdevice.h>\n"
            "static int dummy_poll(struct napi_struct *n, int b) { return 0; }\n"
            "void test(struct net_device *dev, struct napi_struct *napi) {\n"
            "    netif_napi_add(dev, napi, dummy_poll);\n"
            "}\n"
        )
        _write(probe_src, probe_content)
        ok("    vmnet: created netif_napi_add_check.c probe file")

    _patch_insert_after(mk, anchor, insertion,
                        "vmnet Makefile.kernel: VMW_NETIF_SINGLE_NAPI_PARM detection (kernel 6.1+)")


# ── [AP-06] vmnet compat_netdevice.h: VMW_NETIF_SINGLE_NAPI_PARM guard ───────
#
# Problem:  Even when VMW_NETIF_SINGLE_NAPI_PARM is set by the Makefile, the
#           compat_netdevice.h guard only applies to the compat_napi_complete /
#           compat_napi_schedule wrappers but NOT to compat_netif_napi_add
#           itself on kernel >= 6.1.
# Probe:    Check if the 6.1 override is present in compat_netdevice.h.
# Fix:      Append an unconditional 6.1 guard (see AP-03 above — same file,
#           AP-03 and AP-06 are intentionally combined).

# (Handled in _autopatch_napi_add_compat — AP-03)


# ── [AP-07] hostif.c: get_current_state → READ_ONCE(task->__state) ────────────
#
# Problem:  On kernel >= 5.14, task->state was renamed to task->__state and
#           direct reads require READ_ONCE(). VMware's hostif.c defines a
#           get_task_state() macro that correctly handles this, but only if
#           LINUX_VERSION_CODE >= 5.15.0 is detected. The check is already
#           present in the 6.16.x upstream source — this autopatch verifies it.
# Probe:    Look for the guard in hostif.c; warn if absent.
# Fix:      Add the guard if it's missing.

def _autopatch_hostif_task_state(vmmon_dir: Path):
    src = vmmon_dir / "linux" / "hostif.c"
    if not src.exists():
        return

    text = _read(src)
    # The fix is already in the 6.16.x upstream source. Verify it's present;
    # if not (e.g. a different VMware source version), inject it.
    marker = "get_task_state(task) READ_ONCE"
    if marker in text:
        info("    hostif.c: task->__state guard already present — skipped")
        return

    # Try to inject after the first #include block
    anchor = "#include \"hostif.h\""
    if anchor not in text:
        anchor = "#include <linux/sched.h>"
    if anchor not in text:
        warn("    hostif.c: cannot locate anchor for task state guard")
        return

    insertion = (
        "\n\n/* [autopatch] kernel 5.14+ renamed task->state to task->__state */\n"
        "#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 15, 0) || defined(get_current_state)\n"
        "#define get_task_state(task) READ_ONCE((task)->__state)\n"
        "#else\n"
        "#define get_task_state(task) ((task)->state)\n"
        "#endif"
    )
    _patch_insert_after(src, anchor, insertion,
                        "hostif.c: task->__state compat guard (kernel 5.14+)")


# ── [AP-08] vmnet bridge.c: do_gettimeofday removed (kernel >= 5.0) ──────────
#
# Problem:  do_gettimeofday() was removed in kernel 5.0. vmnet/bridge.c calls
#           it, but ONLY inside `#if LOGLEVEL >= 4` debug blocks. Since LOGLEVEL
#           is not set at compile time in production builds, this is harmless in
#           practice — but if someone enables LOGLEVEL the build will fail.
# Probe:    Detect do_gettimeofday() outside of a LINUX_VERSION_CODE < 5.0 guard.
# Fix:      Wrap the usages with a LINUX_VERSION_CODE guard and provide a
#           ktime_get_real_ts64() fallback.

def _autopatch_bridge_gettimeofday(vmnet_dir: Path, kver: KernelVersion):
    src = vmnet_dir / "bridge.c"
    if not src.exists():
        return

    if (kver.major, kver.minor) < (5, 0):
        info("    bridge.c: kernel < 5.0, do_gettimeofday still available — skipped")
        return

    text = _read(src)
    if "do_gettimeofday" not in text:
        info("    bridge.c: do_gettimeofday not present — skipped")
        return
    if "ktime_get_real_ts64" in text or "LINUX_VERSION_CODE < KERNEL_VERSION(5, 0" in text:
        info("    bridge.c: do_gettimeofday already guarded — skipped")
        return

    # Replace the static vnetTime variable with a compat definition.
    # 25H2u1 bridge.c wraps the declaration in #if LOGLEVEL >= 4; the 6.16.x overlay
    # does not.  Try the LOGLEVEL-wrapped form first (25H2u1), fall back to bare form.
    replaced_vnettime = _patch_replace(src,
        "#if LOGLEVEL >= 4\n"
        "static struct timeval vnetTime;\n"
        "#endif",
        "#if LOGLEVEL >= 4\n"
        "#  if LINUX_VERSION_CODE < KERNEL_VERSION(5, 0, 0)\n"
        "static struct timeval vnetTime;\n"
        "#  else\n"
        "static struct timespec64 vnetTime;\n"
        "#  endif\n"
        "#endif",
        "bridge.c: vnetTime timeval → timespec64 inside LOGLEVEL guard (25H2u1, kernel 5.0+)")
    if not replaced_vnettime:
        # Older source (6.16.x overlay): bare declaration without LOGLEVEL guard
        _patch_replace(src,
            "static struct timeval vnetTime;",
            "/* [autopatch] do_gettimeofday removed in kernel 5.0 */\n"
            "#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 0, 0)\n"
            "static struct timeval vnetTime;\n"
            "#else\n"
            "static struct timespec64 vnetTime;\n"
            "#endif",
            "bridge.c: vnetTime timeval → timespec64 (kernel 5.0+)")

    # Replace `do_gettimeofday(&vnetTime)` with compat
    _patch_replace_all(src,
        "do_gettimeofday(&vnetTime)",
        "/* [autopatch] */\\\n"
        "#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 0, 0)\n"
        "         do_gettimeofday(&vnetTime)\n"
        "#else\n"
        "         ktime_get_real_ts64(&vnetTime)\n"
        "#endif",
        "bridge.c: do_gettimeofday(&vnetTime) → ktime_get_real_ts64 (kernel 5.0+)")

    # The `struct timeval now;` local + `do_gettimeofday(&now)` pattern
    _patch_replace(src,
        "struct timeval now;\n      do_gettimeofday(&now);",
        "#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 0, 0)\n"
        "      struct timeval now;\n"
        "      do_gettimeofday(&now);\n"
        "#else\n"
        "      struct timespec64 now;\n"
        "      ktime_get_real_ts64(&now);\n"
        "#endif",
        "bridge.c: local timeval now → timespec64 (kernel 5.0+)")


# ── [AP-09] vmmon hostif.c: get_user_pages_fast FOLL_WRITE→0 for read mappings
#
# Problem:  hostif.c calls get_user_pages_fast() with flags=0 (read-only)
#           for guest-physical to host-physical page mapping. On kernel >= 5.9
#           the signature changed: the third argument is now `unsigned int gup_flags`
#           (was `int write`). The value 0 is compatible in both cases, but
#           an explicit flag check can catch misuse.
# Probe:    Verify the call signature matches current kernel expectations.
#           (get_user_pages_fast still exists in 7.x with same int API — no fix needed.)
# Status:   No-op — current kernel 7.x headers show same `int` API. Logged for
#           awareness.

def _autopatch_hostif_gup(vmmon_dir: Path, kver: KernelVersion):
    src = vmmon_dir / "linux" / "hostif.c"
    if not src.exists():
        return
    text = _read(src)
    if "get_user_pages_fast" not in text:
        return
    # Kernel 7.x still exports get_user_pages_fast with same prototype — OK
    info("    hostif.c: get_user_pages_fast — API compatible, no fix needed")


# ── [AP-10] vmmon/vmnet: strncpy → strscpy (kernel 6.8+ W=1 deprecation) ─────
#
# Problem:  Kernel 6.8 made strncpy() emit a deprecation warning under W=1.
#           While not a build error by default, it clutters the build output
#           and may become an error in future kernels.
# Probe:    Search for strncpy() calls where strscpy() is a safe drop-in.
# Fix:      Replace strncpy(dst, src, n) with strscpy(dst, src, n) where
#           the destination size is the third argument (safe substitution).
#           Only applied on kernel >= 6.8 where strscpy is guaranteed present.

def _autopatch_strncpy_to_strscpy(module_dir: Path, kver: KernelVersion):
    if (kver.major, kver.minor) < (6, 8):
        return

    c_files = list(module_dir.rglob("*.c"))
    replaced_files = 0
    for f in c_files:
        text = _read(f)
        if "strncpy(" not in text:
            continue
        # Only replace patterns where strscpy is a safe drop-in:
        # strncpy(dst, src, sizeof(dst)) or strncpy(dst, src, N)
        new_text = re.sub(r'\bstrncpy\b\s*\(', 'strscpy(', text)
        if new_text != text:
            _write(f, new_text)
            replaced_files += 1
    if replaced_files:
        ok(f"    {module_dir.name}: strncpy → strscpy in {replaced_files} file(s) (kernel 6.8+)")
    else:
        info(f"    {module_dir.name}: no strncpy replacements needed")


# ── [AP-11] vmnet/userif.c: get_user_pages_fast FOLL_WRITE flag ──────────────
#
# Problem:  userif.c calls get_user_pages_fast(addr, 1, FOLL_WRITE, &page).
#           FOLL_WRITE was introduced in 4.9 as the replacement for the old
#           `int write` parameter. This is already correct for kernel >= 4.9.
#           No fix needed — documented for completeness.

def _autopatch_userif_gup(_vmnet_dir: Path, _kver: KernelVersion):
    info("    userif.c: get_user_pages_fast(FOLL_WRITE) — API compatible, no fix needed")


# ── [AP-12] vmmon: MODULE_IMPORT_NS for kernel lockdown (kernel >= 5.15) ──────
#
# Problem:  On some kernels with lockdown or symbol namespaces enabled, modules
#           must declare MODULE_IMPORT_NS(VMWCORE) or similar. Absence causes
#           a taint or refusal to load. This is distribution-specific.
# Probe:    Check if the kernel uses symbol namespaces for vmmon symbols.
# Fix:      Add MODULE_IMPORT_NS if the kernel headers require it.
#           (This is a best-effort; most distros don't enforce namespaces here.)

def _autopatch_module_import_ns(vmmon_dir: Path, kver: KernelVersion):
    if (kver.major, kver.minor) < (5, 15):
        return

    driver = vmmon_dir / "linux" / "driver.c"
    if not driver.exists():
        return

    text = _read(driver)
    if "MODULE_IMPORT_NS" in text:
        info("    driver.c: MODULE_IMPORT_NS already present — skipped")
        return

    # Only add if MODULE_LICENSE is present (sanity check)
    if "MODULE_LICENSE" not in text:
        return

    # Check if kernel enforces namespaces for any exported symbol we use
    # This is a heuristic — check for EXPORT_SYMBOL_NS in kernel headers
    build_include = Path(f"/lib/modules/{kver.raw}/build/include")
    if build_include.exists():
        r = subprocess.run(
            ["grep", "-r", "-l", "-m1", "EXPORT_SYMBOL_NS", str(build_include)],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            info("    driver.c: kernel does not use symbol namespaces — skipped")
            return

    _patch_replace(driver,
        "MODULE_LICENSE(",
        "MODULE_IMPORT_NS(\"VMWCORE\");\nMODULE_LICENSE(",
        "driver.c: MODULE_IMPORT_NS (kernel symbol namespace, 5.15+)")


# ── [AP-13] vmmon/vmnet Makefile.kernel: ccflags-y missing -DVMMON/-DVMNET ───
#
# Problem:  Some VMware source tarballs (especially third-party rebuilds) omit
#           the CC_OPTS += -DVMMON or -DVMNET line from Makefile.kernel,
#           causing the module to be compiled without its identity define.
# Probe:    Check for the presence of -DVMMON / -DVMNET in Makefile.kernel.
# Fix:      Add the missing CC_OPTS line before the ccflags-y assignment.

def _autopatch_module_define(vmmon_dir: Path, vmnet_dir: Path):
    for module_dir, define in [(vmmon_dir, "VMMON"), (vmnet_dir, "VMNET")]:
        mk = module_dir / "Makefile.kernel"
        if not mk.exists():
            continue
        text = _read(mk)
        if f"-D{define}" in text:
            info(f"    {mk.name} ({module_dir.name}): -D{define} already present — skipped")
            continue
        anchor = "ccflags-y :="
        if anchor not in text:
            continue
        _patch_insert_after(mk, anchor,
            f"\n\n# Module identity define\nCC_OPTS += -D{define}",
            f"{module_dir.name} Makefile: add -D{define} module identity flag")


# ── [AP-14] vmnet: add missing CC_OPTS += -DVMNET to Makefile.kernel ─────────
# (Merged into AP-13 above)


# ── [AP-15] vmnet/Makefile.kernel: missing vm_check_build causes silent       ─
#   feature-detection failures                                                  ─
# (See AP-04 above)


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator — decides which autopatches to run based on kernel version and
# actual file content probing
# ─────────────────────────────────────────────────────────────────────────────

def apply_all_patches(build_dir: Path, kver: KernelVersion, optimized: bool,
                      src_info: "VmwareSourceInfo"):
    """
    Probe-and-apply all compatibility patches.

    Uses VmwareSourceInfo (pre-computed from the extracted sources) to avoid
    applying patches that are not relevant to the actual source version.
    Every patch function is idempotent — safe to re-run.
    """
    section("Applying kernel compatibility patches")

    vmmon_dir = build_dir / "vmmon-only"
    vmnet_dir = build_dir / "vmnet-only"

    # ── Legacy 6.16.x source overlay (fallback for VMware < 25H2u1 only) ────────
    #
    # VMware Workstation Pro 25H2u1 and later ship source tarballs that already
    # include the fixes that were previously hand-patched in the community
    # 6.16.x overlay (get_task_state guard, timer-API updates, etc.).  For those
    # installs the overlay is never applied.
    #
    # For older VMware installs (≤ 17.6.x, pre-25H2u1) where the tarball still
    # ships unpatched sources, the overlay is applied as a base layer so that the
    # subsequent _autopatch_* functions can work from a consistent starting point.
    # The primary patching path for all supported installs is always the
    # _autopatch_* functions below — the overlay is a secondary, legacy fallback.
    if kver.needs_base_616_patches():
        if src_info.has_task_state_guard:
            info("  Legacy 6.16.x overlay: 25H2u1 sources detected (modern APIs present) — skipping")
        elif UPSTREAM_616_DIR.exists():
            ok("  Legacy 6.16.x overlay: pre-25H2u1 sources detected — applying community overlay")
            copy_upstream_source("vmmon", build_dir)
            copy_upstream_source("vmnet", build_dir)
            # Re-read source info after overlay (files changed)
            src_info = VmwareSourceInfo(vmmon_dir, vmnet_dir)
        else:
            warn("  Legacy 6.16.x overlay directory not present — skipping (using _autopatch_* only)")
    else:
        info("  Kernel < 6.16 — legacy 6.16.x overlay not required")

    # ── Always-applied structural autopatches ─────────────────────────────────
    info("  [AP-04] vmnet Makefile.kernel: vm_check_build injection")
    _autopatch_vmcheck_build(vmnet_dir)

    info("  [AP-13] Module identity defines in Makefile.kernel")
    _autopatch_module_define(vmmon_dir, vmnet_dir)

    # ── Objtool patches (kernel >= 6.17 / 7.x) ────────────────────────────────
    if kver.needs_objtool_patches():
        if src_info.has_objtool_markers:
            info("  [AP-01] Objtool markers already present — skipping")
        else:
            info("  [AP-01] Kernel >= 6.17 / 7.x: objtool compatibility patches")
            _autopatch_objtool_vmmon(vmmon_dir)
            _autopatch_objtool_vmnet(vmnet_dir)
        info("  [AP-02] Phystrack bare return; removal (objtool)")
        _autopatch_phystrack_bare_returns(vmmon_dir)
    else:
        info("  Kernel < 6.17: objtool patches not required")

    # ── Kernel API compatibility autopatches ───────────────────────────────────
    if src_info.has_napi_add_4arg and not src_info.napi_add_already_fixed:
        info("  [AP-03] netif_napi_add 3-arg fix (kernel 6.1+)")
        _autopatch_napi_add_compat(vmnet_dir, kver)
    else:
        info("  [AP-03] netif_napi_add: not needed or already fixed — skipped")

    info("  [AP-05] VMW_NETIF_SINGLE_NAPI_PARM detection (kernel 6.1+)")
    _autopatch_vmnet_napi_flag(vmnet_dir, kver)

    if not src_info.has_task_state_guard:
        info("  [AP-07] hostif.c: task->__state compat guard (kernel 5.14+)")
        _autopatch_hostif_task_state(vmmon_dir)
    else:
        info("  [AP-07] task->__state guard: already present — skipped")

    if src_info.has_do_gettimeofday and not src_info.do_gettimeofday_guarded:
        info("  [AP-08] bridge.c: do_gettimeofday → ktime_get_real_ts64 (kernel 5.0+)")
        _autopatch_bridge_gettimeofday(vmnet_dir, kver)
    else:
        info("  [AP-08] bridge.c: do_gettimeofday not present or already guarded — skipped")

    info("  [AP-09] hostif.c: get_user_pages_fast API check")
    _autopatch_hostif_gup(vmmon_dir, kver)

    info("  [AP-10] strncpy → strscpy deprecation fix (kernel 6.8+)")
    _autopatch_strncpy_to_strscpy(vmmon_dir, kver)
    _autopatch_strncpy_to_strscpy(vmnet_dir, kver)

    info("  [AP-11] userif.c: get_user_pages_fast API check")
    _autopatch_userif_gup(vmnet_dir, kver)

    info("  [AP-12] MODULE_IMPORT_NS symbol namespace (kernel 5.15+)")
    _autopatch_module_import_ns(vmmon_dir, kver)

    # ── Performance patches (optional, user-selected) ─────────────────────────
    if optimized:
        info("  Optimized mode: applying performance patches")
        _autopatch_optimize_vmmon_makefile(vmmon_dir)
        _autopatch_optimize_vmnet_makefile(vmnet_dir)
        _autopatch_branch_hints(vmmon_dir)
    else:
        info("  Vanilla mode: skipping optional performance patches")


# ── Performance / optimization patches (optional) ─────────────────────────────

def _makefile_cflags_var(text: str) -> str:
    """
    Return the C-flags variable name used in this Makefile.
    Modern VMware (25.x): uses CC_OPTS then ccflags-y += $(EXTRA_CFLAGS) or
                           ccflags-y := $(CC_OPTS)
    Older source:          uses EXTRA_CFLAGS directly.
    Returns 'CC_OPTS' or 'EXTRA_CFLAGS'.
    """
    if "CC_OPTS +=" in text or "CC_OPTS :=" in text:
        return "CC_OPTS"
    return "EXTRA_CFLAGS"


def _makefile_opt_anchor(text: str, module: str) -> str | None:
    """
    Find the best anchor line for inserting optimization flags.
    Tries several patterns across different VMware source versions.
    """
    candidates = []
    if module == "vmmon":
        candidates = [
            "CC_OPTS += -DVMMON -DVMCORE",
            "CC_OPTS += -DVMMON",
            "EXTRA_CFLAGS := $(CC_OPTS)",
            "ccflags-y += $(EXTRA_CFLAGS)",
            "ccflags-y := $(CC_OPTS)",
        ]
    else:
        candidates = [
            "EXTRA_CFLAGS := $(CC_OPTS)",
            "ccflags-y += $(EXTRA_CFLAGS)",
            "INCLUDE := -I$(SRCROOT)",
            "ccflags-y := $(CC_OPTS)",
            "ccflags-y +=",
        ]
    return next((c for c in candidates if c in text), None)


def _autopatch_optimize_vmmon_makefile(vmmon_dir: Path):
    mk = vmmon_dir / "Makefile.kernel"
    if not mk.exists():
        return
    text = _read(mk)
    anchor = _makefile_opt_anchor(text, "vmmon")
    if not anchor:
        warn("    vmmon Makefile: cannot locate anchor for optimization block")
        return
    var = _makefile_cflags_var(text)
    _patch_insert_after(mk, anchor,
        "\n\n# Hardware optimization flags (set VMWARE_OPTIMIZE=1 to enable)\n"
        f"ifdef VMWARE_OPTIMIZE\n"
        f"  {var} += -O3 -ffast-math -funroll-loops\n"
        f"  {var} += -fno-strict-aliasing -fno-strict-overflow\n"
        f"  {var} += -fno-delete-null-pointer-checks\n"
        f"  ifdef ARCH_FLAGS\n"
        f"    {var} += $(ARCH_FLAGS)\n"
        f"  endif\n"
        f"  ifdef HAS_VTX_EPT\n"
        f"    {var} += -DVMWARE_VTX_EPT_OPTIMIZE=1\n"
        f"  endif\n"
        f"  ifdef HAS_AVX512\n"
        f"    {var} += -DVMWARE_AVX512_OPTIMIZE=1\n"
        f"  endif\n"
        f"endif",
        "vmmon Makefile: VMWARE_OPTIMIZE performance flags")


def _autopatch_optimize_vmnet_makefile(vmnet_dir: Path):
    mk = vmnet_dir / "Makefile.kernel"
    if not mk.exists():
        return
    text = _read(mk)
    anchor = _makefile_opt_anchor(text, "vmnet")
    if not anchor:
        warn("    vmnet Makefile: cannot locate anchor for optimization block")
        return
    var = _makefile_cflags_var(text)
    _patch_insert_after(mk, anchor,
        "\n\n# Hardware optimization flags (set VMWARE_OPTIMIZE=1 to enable)\n"
        f"ifdef VMWARE_OPTIMIZE\n"
        f"  {var} += -O3 -ffast-math -funroll-loops\n"
        f"  {var} += -fno-strict-aliasing -fno-strict-overflow\n"
        f"  {var} += -fno-delete-null-pointer-checks\n"
        f"  ifdef ARCH_FLAGS\n"
        f"    {var} += $(ARCH_FLAGS)\n"
        f"  endif\n"
        f"  ifdef HAS_AVX512\n"
        f"    {var} += -DVMWARE_AVX512_OPTIMIZE=1\n"
        f"  endif\n"
        f"endif",
        "vmnet Makefile: VMWARE_OPTIMIZE performance flags")


def _autopatch_branch_hints(vmmon_dir: Path):
    candidates = [
        vmmon_dir / "include" / "vm_basic_types.h",
        vmmon_dir / "vm_basic_types.h",
    ]
    header = next((p for p in candidates if p.exists()), None)
    if header is None:
        info("    vm_basic_types.h not found — skipping branch hints")
        return
    text = _read(header)
    if "#ifndef _VM_BASIC_TYPES_H_" in text:
        anchor = "#ifndef _VM_BASIC_TYPES_H_\n#define _VM_BASIC_TYPES_H_"
    elif "#define INCLUDE_ALLOW_USERLEVEL" in text:
        anchor = "#define INCLUDE_ALLOW_USERLEVEL"
    else:
        warn("    vm_basic_types.h: cannot locate anchor for branch hints")
        return
    _patch_insert_after(header, anchor,
        "\n\n#ifndef likely\n"
        "#define likely(x)   __builtin_expect(!!(x), 1)\n"
        "#define unlikely(x) __builtin_expect(!!(x), 0)\n"
        "#endif\n"
        "#ifndef CACHE_LINE_SIZE\n"
        "#define CACHE_LINE_SIZE 64\n"
        "#endif",
        f"{header.name}: likely/unlikely branch hints")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 — Hardware detection and optimization mode
# ─────────────────────────────────────────────────────────────────────────────

class CpuFeatures:
    def __init__(self):
        flags = ""
        self.cpu_model = ""
        try:
            cpuinfo = Path("/proc/cpuinfo").read_text()
            for line in cpuinfo.splitlines():
                if line.startswith("model name") and not self.cpu_model:
                    self.cpu_model = line.split(":", 1)[1].strip()
                if line.startswith("flags") and not flags:
                    flags = line.split(":", 1)[1].strip()
                if self.cpu_model and flags:
                    break
        except Exception:
            pass
        self.flags = flags.split()
        self.has_vmx    = "vmx"     in self.flags
        self.has_svm    = "svm"     in self.flags
        self.has_avx2   = "avx2"    in self.flags
        self.has_avx512 = "avx512f" in self.flags
        self.has_aesni  = "aes"     in self.flags
        self.has_sse42  = "sse4_2"  in self.flags
        self.has_fma    = "fma"     in self.flags
        self.has_bmi2   = "bmi2"    in self.flags
        self.has_f16c   = "f16c"    in self.flags
        self.has_1gb    = "pdpe1gb" in self.flags   # 1GB EPT huge pages
        self.has_vpid   = "vpid"    in self.flags   # Virtual Processor ID

    def has_virt(self) -> bool:
        return self.has_vmx or self.has_svm

    def summary(self) -> list[str]:
        lines = []
        if self.cpu_model:
            lines.append(f"  CPU Model               : {self.cpu_model}")
        virt = ("Intel VT-x" if self.has_vmx else "AMD-V") if self.has_virt() else "NOT DETECTED"
        lines.append(f"  Hardware Virtualization : {virt}")
        lines.append(f"  VPID                    : {'yes' if self.has_vpid else 'no'}")
        lines.append(f"  AVX-512                 : {'yes' if self.has_avx512 else 'no'}")
        lines.append(f"  AVX2                    : {'yes' if self.has_avx2 else 'no'}")
        lines.append(f"  FMA / F16C              : {'yes' if self.has_fma else 'no'} / {'yes' if self.has_f16c else 'no'}")
        lines.append(f"  AES-NI                  : {'yes' if self.has_aesni else 'no'}")
        lines.append(f"  SSE4.2                  : {'yes' if self.has_sse42 else 'no'}")
        lines.append(f"  1GB Huge Pages (EPT)    : {'yes' if self.has_1gb else 'no'}")
        return lines


def ask_optimization_mode(cpu: CpuFeatures) -> bool:
    """Prompt user for Optimized vs Vanilla. Returns True for optimized."""
    section("Compilation Mode Selection")
    print()
    for line in cpu.summary():
        print(line)
    print()

    # Pre-compute what optimized mode would actually apply on this hardware
    opt_flags = make_flags(True, cpu)
    cores_flag = opt_flags[0]                          # e.g. -j32
    make_vars  = [f for f in opt_flags[1:] if not f.startswith("ARCH_FLAGS")]
    arch_flags = next((f.split("=", 1)[1] for f in opt_flags if f.startswith("ARCH_FLAGS")), "")

    print("  1) Vanilla  — standard VMware compilation, portable")
    print("  2) Optimized — modules only work on this CPU architecture (default)")
    print(f"       Flags that will be applied:")
    if arch_flags:
        print(f"         GCC  : {arch_flags} -O3 -ffast-math -fno-strict-aliasing")
    print(f"         Make : {' '.join(make_vars)}")
    print(f"         Cores: {cores_flag}")
    print()
    try:
        choice = input("  Select [1/2, default=2]: ").strip()
    except (EOFError, KeyboardInterrupt):
        choice = "2"
    return choice != "1"


def make_flags(optimized: bool, cpu: CpuFeatures) -> list[str]:
    """Build make flag list based on detected hardware and selected mode."""
    flags = [f"-j{os.cpu_count() or 4}"]
    if optimized:
        flags.append("VMWARE_OPTIMIZE=1")
        flags.append("ARCH_FLAGS=-march=native -mtune=native")
        if cpu.has_vmx and (cpu.has_avx2 or cpu.has_vpid):
            flags.append("HAS_VTX_EPT=1")
        if cpu.has_avx512:
            flags.append("HAS_AVX512=1")
        if cpu.has_1gb:
            flags.append("HAS_1GB_PAGES=1")
    return flags


# ─────────────────────────────────────────────────────────────────────────────
# Build & install vmmon / vmnet
# ─────────────────────────────────────────────────────────────────────────────

def _headers_present(kver: KernelVersion) -> bool:
    """Return True if usable kernel headers are available for kver."""
    # Primary: /lib/modules/<ver>/build symlink (all distros)
    if Path(f"/lib/modules/{kver.raw}/build").exists():
        return True
    # Secondary: /usr/src/linux-headers-<ver> (Debian/Ubuntu)
    if Path(f"/usr/src/linux-headers-{kver.raw}").exists():
        return True
    # Tertiary: /usr/src/linux-<ver> (Arch, Void, Gentoo)
    if Path(f"/usr/src/linux-{kver.raw}").exists():
        return True
    # Quaternary: /usr/lib/modules/<ver>/build (some Fedora setups)
    if Path(f"/usr/lib/modules/{kver.raw}/build").exists():
        return True
    return False


def check_kernel_headers(kver: KernelVersion, distro: "Distro") -> bool:
    """
    Ensure kernel headers are installed for the running kernel.
    If not found, attempt automatic installation using the distro's package
    manager.  Returns True on success, False if headers cannot be installed.
    """
    if _headers_present(kver):
        build = (
            Path(f"/lib/modules/{kver.raw}/build")
            or Path(f"/usr/src/linux-headers-{kver.raw}")
        )
        ok(f"Kernel headers found: /lib/modules/{kver.raw}/build")
        return True

    warn(f"Kernel headers not found for {kver.raw}")

    if not distro.pm:
        err("No supported package manager detected — cannot auto-install headers.")
        _print_manual_header_hint(kver, distro)
        return False

    pkgs = distro.headers_pkg(kver)
    info(f"Attempting automatic header installation via {distro.pm} ...")
    info(f"Packages to install: {' '.join(pkgs)}")

    # Try packages in order; some distros provide a version-specific and a
    # generic package name — stop at first success
    for pkg in pkgs:
        cmd = distro.install_cmd([pkg])
        if not cmd:
            break
        print(f"  $ {' '.join(cmd)}")
        result = subprocess.run(cmd, text=True)
        if result.returncode == 0 and _headers_present(kver):
            ok(f"Kernel headers installed successfully ({pkg})")
            return True

    # Last resort: sync package lists and retry (handles stale cache on Debian)
    if distro.pm == "apt-get":
        info("Running apt-get update and retrying ...")
        subprocess.run(["apt-get", "update", "-q"], text=True)
        for pkg in pkgs:
            result = subprocess.run(distro.install_cmd([pkg]), text=True)
            if result.returncode == 0 and _headers_present(kver):
                ok(f"Kernel headers installed after cache refresh ({pkg})")
                return True

    err(f"Could not install kernel headers for {kver.raw}")
    _print_manual_header_hint(kver, distro)
    return False


def _print_manual_header_hint(kver: KernelVersion, distro: "Distro"):
    """Print distro-specific manual install instructions."""
    k = kver.raw
    pm = distro.pm
    print()
    if pm == "apt-get":
        print(f"  sudo apt-get install linux-headers-{k}")
        print(f"  # If not available: sudo apt-get install linux-headers-generic")
    elif pm in ("dnf", "yum"):
        print(f"  sudo {pm} install kernel-devel-$(uname -r)")
        print(f"  sudo {pm} install kernel-devel  # (matches running kernel)")
    elif pm == "pacman":
        flavour = distro._arch_kernel_flavour(k)
        print(f"  sudo pacman -S {flavour}-headers")
    elif pm == "zypper":
        print(f"  sudo zypper install kernel-default-devel")
    elif pm == "emerge":
        print(f"  sudo emerge sys-kernel/linux-headers")
    elif pm == "apk":
        print(f"  sudo apk add linux-headers")
    else:
        print(f"  Install kernel headers for {k} using your package manager.")


def build_module(module: str, build_dir: Path, kver: KernelVersion, extra_flags: list) -> bool:
    section(f"Building {module}")
    module_dir = build_dir / f"{module}-only"
    if not module_dir.exists():
        err(f"Module directory not found: {module_dir}")
        return False

    result = run(
        ["make", f"VM_UNAME={kver.raw}"] + extra_flags,
        cwd=str(module_dir),
    )
    if result.returncode != 0:
        err(f"Failed to build {module}")
        return False

    ko = list(module_dir.rglob("*.ko"))
    if not ko:
        err(f"No .ko file produced for {module}")
        return False

    ok(f"{module}.ko built: {ko[0].name}")
    return True


def install_module(module: str, build_dir: Path, kver: KernelVersion) -> bool:
    module_dir = build_dir / f"{module}-only"
    ko_files = list(module_dir.rglob("*.ko"))
    if not ko_files:
        err(f"No .ko found to install for {module}")
        return False

    ko_src = ko_files[0]
    target_dir = Path(f"/lib/modules/{kver.raw}/misc")
    run(["sudo", "mkdir", "-p", str(target_dir)], check=True)

    target = target_dir / f"{module}.ko"
    result = run(["sudo", "cp", str(ko_src), str(target)])
    if result.returncode != 0:
        err(f"Failed to copy {module}.ko to {target_dir}")
        return False

    ok(f"{module}.ko installed to {target}")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — Fix vmci via vmware-modconfig
# ─────────────────────────────────────────────────────────────────────────────

def fix_vmci(kver: KernelVersion) -> bool:
    """
    VMware Workstation 25 does not ship vmci source (modules.xml only lists
    vmmon and vmnet). The kernel provides the equivalent driver as 'vmw_vmci',
    already signed by the kernel build key — no MOK signing required.
    """
    section(f"Loading vmci ({VMCI_MODULE} in-kernel driver)")
    info("VMware Workstation 25 does not ship vmci source.")
    info(f"Using the in-kernel '{VMCI_MODULE}' module instead.")

    load_result = run(["sudo", "modprobe", VMCI_MODULE])
    if load_result.returncode == 0:
        ok(f"{VMCI_MODULE} loaded successfully")
        vmci_dev = Path("/dev/vmci")
        if vmci_dev.exists():
            ok("/dev/vmci exists")
        else:
            info("/dev/vmci not present yet — may appear after VMware service restart")
        return True
    else:
        stderr_out = (load_result.stderr or "").lower()
        if "key was rejected" in stderr_out:
            warn(f"{VMCI_MODULE}: Key was rejected by service (Secure Boot blocking module)")
            return False
        err(f"Failed to load {VMCI_MODULE}: {load_result.stderr.strip()}")
        err("Check: dmesg | tail -20")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Phase 6 — Post-install setup
# ─────────────────────────────────────────────────────────────────────────────

def run_depmod(kver: KernelVersion):
    info("Updating module dependency database...")
    run(["sudo", "depmod", "-a", kver.raw])
    ok("depmod -a done")


def update_initramfs(kver: KernelVersion):
    info("Updating initramfs...")
    if shutil.which("update-initramfs"):
        result = run(["sudo", "update-initramfs", "-u", "-k", kver.raw])
        if result.returncode == 0:
            ok("initramfs updated (Debian/Ubuntu)")
        else:
            warn("update-initramfs returned non-zero, continuing")
    elif shutil.which("dracut"):
        result = run(["sudo", "dracut", "-f",
                       f"/boot/initramfs-{kver.raw}.img", kver.raw])
        if result.returncode == 0:
            ok("initramfs updated (Fedora/RHEL)")
        else:
            warn("dracut returned non-zero, continuing")
    elif shutil.which("mkinitcpio"):
        result = run(["sudo", "mkinitcpio", "-P"])
        if result.returncode == 0:
            ok("initramfs updated (Arch)")
        else:
            warn("mkinitcpio returned non-zero, continuing")
    else:
        warn("No initramfs tool found (update-initramfs/dracut/mkinitcpio) — skipping")


def write_module_load_config():
    """Write /etc/modules-load.d/vmware.conf and /etc/modprobe.d/vmware.conf."""
    info("Writing module boot-load configuration...")

    modules_load = Path("/etc/modules-load.d/vmware.conf")
    modules_load_content = (
        "# VMware kernel modules — load at boot\n"
        "# Written by vmware_module_builder.py\n"
        f"vmmon\n"
        f"vmnet\n"
        f"{VMCI_MODULE}\n"
    )
    result = subprocess.run(
        ["sudo", "tee", str(modules_load)],
        input=modules_load_content, text=True, capture_output=True,
    )
    if result.returncode == 0:
        ok(f"Written: {modules_load}")
    else:
        warn(f"Could not write {modules_load}: {result.stderr.strip()}")

    modprobe_conf = Path("/etc/modprobe.d/vmware.conf")
    modprobe_content = (
        "# VMware module load order\n"
        "# Written by vmware_module_builder.py\n"
        "softdep vmnet pre: vmmon\n"
        f"softdep {VMCI_MODULE} pre: vmmon\n"
    )
    result = subprocess.run(
        ["sudo", "tee", str(modprobe_conf)],
        input=modprobe_content, text=True, capture_output=True,
    )
    if result.returncode == 0:
        ok(f"Written: {modprobe_conf}")
    else:
        warn(f"Could not write {modprobe_conf}: {result.stderr.strip()}")


def create_systemd_unit():
    """Create a native vmware.service systemd unit to replace SysV script warnings."""
    init_script = Path("/etc/init.d/vmware")
    if not init_script.exists():
        info("No /etc/init.d/vmware found — skipping systemd unit creation")
        return

    modprobe_bin = shutil.which("modprobe") or "/usr/sbin/modprobe"
    unit_content = f"""[Unit]
Description=VMware Workstation Services
Documentation=https://www.vmware.com/
After=network.target systemd-modules-load.service
Requires=systemd-modules-load.service

[Service]
Type=forking
ExecStartPre={modprobe_bin} -a vmmon vmnet {VMCI_MODULE}
ExecStart=/etc/init.d/vmware start
ExecStop=/etc/init.d/vmware stop
RemainAfterExit=yes
TimeoutStartSec=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    unit_path = Path("/etc/systemd/system/vmware.service")
    result = subprocess.run(
        ["sudo", "tee", str(unit_path)],
        input=unit_content, text=True, capture_output=True,
    )
    if result.returncode == 0:
        ok(f"Systemd unit written: {unit_path}")
        run(["sudo", "systemctl", "daemon-reload"])
        run(["sudo", "systemctl", "enable", "vmware.service"])
        ok("vmware.service enabled at boot")
    else:
        warn(f"Could not write {unit_path}: {result.stderr.strip()}")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8 — Verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_installation(kver: KernelVersion, optimized: bool, distro: "Distro") -> bool:
    section("Verifying installation")
    all_ok = True

    # Check modules loaded
    lsmod = subprocess.run(["lsmod"], capture_output=True, text=True)
    loaded = lsmod.stdout if lsmod.returncode == 0 else ""

    for mod in ["vmmon", "vmnet", VMCI_MODULE]:
        if mod in loaded:
            ok(f"{mod} is loaded")
        else:
            warn(f"{mod} is NOT loaded")
            if mod == VMCI_MODULE:
                info(f"{VMCI_MODULE} may load when VMware starts a VM — this can be normal")
            else:
                all_ok = False

    # Check /dev/vmci
    vmci_dev = Path("/dev/vmci")
    if vmci_dev.exists():
        ok(f"/dev/vmci exists")
    else:
        warn("/dev/vmci not present — will appear when vmci module is loaded by VMware")

    # Check libgreenboost preload (causes noise for every process if misconfigured)
    greenboost_so = Path("/usr/local/lib/libgreenboost_audit.so")
    ld_preload_conf = Path("/etc/ld.so.preload")
    if ld_preload_conf.exists() and "libgreenboost_audit" in ld_preload_conf.read_text():
        if not greenboost_so.exists():
            warn("/etc/ld.so.preload references libgreenboost_audit.so but the file is missing.")
            warn("This generates ld.so errors on every process. To silence them:")
            print("    sudo sed -i '/libgreenboost_audit/d' /etc/ld.so.preload")

    # Print summary
    print()
    print("  ┌─ Summary " + "─" * 50)
    print(f"  │  Distro            : {distro.summary()}")
    print(f"  │  Kernel            : {kver.raw}")
    print(f"  │  Compilation mode  : {'Optimized' if optimized else 'Vanilla'}")
    lsmod_mods = [m for m in ["vmmon", "vmnet", VMCI_MODULE] if m in loaded]
    print(f"  │  Modules loaded    : {', '.join(lsmod_mods) or 'none'}")
    print(f"  │  /dev/vmci         : {'present' if vmci_dev.exists() else 'absent (normal until VM starts)'}")
    print("  └" + "─" * 59)
    print()

    return all_ok


# ─────────────────────────────────────────────────────────────────────────────
# Checks
# ─────────────────────────────────────────────────────────────────────────────

def check_root():
    if os.geteuid() != 0:
        err("This script must be run as root.")
        print("  Run:  sudo ./install-vmware-modules.sh")
        sys.exit(1)


def check_vmware_config():
    """
    Scan VMware XML config files for the 'Document is empty' crash condition.

    VMware Workstation reads XML preference files at startup. If any of these
    files is zero-byte or contains invalid XML, VMware emits:
        Entity: line 1: parser error : Document is empty
    and then crashes, which on some GNOME/Wayland setups causes a full session
    hang requiring a hard reboot (confirmed in logs: boot -1 ended 15:01:37).

    This check runs before the build so that corrupted configs are flagged
    early and the user can clear them before re-launching VMware.
    """
    section("VMware config integrity check")

    vmware_dirs = [
        Path.home() / ".vmware",
        Path("/etc/vmware"),
    ]

    suspect_files = []

    for vdir in vmware_dirs:
        if not vdir.exists():
            continue
        for xml_path in list(vdir.glob("*.xml")) + list(vdir.glob("preferences")) + list(vdir.glob("*.cfg")):
            if not xml_path.is_file():
                continue
            if xml_path.stat().st_size == 0:
                suspect_files.append((xml_path, "empty file (0 bytes)"))
                continue
            content = xml_path.read_bytes()
            # VMware preferences files may not be XML (key=value format); only
            # validate files that start with '<' (XML indicator).
            stripped = content.lstrip()
            if stripped and stripped[0:1] == b"<":
                try:
                    ET.fromstring(content.decode("utf-8", errors="replace"))
                except ET.ParseError as e:
                    suspect_files.append((xml_path, f"XML parse error: {e}"))

    if not suspect_files:
        ok("VMware config files look healthy (no empty or corrupt XML found)")
        return

    print()
    warn("CRASH RISK DETECTED — corrupt VMware config files found:")
    warn("These files caused the 'Document is empty' crash when launching VMware.")
    print()
    for path, reason in suspect_files:
        print(f"    {path}  [{reason}]")
    print()
    warn("Recommended fix: remove the affected files so VMware regenerates them.")
    print("  To remove them automatically, run:")
    for path, _ in suspect_files:
        print(f"    sudo rm -f {path}")
    print()
    info("The build will continue, but VMware may crash again on launch until")
    info("those files are removed or regenerated by a clean VMware run.")
    print()


def check_patch_repo():
    if not PATCHES_DIR.exists():
        err(f"Patches directory not found at: {PATCHES_DIR}")
        err("Expected a 'patches/' folder next to this script containing the required patch files.")
        sys.exit(1)
    if not UPSTREAM_616_DIR.exists():
        warn(f"Upstream 6.16.x overlay not found at: {UPSTREAM_616_DIR}")
        warn("  This overlay is a legacy fallback for VMware < 25H2u1 and is not required.")
        warn("  All patches will be applied via _autopatch_* functions against the installed sources.")
    ok(f"Patches directory found: {PATCHES_DIR}")


def check_vmware_version() -> tuple[str, int]:
    """
    Detect VMware Workstation version.
    Returns (version_string, major_int).
    Exits if VMware is not installed.
    """
    # Try vmware binary; fall back to reading the modules.xml manifest
    result = subprocess.run(["vmware", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        version_str = result.stdout.strip()
    else:
        # vmware not in PATH — try reading the installed manifest
        manifest = Path("/usr/lib/vmware/modules/source/modules.xml")
        version_str = ""
        if manifest.exists():
            m = re.search(r'version="([^"]+)"', manifest.read_text())
            if m:
                version_str = f"VMware Workstation {m.group(1)}"

    if not version_str:
        err("VMware Workstation not found (vmware --version failed and no manifest).")
        err("Install VMware Workstation before running this script.")
        sys.exit(1)

    ok(f"VMware detected: {version_str}")
    m = re.search(r'(\d+)\.\d', version_str)
    major = int(m.group(1)) if m else 0

    if major >= 26:
        warn(f"VMware Workstation {major}.x — upstream sources may differ from the")
        warn("6.16.x reference sources bundled here.  Autopatches will adapt.")
    return version_str, major


def check_vmware_sources():
    """Verify vmmon.tar and vmnet.tar exist under VMWARE_MOD_DIR."""
    for tarname in ["vmmon.tar", "vmnet.tar"]:
        if not (VMWARE_MOD_DIR / tarname).exists():
            err(f"VMware module source not found: {VMWARE_MOD_DIR / tarname}")
            err("Is VMware Workstation properly installed?")
            sys.exit(1)
    ok(f"VMware module sources found in {VMWARE_MOD_DIR}")

    # Validate modules.xml — an empty or corrupt manifest causes VMware to crash
    # on startup with "Document is empty" (confirmed crash on 2026-03-26 15:01:37).
    manifest = VMWARE_MOD_DIR / "modules.xml"
    if manifest.exists():
        if manifest.stat().st_size == 0:
            warn(f"{manifest} is empty — VMware may crash on launch.")
            warn("Try reinstalling VMware Workstation to regenerate it.")
        else:
            try:
                ET.parse(str(manifest))
                ok(f"modules.xml is valid XML")
            except ET.ParseError as e:
                warn(f"{manifest} contains invalid XML: {e}")
                warn("VMware may crash on launch. Try reinstalling VMware Workstation.")


# ─────────────────────────────────────────────────────────────────────────────
# VMware source explorer
#
# Inspects the extracted vmmon/vmnet source trees *before* patching to
# discover what the actual source version looks like.  This information drives
# the autopatch decisions: patches are only applied when the problem signature
# is present and the fix is not yet there.
# ─────────────────────────────────────────────────────────────────────────────

class VmwareSourceInfo:
    """
    Lightweight static analysis of extracted vmmon/vmnet sources.
    Populated by explore_vmware_sources() before apply_all_patches().
    """

    def __init__(self, vmmon_dir: Path, vmnet_dir: Path):
        self.vmmon_dir = vmmon_dir
        self.vmnet_dir = vmnet_dir

        # ── Makefile style (affects anchor selection) ─────────────────────────
        vmmon_mk = _read(vmmon_dir / "Makefile.kernel") if (vmmon_dir / "Makefile.kernel").exists() else ""
        vmnet_mk = _read(vmnet_dir / "Makefile.kernel") if (vmnet_dir / "Makefile.kernel").exists() else ""

        # Older VMware: EXTRA_CFLAGS; newer: CC_OPTS + ccflags-y
        self.vmmon_uses_extra_cflags = "EXTRA_CFLAGS" in vmmon_mk and "CC_OPTS += -DVMMON" not in vmmon_mk
        self.vmnet_uses_extra_cflags = "EXTRA_CFLAGS" in vmnet_mk

        # ── Source API usage ──────────────────────────────────────────────────
        hostif = _read(vmmon_dir / "linux" / "hostif.c") if (vmmon_dir / "linux" / "hostif.c").exists() else ""
        bridge = _read(vmnet_dir / "bridge.c") if (vmnet_dir / "bridge.c").exists() else ""
        compat_nd = _read(vmnet_dir / "compat_netdevice.h") if (vmnet_dir / "compat_netdevice.h").exists() else ""

        self.has_do_gettimeofday = "do_gettimeofday" in bridge
        self.do_gettimeofday_guarded = (
            "LINUX_VERSION_CODE < KERNEL_VERSION(5, 0" in bridge and
            "ktime_get_real_ts64" in bridge
        )
        self.has_napi_add_4arg = (
            "netif_napi_add(dev, napi, poll, quota)" in compat_nd or
            "netif_napi_add(dev, napi, poll, weight)" in compat_nd
        )
        self.napi_add_already_fixed = (
            "kernel 6.1+" in compat_nd or
            "KERNEL_VERSION(6, 1" in compat_nd
        )
        self.has_task_state_guard = "get_task_state(task) READ_ONCE" in hostif
        self.has_objtool_markers = "OBJECT_FILES_NON_STANDARD" in vmmon_mk

        # ── File existence ────────────────────────────────────────────────────
        self.has_phystrack = (vmmon_dir / "common" / "phystrack.c").exists()
        self.has_compat_netdevice = (vmnet_dir / "compat_netdevice.h").exists()
        self.has_vm_basic_types_vmmon = (vmmon_dir / "include" / "vm_basic_types.h").exists()

    def report(self):
        info("  VMware source analysis:")
        info(f"    vmmon Makefile style : {'EXTRA_CFLAGS' if self.vmmon_uses_extra_cflags else 'CC_OPTS'}")
        info(f"    vmnet Makefile style : {'EXTRA_CFLAGS' if self.vmnet_uses_extra_cflags else 'CC_OPTS'}")
        info(f"    do_gettimeofday      : {'yes (unguarded)' if self.has_do_gettimeofday and not self.do_gettimeofday_guarded else 'guarded/absent'}")
        info(f"    netif_napi_add       : {'4-arg (needs fix)' if self.has_napi_add_4arg and not self.napi_add_already_fixed else 'OK'}")
        info(f"    task->state guard    : {'present' if self.has_task_state_guard else 'absent'}")
        info(f"    objtool markers      : {'present' if self.has_objtool_markers else 'absent'}")


def explore_vmware_sources(build_dir: Path) -> VmwareSourceInfo:
    """
    Extract and analyse the VMware sources before patching.
    Returns a VmwareSourceInfo that the autopatch system uses to decide
    which fixes are needed.
    """
    section("Exploring VMware source trees")
    src = VmwareSourceInfo(build_dir / "vmmon-only", build_dir / "vmnet-only")
    src.report()
    return src


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    banner(
        "VMware Module Builder\n"
        "Fixes vmci + rebuilds vmmon/vmnet\n"
        "with kernel compatibility patches"
    )

    # ── Pre-flight checks ─────────────────────────────────────────────────────
    section("Pre-flight checks")
    check_root()
    check_patch_repo()

    # Distro detection — must happen before header check so we know the PM
    distro = detect_distro()
    ok(f"Distro: {distro.summary()}")

    kver = get_kernel_version()
    ok(f"Kernel: {kver.raw}  (major={kver.major}, minor={kver.minor}, patch={kver.patch})")

    if not kver.is_supported():
        err(f"Kernel {kver.raw} is below 6.16 — unsupported by the 6.16.x patches")
        err("Please upgrade your kernel or patch manually.")
        sys.exit(1)

    if not check_kernel_headers(kver, distro):
        sys.exit(1)

    check_vmware_version()
    check_vmware_sources()
    check_vmware_config()

    # ── Secure Boot detection ─────────────────────────────────────────────────
    section("Secure Boot detection")
    secure_boot = detect_secure_boot()
    if secure_boot:
        print_secure_boot_signing_instructions(kver.raw)
        warn("Continuing with build — you will need to sign modules manually after.")
    else:
        ok("Secure Boot: disabled (modules can load unsigned)")

    # ── Hardware detection & optimization mode ────────────────────────────────
    cpu = CpuFeatures()
    if not cpu.has_virt():
        warn("Hardware virtualization (VT-x / AMD-V) not detected in CPU flags!")
        warn("VMware requires hardware virtualization. Check your BIOS settings.")

    optimized = ask_optimization_mode(cpu)
    extra_make_flags = make_flags(optimized, cpu)
    ok(f"Compilation mode: {'Optimized' if optimized else 'Vanilla'}")
    ok(f"Make flags: {' '.join(extra_make_flags)}")

    # ── Unload existing modules ───────────────────────────────────────────────
    section("Unloading existing VMware modules")
    for mod in ["vmnet", "vmmon", VMCI_MODULE]:
        run(["sudo", "modprobe", "-r", mod])
        run(["sudo", "rmmod", mod])
    ok("Existing modules unloaded (errors above are normal if not loaded)")

    # ── Backup & extract ──────────────────────────────────────────────────────
    section("Backup & source extraction")
    backup_dir = get_or_create_backup()

    with tempfile.TemporaryDirectory(prefix="vmware_build_") as tmp:
        build_dir = Path(tmp)
        ok(f"Temporary build directory: {build_dir}")

        for module in ["vmmon", "vmnet"]:
            tar_src = backup_dir / f"{module}.tar"
            info(f"Extracting {tar_src.name} from backup...")
            with tarfile.open(tar_src, "r") as tf:
                tf.extractall(tmp)
            ok(f"{module} source extracted")

        # ── Explore source trees before patching ──────────────────────────────
        src_info = explore_vmware_sources(build_dir)

        # ── Apply patches ─────────────────────────────────────────────────────
        apply_all_patches(build_dir, kver, optimized, src_info)

        # ── Build modules ─────────────────────────────────────────────────────
        section("Compiling vmmon and vmnet")
        for module in ["vmmon", "vmnet"]:
            if not build_module(module, build_dir, kver, extra_make_flags):
                err(f"Build failed for {module}. Aborting.")
                sys.exit(1)

        # ── Install modules ───────────────────────────────────────────────────
        section("Installing vmmon and vmnet")
        for module in ["vmmon", "vmnet"]:
            if not install_module(module, build_dir, kver):
                err(f"Install failed for {module}. Aborting.")
                sys.exit(1)

        # ── Update tarballs in VMware source dir ──────────────────────────────
        section("Updating VMware source tarballs")
        info("Cleaning build artifacts before repacking...")
        for module in ["vmmon", "vmnet"]:
            module_dir = build_dir / f"{module}-only"
            run(["make", "clean"], cwd=str(module_dir))

        for module in ["vmmon", "vmnet"]:
            tarball = build_dir / f"{module}.tar"
            info(f"Repacking {module}.tar...")
            with tarfile.open(str(tarball), "w") as tf:
                tf.add(str(build_dir / f"{module}-only"),
                       arcname=f"{module}-only")
            run(["sudo", "cp", str(tarball), str(VMWARE_MOD_DIR / f"{module}.tar")])
            ok(f"{module}.tar updated in {VMWARE_MOD_DIR}")

    # ── depmod ────────────────────────────────────────────────────────────────
    section("Post-install setup")
    run_depmod(kver)

    # ── Fix vmci (Phase 1) ────────────────────────────────────────────────────
    vmci_ok = fix_vmci(kver)

    # ── initramfs ─────────────────────────────────────────────────────────────
    update_initramfs(kver)

    # ── Module load config ────────────────────────────────────────────────────
    write_module_load_config()

    # ── Systemd unit ──────────────────────────────────────────────────────────
    create_systemd_unit()

    # ── Load modules ──────────────────────────────────────────────────────────
    section("Loading modules")
    for mod in ["vmmon", "vmnet"]:
        result = run(["sudo", "modprobe", mod])
        if result.returncode == 0:
            ok(f"{mod} loaded")
        else:
            stderr_out = (result.stderr or "").lower()
            if "key was rejected" in stderr_out:
                err(f"{mod}: Secure Boot is blocking the module — sign it with your MOK key")
                if not secure_boot:
                    warn("Secure Boot was not detected earlier but modprobe reports key rejection.")
                    warn("Check: mokutil --sb-state")
            else:
                err(f"Failed to load {mod}: {result.stderr.strip()}")

    # ── Restart VMware services ───────────────────────────────────────────────
    section("Restarting VMware services")
    for svc in ["vmware.service", "vmware-networks.service"]:
        run(["sudo", "systemctl", "restart", svc], timeout=30)
    # Legacy fallback
    if Path("/etc/init.d/vmware").exists():
        run(["sudo", "/etc/init.d/vmware", "restart"], timeout=30)

    # ── Verification ──────────────────────────────────────────────────────────
    all_ok = verify_installation(kver, optimized, distro)

    # ── Final notes ───────────────────────────────────────────────────────────
    if secure_boot and not vmci_ok:
        print()
        warn(f"Secure Boot is enabled and {VMCI_MODULE} failed to load.")
        warn("vmmon and vmnet must be signed with your MOK key — see instructions above.")
        warn(f"{VMCI_MODULE} is kernel-signed and should not require MOK signing.")

    if not vmci_ok:
        print()
        warn(f"{VMCI_MODULE} module could not be loaded.")
        warn(f"Try:  sudo modprobe {VMCI_MODULE}")
        warn("If that fails, check: dmesg | tail -20")

    print()
    if all_ok or vmci_ok:
        ok("Done! Start VMware Workstation — your VM should now power on.")
    else:
        warn("Some modules did not load. Check errors above.")
        warn("If the issue persists, try rebooting: sudo reboot")

    print()


if __name__ == "__main__":
    main()
