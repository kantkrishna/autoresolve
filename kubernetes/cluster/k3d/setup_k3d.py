"""
kubernetes/cluster/k3d/setup_k3d.py

Automates provisioning of the k3d cluster with normalized line-ending output.
"""

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

# Enforce UTF-8 in Windows PowerShell to prevent emoji/charmap crashes
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def run_command(command: list, description: str):
    print(f"[INFO] {description}...")
    try:
        # Use errors='replace' to safely handle unexpected Windows byte streams
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
    # Idempotent Directory Creation & Path Injection
    user_home = Path.home()
    data_dir = user_home / ".autoresolve" / "postgres-data"
    
    print(f"[INFO] Securing persistent data directory at: {data_dir}")
    # Create the directory safely (fails silently if it already exists)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Inject into the environment. We use .as_posix() to safely convert 
    # Windows backslashes (C:\) to forward slashes (C:/) which Docker prefers.
    os.environ["AUTORESOLVE_DATA_DIR"] = data_dir.as_posix()

    # Ensure the Timezone ConfigMap exists k3d Cluster Provisioning
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    env_path = base_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    
    tz = os.getenv("CLUSTER_TIMEZONE", "Asia/Kolkata")
    print(f"[INFO] Loaded CLUSTER_TIMEZONE={tz} for K3d virtual nodes.")
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    k3d_config = base_dir / "cluster" / "k3d" / "k3d-config.yaml"

    # Updated paths based on your new file locations
    namespaces_file = base_dir / "lab" / "namespaces.yaml"
    netpol_file = base_dir / "lab" / "network-policy.yaml"

    print("==================================================")
    print("[🚀] AutoResolve - k3d Cluster Provisioning")
    print("==================================================\n")

    # Step 1: Create Cluster
    if "autoresolve-lab" not in subprocess.getoutput("k3d cluster list"):
        run_command(
            ["k3d", "cluster", "create", "--config", str(k3d_config)],
            "Creating lightweight k3d cluster (autoresolve-lab)"
        )
    else:
        print("[INFO] Cluster 'autoresolve-lab' already exists. Skipping creation.")

    # Step 2: Apply Namespaces
    run_command(
        ["kubectl", "apply", "-f", str(namespaces_file)],
        "Provisioning isolated namespaces (autoresolve-ai & boutique-demo)"
    )

    # Step 3: Apply Network Policies
    run_command(
        ["kubectl", "apply", "-f", str(netpol_file)],
        "Applying Zero-Trust Network Policies"
    )

    print("\n==================================================")
    print("[SUCCESS] k3d Production Engineering Lab Successfully Setup!")
    print("==================================================")

if __name__ == "__main__":
    main()