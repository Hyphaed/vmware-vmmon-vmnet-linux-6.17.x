# Troubleshooting Guide

This guide covers common issues when installing VMware modules on kernel 6.17.x and their solutions.

## Table of Contents

1. [Compilation Issues](#compilation-issues)
2. [Module Loading Issues](#module-loading-issues)
3. [VMware Startup Issues](#vmware-startup-issues)
4. [Performance Issues](#performance-issues)
5. [System-Specific Issues](#system-specific-issues)

---

## Compilation Issues

### Error: "Error extracting modules"

**Symptom:**
```
[✗] Error extracting modules
```

**Cause:** VMware module tar files are missing, corrupted, or inaccessible.

**Solution:**

1. **Verify VMware Installation:**
   ```bash
   ls -l /usr/lib/vmware/modules/source/
   ```
   You should see `vmmon.tar` and `vmnet.tar` files.

2. **Check File Permissions:**
   ```bash
   sudo ls -l /usr/lib/vmware/modules/source/
   ```
   If the files exist but can't be accessed, you may need to run the script with sudo:
   ```bash
   sudo bash scripts/install-vmware-modules.sh
   ```

3. **Reinstall VMware Workstation:**
   If the tar files are missing or corrupted:
   ```bash
   # Download VMware Workstation from official website
   # Then reinstall:
   sudo bash VMware-Workstation-*.bundle
   ```

4. **Check for Disk Space:**
   ```bash
   df -h /tmp
   ```
   Ensure you have at least 500MB free space in /tmp.

5. **Verify Tar Command:**
   ```bash
   which tar
   tar --version
   ```
   Ensure tar is installed and working.

### Error: "No such file or directory: linux/version.h"

**Symptom:**
```
fatal error: linux/version.h: No such file or directory
```

**Cause:** Kernel headers not installed or incorrect version.

**Solution:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install linux-headers-$(uname -r)

# Fedora/RHEL
sudo dnf install kernel-devel kernel-headers

# Arch Linux
sudo pacman -S linux-headers
```

### Error: "gcc: command not found"

**Symptom:**
```
make: gcc: command not found
```

**Cause:** Build tools not installed.

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install build-essential

# Fedora/RHEL
sudo dnf groupinstall "Development Tools"

# Arch Linux
sudo pacman -S base-devel
```

### Error: "objtool: ... falls through to next function"

**Symptom:**
```
objtool: phystrack.o: warning: objtool: PhysTrack_Add() falls through to next function
```

**Cause:** Patches not applied correctly.

**Solution:**
1. Verify patches were applied:
   ```bash
   grep "OBJECT_FILES_NON_STANDARD" vmmon-only/Makefile.kernel
   ```
2. Re-apply patches:
   ```bash
   bash scripts/apply-patches-6.17.sh /path/to/vmmon-only /path/to/vmnet-only
   ```

### Error: "Module.symvers not found"

**Symptom:**
```
WARNING: Symbol version dump ./Module.symvers is missing
```

**Cause:** Normal warning, can be ignored.

**Solution:** This warning is harmless. The modules will still work.

---

## Module Loading Issues

### Error: "modprobe: FATAL: Module vmmon not found"

**Symptom:**
```
modprobe: FATAL: Module vmmon not found in directory /lib/modules/6.17.0-5-generic
```

**Cause:** Module not installed or depmod not run.

**Solution:**
```bash
# Check if module exists
ls -l /lib/modules/$(uname -r)/misc/vmmon.ko

# If missing, copy it
sudo cp vmmon-only/vmmon.ko /lib/modules/$(uname -r)/misc/

# Update module dependencies
sudo depmod -a

# Try loading again
sudo modprobe vmmon
```

### Error: "Required key not available"

**Symptom:**
```
modprobe: ERROR: could not insert 'vmmon': Required key not available
```

**Cause:** Secure Boot is enabled and module is not signed.

**Solution (Option 1 - Disable Secure Boot):**
1. Reboot into BIOS/UEFI
2. Disable Secure Boot
3. Save and reboot

**Solution (Option 2 - Sign the module):**
```bash
# Generate signing key (if not exists)
sudo /usr/src/linux-headers-$(uname -r)/scripts/sign-file sha256 \
    /var/lib/shim-signed/mok/MOK.priv \
    /var/lib/shim-signed/mok/MOK.der \
    /lib/modules/$(uname -r)/misc/vmmon.ko

# Repeat for vmnet
sudo /usr/src/linux-headers-$(uname -r)/scripts/sign-file sha256 \
    /var/lib/shim-signed/mok/MOK.priv \
    /var/lib/shim-signed/mok/MOK.der \
    /lib/modules/$(uname -r)/misc/vmnet.ko
```

### Error: "Operation not permitted"

**Symptom:**
```
modprobe: ERROR: could not insert 'vmmon': Operation not permitted
```

**Cause:** Not running as root or SELinux/AppArmor blocking.

**Solution:**
```bash
# Run as root
sudo modprobe vmmon

# Check SELinux (if applicable)
sudo setenforce 0  # Temporary
sudo getenforce

# Check AppArmor (if applicable)
sudo aa-status
```

---

## VMware Startup Issues

### Error: "Could not open /dev/vmmon"

**Symptom:**
```
Could not open /dev/vmmon: No such file or directory.
Please make sure that the kernel module 'vmmon' is loaded.
```

**Cause:** vmmon module not loaded.

**Solution:**
```bash
# Load module
sudo modprobe vmmon

# Verify it's loaded
lsmod | grep vmmon

# Make it load at boot
echo "vmmon" | sudo tee -a /etc/modules
echo "vmnet" | sudo tee -a /etc/modules
```

### Error: "Unable to change virtual machine power state"

**Symptom:** VM fails to start with power state error.

**Cause:** Module version mismatch or VMware services not running.

**Solution:**
```bash
# Restart VMware services
sudo systemctl restart vmware

# Or manually
sudo /etc/init.d/vmware restart

# Verify services
sudo systemctl status vmware
```

### Error: "Transport (VMDB) error -14"

**Symptom:** VMware fails to start VMs with VMDB error.

**Cause:** Corrupted VMware configuration or stale lock files.

**Solution:**
```bash
# Stop VMware
sudo systemctl stop vmware

# Remove lock files
sudo rm -rf /tmp/vmware-*

# Restart VMware
sudo systemctl start vmware
```

---

## Performance Issues

### Issue: Slow VM Performance

**Symptoms:**
- VMs running slower than expected
- High CPU usage on host

**Solutions:**

1. **Enable VT-x/AMD-V in BIOS:**
   ```bash
   # Check if enabled
   egrep -c '(vmx|svm)' /proc/cpuinfo
   # Should return > 0
   ```

2. **Allocate more resources:**
   - Increase VM RAM
   - Increase CPU cores
   - Use paravirtualized drivers

3. **Check host CPU governor:**
   ```bash
   cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   # Should be "performance" for best results
   ```

### Issue: Network Performance Problems

**Symptoms:**
- Slow network in VMs
- Packet loss

**Solutions:**

1. **Verify vmnet is loaded:**
   ```bash
   lsmod | grep vmnet
   ```

2. **Check network configuration:**
   ```bash
   sudo vmware-networks --status
   ```

3. **Restart networking:**
   ```bash
   sudo vmware-networks --stop
   sudo vmware-networks --start
   ```

---

## System-Specific Issues

### Ubuntu/Debian: DKMS Issues

**Symptom:** Modules don't rebuild after kernel update.

**Solution:**
```bash
# Remove old DKMS entries
sudo dkms remove vmware/17.6.4 --all

# Manually rebuild
sudo bash scripts/install-vmware-modules.sh
```

### Fedora/RHEL: SELinux Denials

**Symptom:** SELinux blocks module loading.

**Solution:**
```bash
# Check for denials
sudo ausearch -m avc -ts recent | grep vmware

# Create policy (if needed)
sudo ausearch -m avc -ts recent | grep vmware | audit2allow -M vmware_custom
sudo semodule -i vmware_custom.pp
```

### Arch Linux: Module Signing

**Symptom:** Modules fail to load on Arch with custom kernel.

**Solution:**
```bash
# Install kernel headers
sudo pacman -S linux-headers

# Rebuild modules
cd /tmp
tar -xf /usr/lib/vmware/modules/source/vmmon.tar
cd vmmon-only
make
sudo make install
```

---

## Diagnostic Commands

### Collect System Information

```bash
# Kernel version
uname -r

# VMware version
vmware --version

# Module information
modinfo vmmon
modinfo vmnet

# Loaded modules
lsmod | grep vm

# Kernel messages
dmesg | grep -i vmware | tail -20

# VMware services
systemctl status vmware

# Check for errors
journalctl -xe | grep -i vmware
```

### Create Debug Log

```bash
# Create comprehensive debug log
{
    echo "=== System Information ==="
    uname -a
    echo ""
    
    echo "=== VMware Version ==="
    vmware --version
    echo ""
    
    echo "=== Kernel Modules ==="
    lsmod | grep vm
    echo ""
    
    echo "=== Module Info ==="
    modinfo vmmon
    echo ""
    modinfo vmnet
    echo ""
    
    echo "=== Kernel Messages ==="
    dmesg | grep -i vmware | tail -50
    echo ""
    
    echo "=== VMware Services ==="
    systemctl status vmware
    echo ""
    
} > vmware-debug.log

cat vmware-debug.log
```

---

## Display Issues

### Issue: Top Bar Doesn't Hide on First VM Boot (Wayland)

**Note:** With optimized modules, top bar hiding works ~90% of the time on Wayland. This troubleshooting section addresses the remaining ~10% of cases where initialization timing causes issues.

**Symptom:** 
First time powering on a VM, the top bar remains visible in fullscreen mode. Restarting the VM fixes it. This occurs occasionally even with optimized modules.

**Cause:** 
Module initialization race condition - VMware may start before kernel modules fully initialize and register with the system. The optimizations reduce CPU overhead, which helps the compositor respond better, but timing issues can still occur on first boot.

**Permanent Fix:**
This fix is already included in v1.0.5+ installations via `/etc/modules-load.d/vmware.conf` and `/etc/modprobe.d/vmware.conf`.

**Manual Fix (if upgraded from older version):**
```bash
# Ensure modules load early at boot
sudo tee /etc/modules-load.d/vmware.conf > /dev/null << 'EOF'
# VMware kernel modules
# Load early to ensure availability before VMware starts
vmmon
vmnet
EOF

# Configure load order
sudo tee /etc/modprobe.d/vmware.conf > /dev/null << 'EOF'
# VMware kernel module configuration
# Ensure vmmon loads before vmnet
softdep vmnet pre: vmmon
EOF

# Apply changes
sudo depmod -a

# Reboot to apply
sudo reboot
```

**Quick Workaround (without reboot):**
```bash
# Unload and reload modules in correct order
sudo modprobe -r vmnet vmmon
sudo modprobe vmmon
sudo modprobe vmnet

# Restart VMware
sudo systemctl restart vmware.service
```

---

## Getting Help

If you still have issues after trying these solutions:

1. **Check existing issues:** [GitHub Issues](https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/issues)

2. **Create a new issue** with:
   - Exact kernel version (`uname -r`)
   - VMware version (`vmware --version`)
   - Distribution and version
   - Complete error messages
   - Output of diagnostic commands above

3. **Include logs:**
   - `dmesg | grep -i vmware`
   - Compilation output (if build failed)
   - `vmware-debug.log` (from above)

---

## Additional Resources

- [VMware Communities](https://communities.vmware.com/)
- [Linux Kernel Documentation](https://www.kernel.org/doc/)
- [Project GitHub](https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x)

---

**Note:** Always backup your system before making kernel-level changes.
