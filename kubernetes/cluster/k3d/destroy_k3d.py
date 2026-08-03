"""
kubernetes/cluster/k3d/destroy_k3d.py

Tears down the k3d Production Engineering Lab cluster to free system resources.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Enforce UTF-8 in Windows PowerShell to prevent emoji/charmap crashes
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def run_command(command: list, description: str):
    print(f"[INFO] {description}...")
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        for line in result.stdout.splitlines():
            print(f"       {line}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {' '.join(command)}")
        print(e.stdout)
        sys.exit(1)

def main():
    print("==================================================")
    print("[🛑] AutoResolve - Destroying k3d Cluster")
    print("==================================================\n")

    # Check if cluster exists before trying to delete it
    clusters = subprocess.getoutput("k3d cluster list")
    
    if "autoresolve-lab" in clusters:
        run_command(
            ["k3d", "cluster", "delete", "autoresolve-lab"],
            "Deleting k3d cluster (autoresolve-lab) and freeing resources"
        )

        data_dir = Path.home() / ".autoresolve" / "postgres-data"
        if data_dir.exists():
            print(f"\n[🧹] Performing Disk Hygiene: Scrubbing orphaned database volumes at {data_dir}...")
            try:
                # Recursively delete the directory and all its contents
                shutil.rmtree(data_dir)
                print("       [SUCCESS] Old persistent volumes securely deleted.")
            except Exception as e:
                print(f"       [WARNING] Could not completely delete files (they may be locked by Windows): {e}")
        
        print("\n==================================================")
        print("[SUCCESS] Cluster successfully destroyed! Ports and RAM are free.")
        print("==================================================")
    else:
        print("[INFO] Cluster 'autoresolve-lab' does not exist. Your environment is clean.")

if __name__ == "__main__":
    main()