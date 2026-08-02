"""
kubernetes/cluster/k3d/destroy_k3d.py

Tears down the k3d Production Engineering Lab cluster to free system resources.
"""

import os
import sys
import subprocess

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
        print("\n==================================================")
        print("[SUCCESS] Cluster successfully destroyed! Ports and RAM are free.")
        print("==================================================")
    else:
        print("[INFO] Cluster 'autoresolve-lab' does not exist. Your environment is clean.")

if __name__ == "__main__":
    main()