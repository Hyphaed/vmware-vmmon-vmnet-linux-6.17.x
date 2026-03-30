#!/usr/bin/env bash
# install-vmware-modules.sh — VMware Module Builder v1.0.0
# Rebuilds and installs VMware kernel modules (vmmon, vmnet) with kernel
# compatibility patches for Linux 6.16+ / 7.x.
#
# Usage:
#   sudo ./install-vmware-modules.sh
#
# On startup it checks for a newer version on GitLab, then asks whether to
# install with DKMS (automatic kernel-update rebuilds) or without (manual).
#
# Project: https://gitlab.com/IsolatedOctopi/vmware_module_builder

set -uo pipefail

# ── Version & update-check constants ─────────────────────────────────────────
SCRIPT_VERSION="v1.0.0"
GITLAB_API="https://gitlab.com/api/v4/projects/IsolatedOctopi%2Fvmware_module_builder/repository/tags"
GITLAB_URL="https://gitlab.com/IsolatedOctopi/vmware_module_builder"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/vmware_module_builder.py"
VMWARE_MOD_DIR="/usr/lib/vmware/modules/source"

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()      { echo -e "  ${GREEN}✅${NC}  $*"; }
err()     { echo -e "  ${RED}❌${NC}  $*" >&2; }
warn()    { echo -e "  ${YELLOW}⚠️ ${NC}  $*" >&2; }
info()    { echo -e "  ℹ️   $*"; }
section() { echo -e "\n${CYAN}──────────────────────────────────────────────────────────────${NC}"; echo -e "  $*"; echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          VMware Module Builder ${SCRIPT_VERSION}                        ║"
echo "║  Patches + compiles vmmon/vmnet for Linux 6.16+ / 7.x       ║"
echo "║  ${GITLAB_URL}  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── Step 0a: GitLab version check (non-blocking, 5s timeout) ─────────────────
check_for_update() {
    local raw latest newer

    if command -v curl &>/dev/null; then
        raw=$(curl -fsSL --max-time 5 "${GITLAB_API}" 2>/dev/null)
    elif command -v wget &>/dev/null; then
        raw=$(wget -qO- --timeout=5 "${GITLAB_API}" 2>/dev/null)
    else
        return  # no HTTP client available — skip silently
    fi

    [[ -z "${raw}" ]] && return  # offline or empty response

    # Extract the highest version tag (e.g. "v1.0.0")
    latest=$(echo "${raw}" \
        | grep -oP '"name"\s*:\s*"\Kv?[0-9]+\.[0-9]+(?:\.[0-9]+)?' \
        | sort -V | tail -1)

    [[ -z "${latest}" ]] && return  # no version tags found yet

    # Compare: strip leading 'v' for sort -V comparison
    newer=$(printf '%s\n%s\n' "${SCRIPT_VERSION#v}" "${latest#v}" | sort -V | tail -1)

    if [[ "${newer}" != "${SCRIPT_VERSION#v}" ]]; then
        echo ""
        warn "╔══════════════════════════════════════════════════════════════╗"
        warn "║  A newer version of VMware Module Builder is available!      ║"
        warn "║  Latest  : ${latest}"
        warn "║  Current : ${SCRIPT_VERSION}"
        warn "║  Download: ${GITLAB_URL}"
        warn "╚══════════════════════════════════════════════════════════════╝"
        echo ""
        local upd
        read -rp "  Stop installation to download the update first? [y/N]: " upd
        if [[ "${upd,,}" == "y" ]]; then
            info "Exiting. Clone or download the new version and re-run."
            info "  git clone ${GITLAB_URL}.git"
            exit 0
        fi
        info "Continuing with current version (${SCRIPT_VERSION})."
        echo ""
    else
        ok "Version ${SCRIPT_VERSION} — up to date"
    fi
}

check_for_update

# ── Step 0b: Installation mode selection ─────────────────────────────────────
echo "  How would you like to install the VMware kernel modules?"
echo ""
echo "  ┌──────────────────────────────────────────────────────────┐"
echo "  │  1) DKMS  (recommended — default)                        │"
echo "  │     Modules are registered with DKMS and rebuilt         │"
echo "  │     automatically on every kernel update.                │"
echo "  │     No manual re-run needed after 'apt upgrade'.         │"
echo "  │                                                          │"
echo "  │  2) Non-DKMS  (manual)                                   │"
echo "  │     Modules are installed for the current kernel only.   │"
echo "  │     You must re-run this script after every kernel       │"
echo "  │     update.                                              │"
echo "  └──────────────────────────────────────────────────────────┘"
echo ""
read -rp "  Select [1/2, default=1]: " MODE_CHOICE
MODE_CHOICE="${MODE_CHOICE:-1}"

case "${MODE_CHOICE}" in
    1) INSTALL_MODE="dkms" ;;
    2) INSTALL_MODE="nondkms" ;;
    *)
        warn "Invalid choice '${MODE_CHOICE}'. Defaulting to DKMS."
        INSTALL_MODE="dkms"
        ;;
esac

echo ""
if [[ "${INSTALL_MODE}" == "dkms" ]]; then
    ok "Mode selected: DKMS (automatic kernel-update rebuilds)"
else
    ok "Mode selected: Non-DKMS (manual re-run required after kernel updates)"
fi
echo ""

# ── Common pre-flight checks ──────────────────────────────────────────────────

# Root check
if [[ "${EUID}" -ne 0 ]]; then
    err "This script must be run as root."
    echo "  Run:  sudo ./install-vmware-modules.sh"
    exit 1
fi

# Python 3 check
if ! command -v python3 &>/dev/null; then
    err "python3 is required but not found."
    echo "  Install it with your package manager, e.g.:"
    echo "    apt-get install python3   # Debian/Ubuntu"
    echo "    dnf install python3       # Fedora/RHEL"
    echo "    pacman -S python          # Arch"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
PYTHON_MAJOR=$(echo "${PYTHON_VERSION}" | cut -d. -f1)
PYTHON_MINOR=$(echo "${PYTHON_VERSION}" | cut -d. -f2)

if [[ "${PYTHON_MAJOR}" -lt 3 ]] || { [[ "${PYTHON_MAJOR}" -eq 3 ]] && [[ "${PYTHON_MINOR}" -lt 8 ]]; }; then
    err "Python 3.8+ is required (found ${PYTHON_VERSION})."
    exit 1
fi

ok "Python ${PYTHON_VERSION} found"

# Builder script check
if [[ ! -f "${PYTHON_SCRIPT}" ]]; then
    err "Builder script not found: ${PYTHON_SCRIPT}"
    err "Ensure vmware_module_builder.py is in the same directory."
    exit 1
fi

ok "Builder found: ${PYTHON_SCRIPT}"

# DKMS check (only required for DKMS mode)
if [[ "${INSTALL_MODE}" == "dkms" ]]; then
    if ! command -v dkms &>/dev/null; then
        err "DKMS is required for this installation mode but was not found."
        echo "  Install it with your package manager, e.g.:"
        echo "    apt-get install dkms   # Debian/Ubuntu"
        echo "    dnf install dkms       # Fedora/RHEL"
        echo "    pacman -S dkms         # Arch"
        echo ""
        echo "  Or re-run and select option 2 (Non-DKMS)."
        exit 1
    fi
    DKMS_VERSION=$(dkms --version 2>/dev/null | head -1)
    ok "DKMS found: ${DKMS_VERSION}"
fi

# ── Run the Python builder (patch + build + install for current kernel) ────────
section "Running VMware Module Builder (patch + build + install)"
echo ""

python3 "${PYTHON_SCRIPT}"

echo ""
ok "Build and install complete."

# ── Non-DKMS path: done ───────────────────────────────────────────────────────
if [[ "${INSTALL_MODE}" == "nondkms" ]]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  Installation complete (non-DKMS).                          ║"
    echo "║                                                              ║"
    echo "║  Remember: re-run this script after every kernel update.    ║"
    echo "║    sudo ./install-vmware-modules.sh                         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    exit 0
fi

# ── DKMS path: extract patched sources + register ────────────────────────────

# Detect VMware version for DKMS module versioning
VMWARE_VER=""
if command -v vmware &>/dev/null; then
    VMWARE_VER=$(vmware --version 2>/dev/null | grep -oP '[\d.]+' | head -1 || true)
fi
if [[ -z "${VMWARE_VER}" ]]; then
    VMWARE_VER=$(grep -oP 'version="\K[^"]+' "${VMWARE_MOD_DIR}/modules.xml" 2>/dev/null | head -1 || true)
fi
if [[ -z "${VMWARE_VER}" ]]; then
    VMWARE_VER="25.0.0"
    warn "Could not detect VMware version; using fallback '${VMWARE_VER}' for DKMS."
fi

ok "VMware version: ${VMWARE_VER} (DKMS module version)"

# ── Purge ALL pre-existing DKMS registrations for vmmon/vmnet ────────────────
# This removes any registration VMware's own installer (vmware-installer,
# open-vm-tools, or a previous run) may have put in place, regardless of
# version, so our patched build is the sole authority in the DKMS database.
section "Purging any pre-existing DKMS registrations for vmmon / vmnet"

for MODULE in vmmon vmnet; do
    # Collect every registered version (dkms status output: "module/version, ...")
    mapfile -t REGISTERED < <(dkms status "${MODULE}" 2>/dev/null \
        | grep -oP "^${MODULE}/\K[^,: ]+" || true)

    if [[ ${#REGISTERED[@]} -eq 0 ]]; then
        info "No existing DKMS registrations found for ${MODULE}."
    else
        for VER in "${REGISTERED[@]}"; do
            info "Removing DKMS registration: ${MODULE}/${VER} ..."
            dkms remove "${MODULE}/${VER}" --all 2>/dev/null || true
            ok "  Removed ${MODULE}/${VER}"
        done
    fi

    # Also wipe any /usr/src/<module>-*/ trees VMware may have placed there
    # (vmware-installer sometimes populates these directly)
    for leftover in /usr/src/${MODULE}-*/; do
        [[ -d "${leftover}" ]] || continue
        info "Removing stale source tree: ${leftover} ..."
        rm -rf "${leftover}"
        ok "  Removed ${leftover}"
    done
done

# ── Extract patched source trees into /usr/src/ ───────────────────────────────
# After vmware_module_builder.py runs, the repacked tarballs at
# /usr/lib/vmware/modules/source/{vmmon,vmnet}.tar contain the patched source.
section "Extracting patched sources for DKMS"

for MODULE in vmmon vmnet; do
    DKMS_SRC_DIR="/usr/src/${MODULE}-${VMWARE_VER}"
    TARBALL="${VMWARE_MOD_DIR}/${MODULE}.tar"

    if [[ ! -f "${TARBALL}" ]]; then
        err "Tarball not found: ${TARBALL}"
        err "The build step should have produced this file. Aborting DKMS setup."
        exit 1
    fi

    mkdir -p "${DKMS_SRC_DIR}"

    info "Extracting ${TARBALL} → ${DKMS_SRC_DIR}/ ..."
    tar xf "${TARBALL}" -C "${DKMS_SRC_DIR}" --strip-components=1
    ok "Patched source extracted: ${DKMS_SRC_DIR}"
done

# Write dkms.conf for each module
section "Writing DKMS configuration"

cat > "/usr/src/vmmon-${VMWARE_VER}/dkms.conf" <<EOF
PACKAGE_NAME="vmmon"
PACKAGE_VERSION="${VMWARE_VER}"
BUILT_MODULE_NAME[0]="vmmon"
BUILT_MODULE_LOCATION[0]="."
DEST_MODULE_LOCATION[0]="/updates/dkms"
MAKE[0]="make VM_UNAME=\${kernelver}"
CLEAN="make clean"
AUTOINSTALL="yes"
EOF
ok "dkms.conf written: /usr/src/vmmon-${VMWARE_VER}/dkms.conf"

cat > "/usr/src/vmnet-${VMWARE_VER}/dkms.conf" <<EOF
PACKAGE_NAME="vmnet"
PACKAGE_VERSION="${VMWARE_VER}"
BUILT_MODULE_NAME[0]="vmnet"
BUILT_MODULE_LOCATION[0]="."
DEST_MODULE_LOCATION[0]="/updates/dkms"
MAKE[0]="make VM_UNAME=\${kernelver}"
CLEAN="make clean"
AUTOINSTALL="yes"
EOF
ok "dkms.conf written: /usr/src/vmnet-${VMWARE_VER}/dkms.conf"

# Register, build, and install via DKMS
section "Registering modules with DKMS"

KVER="$(uname -r)"

# Remove any pre-existing .ko files from the kernel tree for vmmon/vmnet before
# dkms install runs. DKMS labels the entry "(Original modules exist)" whenever it
# finds a .ko already sitting at the destination path and backs it up. Removing
# them first means DKMS installs into an empty slot and reports plain "installed".
for MODULE in vmmon vmnet; do
    for ko_path in \
        "/lib/modules/${KVER}/misc/${MODULE}.ko" \
        "/lib/modules/${KVER}/misc/${MODULE}.ko.zst" \
        "/lib/modules/${KVER}/misc/${MODULE}.ko.xz" \
        "/lib/modules/${KVER}/extra/${MODULE}.ko" \
        "/lib/modules/${KVER}/extra/${MODULE}.ko.zst" \
        "/lib/modules/${KVER}/kernel/drivers/misc/${MODULE}.ko" \
        "/lib/modules/${KVER}/updates/dkms/${MODULE}.ko" \
        "/lib/modules/${KVER}/updates/dkms/${MODULE}.ko.zst"; do
        if [[ -f "${ko_path}" ]]; then
            info "Removing pre-existing module: ${ko_path}"
            rm -f "${ko_path}"
        fi
    done
    # Also remove any DKMS-saved "original" backup copies
    find "/var/lib/dkms/${MODULE}" -name "*.ko" -o -name "*.ko.zst" \
        2>/dev/null | xargs -r rm -f
done
depmod -a "${KVER}" 2>/dev/null || true

for MODULE in vmmon vmnet; do
    DKMS_SRC_DIR="/usr/src/${MODULE}-${VMWARE_VER}"

    info "dkms add ${MODULE}/${VMWARE_VER} ..."
    dkms add "${DKMS_SRC_DIR}"
    ok "${MODULE}: added to DKMS"

    info "dkms build ${MODULE}/${VMWARE_VER} -k ${KVER} ..."
    if ! dkms build "${MODULE}/${VMWARE_VER}" -k "${KVER}"; then
        err "DKMS build failed for ${MODULE}/${VMWARE_VER}."
        err "The .ko installed by vmware_module_builder.py is still active for the current kernel."
        warn "DKMS will handle future kernels once the build issue is resolved."
        continue
    fi
    ok "${MODULE}: DKMS build successful"

    info "dkms install ${MODULE}/${VMWARE_VER} -k ${KVER} --force ..."
    if dkms install "${MODULE}/${VMWARE_VER}" -k "${KVER}" --force; then
        ok "${MODULE}: installed via DKMS for kernel ${KVER}"
    else
        warn "${MODULE}: dkms install returned non-zero. The module may still be active."
    fi
done

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  DKMS installation complete.                                 ║"
echo "║                                                              ║"
echo "║  vmmon and vmnet are now managed by DKMS.                   ║"
echo "║  They rebuild automatically on every kernel update.         ║"
echo "║  No manual re-run needed after 'apt upgrade' or similar.   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "  Module status (patched + optimized builds):"
for MODULE in vmmon vmnet; do
    KO_PATH=$(find "/lib/modules/${KVER}" -name "${MODULE}.ko" \
        -o -name "${MODULE}.ko.zst" -o -name "${MODULE}.ko.xz" \
        2>/dev/null | head -1)
    if [[ -n "${KO_PATH}" ]]; then
        ok "  ${MODULE}: installed → ${KO_PATH}"
    else
        warn "  ${MODULE}: .ko not found under /lib/modules/${KVER}"
    fi
    LOADED=$(lsmod 2>/dev/null | grep -c "^${MODULE}" || true)
    if [[ "${LOADED}" -gt 0 ]]; then
        ok "  ${MODULE}: loaded in kernel"
    else
        info "  ${MODULE}: not currently loaded (will load on next VMware start)"
    fi
done
echo ""
