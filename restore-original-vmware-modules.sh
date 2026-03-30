#!/usr/bin/env bash
# restore-original-vmware-modules.sh
# Restores VMware's original (unpatched) module source tarballs from the
# backups created by install-vmware-modules.sh, then rebuilds the modules
# using VMware's own vmware-modconfig tool.
#
# Usage:
#   sudo ./restore-original-vmware-modules.sh
#
# This is useful if:
#   - You want to go back to VMware's stock modules
#   - A patched build is causing issues
#   - You are about to reinstall VMware Workstation
#
# Backups are stored in:
#   /usr/lib/vmware/modules/source/backup-<timestamp>/

set -uo pipefail

VMWARE_MOD_DIR="/usr/lib/vmware/modules/source"
KVER="$(uname -r)"

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()      { echo -e "  ${GREEN}✅${NC}  $*"; }
err()     { echo -e "  ${RED}❌${NC}  $*" >&2; }
warn()    { echo -e "  ${YELLOW}⚠️ ${NC}  $*" >&2; }
info()    { echo -e "  ℹ️   $*"; }
section() { echo -e "\n${CYAN}──────────────────────────────────────────────────────────────${NC}"; echo -e "  $*"; echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"; }

# ── Root check ────────────────────────────────────────────────────────────────
if [[ "${EUID}" -ne 0 ]]; then
    err "This script must be run as root."
    echo "  Run:  sudo ./restore-original-vmware-modules.sh"
    exit 1
fi

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          VMware Module Restore                               ║"
echo "║  Restores original VMware sources and rebuilds modules       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
info "Running kernel : ${KVER}"
info "Source dir     : ${VMWARE_MOD_DIR}"
echo ""

# ── Find backups ──────────────────────────────────────────────────────────────
section "Available backups"

mapfile -t BACKUPS < <(ls -d "${VMWARE_MOD_DIR}"/backup-* 2>/dev/null | sort)

if [[ ${#BACKUPS[@]} -eq 0 ]]; then
    err "No backups found in ${VMWARE_MOD_DIR}."
    err "Backups are created automatically by install-vmware-modules.sh on first run."
    err "If you have never run that script, no backup exists."
    echo ""
    info "Alternatives:"
    info "  - Reinstall VMware Workstation to get fresh source tarballs"
    info "  - Run: sudo vmware-modconfig --console --install-all"
    exit 1
fi

echo ""
echo "  Found ${#BACKUPS[@]} backup(s):"
echo ""

for i in "${!BACKUPS[@]}"; do
    BDIR="${BACKUPS[$i]}"
    BNAME="$(basename "${BDIR}")"
    # Show sizes
    VMMON_SIZE="n/a"
    VMNET_SIZE="n/a"
    [[ -f "${BDIR}/vmmon.tar" ]] && VMMON_SIZE="$(du -sh "${BDIR}/vmmon.tar" 2>/dev/null | cut -f1)"
    [[ -f "${BDIR}/vmnet.tar" ]] && VMNET_SIZE="$(du -sh "${BDIR}/vmnet.tar" 2>/dev/null | cut -f1)"
    echo "  $((i+1))) ${BNAME}   [vmmon.tar: ${VMMON_SIZE}, vmnet.tar: ${VMNET_SIZE}]"
done

# Always show "oldest" hint
echo ""
info "The oldest backup (option 1) is the most likely to be the clean original."
echo ""

# ── Select backup ─────────────────────────────────────────────────────────────
DEFAULT_IDX=1
read -rp "  Select backup to restore [1-${#BACKUPS[@]}, default=${DEFAULT_IDX}]: " BACKUP_CHOICE
BACKUP_CHOICE="${BACKUP_CHOICE:-${DEFAULT_IDX}}"

if ! [[ "${BACKUP_CHOICE}" =~ ^[0-9]+$ ]] || \
   [[ "${BACKUP_CHOICE}" -lt 1 ]] || \
   [[ "${BACKUP_CHOICE}" -gt ${#BACKUPS[@]} ]]; then
    err "Invalid selection: ${BACKUP_CHOICE}"
    exit 1
fi

SELECTED_BACKUP="${BACKUPS[$((BACKUP_CHOICE-1))]}"
SELECTED_NAME="$(basename "${SELECTED_BACKUP}")"

echo ""
info "Selected: ${SELECTED_NAME}"

# Verify tarball presence
MISSING=0
for tarname in vmmon.tar vmnet.tar; do
    if [[ ! -f "${SELECTED_BACKUP}/${tarname}" ]]; then
        err "Missing in backup: ${SELECTED_BACKUP}/${tarname}"
        MISSING=1
    fi
done
if [[ "${MISSING}" -ne 0 ]]; then
    err "Backup is incomplete. Choose a different backup or reinstall VMware."
    exit 1
fi

# ── Confirm ───────────────────────────────────────────────────────────────────
echo ""
warn "This will overwrite the current vmmon.tar and vmnet.tar in:"
warn "  ${VMWARE_MOD_DIR}"
warn "with the contents of backup: ${SELECTED_NAME}"
echo ""
read -rp "  Proceed? [y/N]: " CONFIRM
if [[ ! "${CONFIRM}" =~ ^[Yy]$ ]]; then
    info "Cancelled. No changes made."
    exit 0
fi

# ── Restore tarballs ──────────────────────────────────────────────────────────
section "Restoring tarballs from ${SELECTED_NAME}"

for tarname in vmmon.tar vmnet.tar; do
    src="${SELECTED_BACKUP}/${tarname}"
    dst="${VMWARE_MOD_DIR}/${tarname}"
    cp "${src}" "${dst}"
    ok "Restored: ${dst}"
done

# ── Optionally rebuild with vmware-modconfig ──────────────────────────────────
section "Rebuilding modules from restored sources"

if ! command -v vmware-modconfig &>/dev/null; then
    warn "vmware-modconfig not found in PATH."
    warn "Skipping rebuild. To rebuild manually, run:"
    warn "  sudo vmware-modconfig --console --install-all"
    echo ""
    info "Or run install-vmware-modules.sh again to use the patched builder:"
    info "  sudo ./install-vmware-modules.sh"
    exit 0
fi

echo ""
echo "  Choose how to rebuild the restored modules:"
echo ""
echo "  1) Use VMware's own vmware-modconfig (stock, unpatched build)"
echo "  2) Use install-vmware-modules.sh (patched build for kernel ${KVER})"
echo "  3) Skip rebuild (restore tarballs only)"
echo ""
read -rp "  Select [1/2/3, default=1]: " REBUILD_CHOICE
REBUILD_CHOICE="${REBUILD_CHOICE:-1}"

case "${REBUILD_CHOICE}" in
    1)
        info "Running: vmware-modconfig --console --install-all"
        echo ""
        if vmware-modconfig --console --install-all; then
            ok "Modules rebuilt with vmware-modconfig"
        else
            warn "vmware-modconfig returned non-zero. Check output above."
            warn "You may need to install kernel headers or reboot first."
        fi
        ;;
    2)
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        INSTALL_SH="${SCRIPT_DIR}/install-vmware-modules.sh"
        if [[ -f "${INSTALL_SH}" ]]; then
            info "Running: ${INSTALL_SH}"
            echo ""
            exec bash "${INSTALL_SH}"
        else
            err "install-vmware-modules.sh not found at: ${INSTALL_SH}"
            err "Run it manually from the repo directory."
            exit 1
        fi
        ;;
    3)
        info "Skipping rebuild. Tarballs have been restored."
        info "To rebuild later, run one of:"
        info "  sudo vmware-modconfig --console --install-all"
        info "  sudo ./install-vmware-modules.sh"
        ;;
    *)
        warn "Invalid choice '${REBUILD_CHOICE}'. Skipping rebuild."
        ;;
esac

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Restore complete.                                           ║"
echo "║  Original VMware source tarballs have been reinstated.      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
