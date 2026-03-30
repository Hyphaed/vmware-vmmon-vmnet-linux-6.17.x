#!/usr/bin/env bash
# uninstall-vmware-modules.sh
# Removes VMware kernel modules installed by install-vmware-modules.sh,
# with options to restore original VMware-shipped sources or do a clean sweep.
#
# Usage:
#   sudo ./uninstall-vmware-modules.sh
#
# Menu options:
#   1) Uninstall modules and restore original VMware sources
#      - Unloads vmmon, vmnet, vmw_vmci from the running kernel
#      - Removes installed .ko files
#      - Restores vmmon.tar / vmnet.tar from the oldest backup
#      - Runs vmware-modconfig to rebuild from original sources
#      - Removes systemd unit and module-load configs created by this tool
#
#   2) Fully uninstall VMware modules (no restore)
#      - Unloads and removes .ko files
#      - Removes all configuration written by this tool
#      - Does NOT touch /usr/lib/vmware/modules/source/ tarballs
#
#   3) Cancel

set -uo pipefail

VMWARE_MOD_DIR="/usr/lib/vmware/modules/source"
KVER="$(uname -r)"
MODULE_DIR="/lib/modules/${KVER}/misc"

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
    echo "  Run:  sudo ./uninstall-vmware-modules.sh"
    exit 1
fi

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          VMware Module Uninstaller                           ║"
echo "║  Removes modules installed by install-vmware-modules.sh     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
info "Running kernel : ${KVER}"
info "Module dir     : ${MODULE_DIR}"
echo ""

# ── Menu ──────────────────────────────────────────────────────────────────────
echo "  What would you like to do?"
echo ""
echo "  1) Uninstall modules and restore original VMware sources"
echo "     (removes .ko files, restores backup tarballs, rebuilds with vmware-modconfig)"
echo ""
echo "  2) Fully uninstall VMware modules without restoring originals"
echo "     (removes .ko files and all tool config; tarballs are left unchanged)"
echo ""
echo "  3) Cancel"
echo ""
read -rp "  Select [1/2/3, default=3]: " CHOICE
CHOICE="${CHOICE:-3}"

case "${CHOICE}" in
    1|2) : ;;
    3|*)
        info "Cancelled. No changes made."
        exit 0
        ;;
esac

# ── Confirm ───────────────────────────────────────────────────────────────────
echo ""
if [[ "${CHOICE}" == "1" ]]; then
    warn "This will unload VMware modules, remove installed .ko files, restore"
    warn "the original VMware source tarballs, and remove tool-managed configs."
else
    warn "This will unload VMware modules, remove installed .ko files, and"
    warn "remove all configuration written by install-vmware-modules.sh."
    warn "The VMware source tarballs in ${VMWARE_MOD_DIR} will not be changed."
fi
echo ""
read -rp "  Are you sure? [y/N]: " CONFIRM
if [[ ! "${CONFIRM}" =~ ^[Yy]$ ]]; then
    info "Cancelled. No changes made."
    exit 0
fi

# ── Step 1: Remove DKMS registrations (if any) ───────────────────────────────
section "Checking for DKMS registrations"

VMWARE_VER=""
if command -v vmware &>/dev/null; then
    VMWARE_VER=$(vmware --version 2>/dev/null | grep -oP '[\d.]+' | head -1 || true)
fi
if [[ -z "${VMWARE_VER}" ]]; then
    VMWARE_VER=$(grep -oP 'version="\K[^"]+' "${VMWARE_MOD_DIR}/modules.xml" 2>/dev/null | head -1 || true)
fi

if command -v dkms &>/dev/null; then
    for mod in vmmon vmnet; do
        # Check all registered versions (not just the current one)
        while IFS= read -r dkms_line; do
            if [[ -n "${dkms_line}" ]]; then
                VER=$(echo "${dkms_line}" | grep -oP "${mod}/\K[^,]+" | head -1 || true)
                if [[ -n "${VER}" ]]; then
                    info "Removing DKMS registration: ${mod}/${VER}"
                    dkms remove "${mod}/${VER}" --all 2>/dev/null && ok "Removed DKMS: ${mod}/${VER}" || warn "Could not remove DKMS entry for ${mod}/${VER}"
                    # Also remove the source tree
                    DKMS_SRC="/usr/src/${mod}-${VER}"
                    if [[ -d "${DKMS_SRC}" ]]; then
                        rm -rf "${DKMS_SRC}"
                        ok "Removed DKMS source tree: ${DKMS_SRC}"
                    fi
                fi
            fi
        done < <(dkms status "${mod}" 2>/dev/null | grep "^${mod}" || true)
    done
    ok "DKMS check complete"
else
    info "DKMS not installed — skipping DKMS cleanup"
fi

# ── Step 2: Unload modules ────────────────────────────────────────────────────
section "Unloading VMware kernel modules"

for mod in vmnet vmmon vmw_vmci; do
    if lsmod 2>/dev/null | grep -q "^${mod} "; then
        if modprobe -r "${mod}" 2>/dev/null || rmmod "${mod}" 2>/dev/null; then
            ok "Unloaded: ${mod}"
        else
            warn "Could not unload ${mod} (may be in use by a running VM)"
        fi
    else
        info "${mod} was not loaded — skipping"
    fi
done

# ── Step 4: Remove installed .ko files ───────────────────────────────────────
section "Removing installed module files"

for mod in vmmon vmnet; do
    ko="${MODULE_DIR}/${mod}.ko"
    if [[ -f "${ko}" ]]; then
        rm -f "${ko}"
        ok "Removed: ${ko}"
    else
        info "Not found (already removed?): ${ko}"
    fi
done

depmod -a "${KVER}"
ok "depmod -a done"

# ── Step 5: Remove tool-managed configs ───────────────────────────────────────
section "Removing tool-managed configuration files"

CONFIGS=(
    "/etc/modules-load.d/vmware.conf"
    "/etc/modprobe.d/vmware.conf"
    "/etc/systemd/system/vmware.service"
)

for cfg in "${CONFIGS[@]}"; do
    if [[ -f "${cfg}" ]]; then
        rm -f "${cfg}"
        ok "Removed: ${cfg}"
    else
        info "Not found: ${cfg}"
    fi
done

if systemctl list-unit-files vmware.service &>/dev/null; then
    systemctl disable vmware.service 2>/dev/null && ok "vmware.service disabled" || true
    systemctl daemon-reload
    ok "systemd daemon reloaded"
fi

# ── Step 6 (option 1 only): Restore original VMware sources ───────────────────
if [[ "${CHOICE}" == "1" ]]; then
    section "Restoring original VMware source tarballs"

    # Find oldest backup
    BACKUPS=($(ls -d "${VMWARE_MOD_DIR}"/backup-* 2>/dev/null | sort))
    if [[ ${#BACKUPS[@]} -eq 0 ]]; then
        warn "No backups found in ${VMWARE_MOD_DIR}."
        warn "Cannot restore originals — run restore-original-vmware-modules.sh manually."
    else
        OLDEST="${BACKUPS[0]}"
        info "Using backup: ${OLDEST}"
        for tarname in vmmon.tar vmnet.tar; do
            src="${OLDEST}/${tarname}"
            dst="${VMWARE_MOD_DIR}/${tarname}"
            if [[ -f "${src}" ]]; then
                cp "${src}" "${dst}"
                ok "Restored: ${dst}"
            else
                warn "Backup tarball not found: ${src}"
            fi
        done

        # Rebuild from restored originals using VMware's own modconfig
        if command -v vmware-modconfig &>/dev/null; then
            section "Rebuilding modules from restored originals"
            info "Running vmware-modconfig --console --install-all ..."
            if vmware-modconfig --console --install-all; then
                ok "VMware modules rebuilt from original sources"
            else
                warn "vmware-modconfig returned non-zero. Check output above."
                warn "You may need to reboot or run vmware-modconfig manually."
            fi
        else
            warn "vmware-modconfig not found — skipping rebuild."
            warn "To rebuild, run: sudo vmware-modconfig --console --install-all"
        fi
    fi
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
if [[ "${CHOICE}" == "1" ]]; then
    echo "║  Uninstall + restore complete.                               ║"
    echo "║  VMware Workstation will use its own (original) modules.     ║"
else
    echo "║  Uninstall complete.                                         ║"
    echo "║  VMware kernel modules and configs have been removed.        ║"
fi
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
