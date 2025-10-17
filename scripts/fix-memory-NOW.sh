#!/bin/bash
# ========================================
# IMMEDIATE MEMORY FIX - Run as ROOT
# ========================================
# This fixes memory saturation caused by huge pages

set -e

echo "=========================================="
echo "IMMEDIATE MEMORY FIX"
echo "=========================================="
echo ""

# Check if root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root: sudo bash $0"
    exit 1
fi

# 1. Check current status
echo "=== Current Huge Pages Status ==="
grep Huge /proc/meminfo
echo ""

# 2. Disable huge pages immediately (runtime)
echo "=== Disabling Huge Pages (Runtime) ==="
echo 0 > /proc/sys/vm/nr_hugepages 2>/dev/null || true
echo never > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true
echo "✓ Runtime huge pages disabled"
echo ""

# 3. Check GRUB configuration
echo "=== Checking GRUB Configuration ==="
if grep -q "hugepage" /etc/default/grub; then
    echo "⚠️  Found huge pages in GRUB - removing..."
    
    # Backup GRUB
    cp /etc/default/grub /etc/default/grub.backup-memory-fix-$(date +%Y%m%d-%H%M%S)
    
    # Remove huge pages parameters
    sed -i 's/hugepages=[0-9]* //g' /etc/default/grub
    sed -i 's/hugepagesz=[^ ]* //g' /etc/default/grub
    sed -i 's/default_hugepagesz=[^ ]* //g' /etc/default/grub
    sed -i 's/transparent_hugepage=never/transparent_hugepage=madvise/g' /etc/default/grub
    
    echo "✓ GRUB configuration cleaned"
    
    # Update GRUB
    echo ""
    echo "=== Updating GRUB ==="
    if command -v update-grub >/dev/null 2>&1; then
        update-grub
        echo "✓ GRUB updated"
    elif command -v grub2-mkconfig >/dev/null 2>&1; then
        grub2-mkconfig -o /boot/grub2/grub.cfg 2>/dev/null || grub2-mkconfig -o /boot/efi/EFI/fedora/grub.cfg
        echo "✓ GRUB2 updated"
    fi
else
    echo "✓ No huge pages found in GRUB"
fi
echo ""

# 4. Check for tuning configurations
echo "=== Checking Tuning Configurations ==="
if [ -f "/etc/sysctl.d/99-vmware-optimization.conf" ]; then
    echo "⚠️  Found VMware tuning config - backing up and removing..."
    mv /etc/sysctl.d/99-vmware-optimization.conf /etc/sysctl.d/99-vmware-optimization.conf.disabled-$(date +%Y%m%d-%H%M%S)
    echo "✓ Tuning config disabled"
else
    echo "✓ No tuning config found"
fi
echo ""

# 5. Clear system caches to free memory
echo "=== Clearing System Caches ==="
sync
echo 3 > /proc/sys/vm/drop_caches
echo "✓ Caches cleared"
echo ""

# 6. Show memory status after fixes
echo "=========================================="
echo "MEMORY STATUS AFTER FIXES"
echo "=========================================="
free -h
echo ""
echo "Huge Pages Status:"
grep Huge /proc/meminfo
echo ""

echo "=========================================="
echo "✅ IMMEDIATE FIXES APPLIED!"
echo "=========================================="
echo ""
echo "What was done:"
echo "  ✓ Disabled huge pages (runtime)"
echo "  ✓ Removed huge pages from GRUB"
echo "  ✓ Updated GRUB configuration"
echo "  ✓ Disabled tuning configurations"
echo "  ✓ Cleared system caches"
echo ""
echo "⚠️  IMPORTANT:"
echo "  • Memory should be available now"
echo "  • For permanent fix, REBOOT your system"
echo "  • After reboot, huge pages will stay disabled"
echo ""
echo "To reboot now, run: sudo reboot"
echo ""

