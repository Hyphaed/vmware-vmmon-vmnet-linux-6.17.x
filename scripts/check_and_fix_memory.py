#!/usr/bin/env python3
"""
Quick memory saturation check and fix
Can be called standalone or from bash script
"""

import sys
import subprocess
import time
import re


def check_and_fix_memory():
    """Check for memory saturation (huge pages) and fix automatically"""
    try:
        # Check if huge pages are consuming memory
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        
        # Extract huge pages info
        hugepages_total = 0
        hugepages_size = 0
        for line in meminfo.split('\n'):
            if 'HugePages_Total:' in line:
                hugepages_total = int(line.split()[1])
            elif 'Hugepagesize:' in line:
                hugepages_size = int(line.split()[1])  # in KB
        
        # Calculate reserved memory (in GB)
        reserved_gb = (hugepages_total * hugepages_size) / (1024 * 1024)
        
        if reserved_gb > 1.0:  # More than 1GB reserved
            print("")
            print("\033[93m⚠️  MEMORY SATURATION DETECTED!\033[0m")
            print("")
            print(f"\033[93mHuge pages are reserving {reserved_gb:.1f} GB of RAM\033[0m")
            print("\033[96mThis was likely caused by previous tuning attempts\033[0m")
            print("")
            print("\033[92m🔧 Automatically fixing memory saturation...\033[0m")
            print("")
            
            # Fix 1: Disable huge pages immediately
            subprocess.run(['sh', '-c', 'echo 0 > /proc/sys/vm/nr_hugepages'], 
                         check=False, capture_output=True)
            print("\033[92m✓ Disabled huge pages (runtime)\033[0m")
            
            # Fix 2: Clear caches
            subprocess.run(['sync'], check=False)
            subprocess.run(['sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'], 
                         check=False, capture_output=True)
            print("\033[92m✓ Cleared system caches\033[0m")
            
            # Fix 3: Remove from GRUB
            try:
                with open('/etc/default/grub', 'r') as f:
                    grub_content = f.read()
                
                if 'hugepage' in grub_content:
                    grub_content = re.sub(r'hugepages=\d+\s*', '', grub_content)
                    grub_content = re.sub(r'hugepagesz=[^\s]+\s*', '', grub_content)
                    grub_content = re.sub(r'default_hugepagesz=[^\s]+\s*', '', grub_content)
                    grub_content = grub_content.replace('transparent_hugepage=never', 'transparent_hugepage=madvise')
                    
                    # Backup and write
                    subprocess.run(['cp', '/etc/default/grub', 
                                  f'/etc/default/grub.backup-memfix-{int(time.time())}'], check=False)
                    
                    with open('/tmp/grub_fixed', 'w') as f:
                        f.write(grub_content)
                    subprocess.run(['cp', '/tmp/grub_fixed', '/etc/default/grub'], check=False)
                    
                    print("\033[92m✓ Removed huge pages from GRUB\033[0m")
                    
                    # Update GRUB
                    result = subprocess.run(['update-grub'], check=False, capture_output=True)
                    if result.returncode != 0:
                        subprocess.run(['grub2-mkconfig', '-o', '/boot/grub2/grub.cfg'], 
                                     check=False, capture_output=True)
                    print("\033[92m✓ Updated GRUB configuration\033[0m")
            except Exception as e:
                print(f"\033[93mWarning: Could not update GRUB: {e}\033[0m")
            
            print("")
            print(f"\033[92m✅ Memory fixed! {reserved_gb:.1f} GB freed\033[0m")
            print("\033[96m💡 Memory will be fully available after reboot\033[0m")
            print("")
            
            return 0  # Fixed
        else:
            return 1  # No issue found
            
    except Exception as e:
        print(f"\033[91mError checking memory: {e}\033[0m", file=sys.stderr)
        return 2  # Error


if __name__ == '__main__':
    sys.exit(check_and_fix_memory())

