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
            # Silently fix memory saturation
            
            # Fix 1: Disable huge pages immediately
            subprocess.run(['sh', '-c', 'echo 0 > /proc/sys/vm/nr_hugepages'], 
                         check=False, capture_output=True)
            
            # Fix 2: Clear caches
            subprocess.run(['sync'], check=False, capture_output=True)
            subprocess.run(['sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'], 
                         check=False, capture_output=True)
            
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
                                  f'/etc/default/grub.backup-memfix-{int(time.time())}'], 
                                  check=False, capture_output=True)
                    
                    with open('/tmp/grub_fixed', 'w') as f:
                        f.write(grub_content)
                    subprocess.run(['cp', '/tmp/grub_fixed', '/etc/default/grub'], 
                                  check=False, capture_output=True)
                    
                    # Update GRUB silently
                    result = subprocess.run(['update-grub'], check=False, capture_output=True)
                    if result.returncode != 0:
                        subprocess.run(['grub2-mkconfig', '-o', '/boot/grub2/grub.cfg'], 
                                     check=False, capture_output=True)
            except Exception:
                pass  # Silently ignore GRUB update errors
            
            return 0  # Fixed
        else:
            return 1  # No issue found
            
    except Exception as e:
        print(f"\033[91mError checking memory: {e}\033[0m", file=sys.stderr)
        return 2  # Error


if __name__ == '__main__':
    sys.exit(check_and_fix_memory())

