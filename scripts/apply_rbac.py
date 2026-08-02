# scripts/apply_rbac.py

# Automates the application of RBAC policies to the k3d cluster for the Production
# Engineering Lab. This script ensures that the Prometheus and Alertmanager components
# have the necessary permissions to operate securely within the cluster.

import sys
import subprocess
from pathlib import Path

# Enforce UTF-8 to prevent Windows terminal crashes
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
    base_dir = Path(__file__).resolve().parent.parent
    rbac_file = base_dir / "kubernetes" / "lab" / "rbac.yaml"

    print("==========================================================")
    print("[🔐] AutoResolve - Zero-Trust Security Initialization")
    print("==========================================================\n")

    run_command(
        ["kubectl", "apply", "-f", str(rbac_file)],
        "Applying Least-Privilege RBAC Policies"
    )

    print("\n==========================================================")
    print("[SUCCESS] AI Service Account securely provisioned!")
    print("==========================================================")

if __name__ == "__main__":
    main()