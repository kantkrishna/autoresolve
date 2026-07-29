# kubernetes/lab/deploy_workload.py
# Automates deployment of the Google Online Boutique microservices demo and a
# lightweight Prometheus stack for the Production Engineering Lab.

import os
import sys
import subprocess
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
    base_dir = Path(__file__).resolve().parent
    prom_values = base_dir / "prometheus-lite-values.yaml"
    
    # Official Google Online Boutique Release Manifest
    BOUTIQUE_MANIFEST = "https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/main/release/kubernetes-manifests.yaml"

    print("==========================================================")
    print("🛍️ AutoResolve - Target Workload Deployment")
    print("==========================================================\n")

    # Step 1: Deploy Google Online Boutique
    run_command(
        ["kubectl", "apply", "-f", BOUTIQUE_MANIFEST, "-n", "boutique-demo"],
        "Deploying Google Online Boutique microservices to 'boutique-demo' namespace"
    )

    # Step 2: Add Helm Repositories
    run_command(
        ["helm", "repo", "add", "prometheus-community", "https://prometheus-community.github.io/helm-charts"],
        "Adding Prometheus Community Helm Repository"
    )
    run_command(
        ["helm", "repo", "update"],
        "Updating Helm Repositories"
    )

    # Step 3: Install Lightweight Prometheus Stack
    # We use upgrade --install so the script is idempotent (can be run multiple times safely)
    run_command(
        [
            "helm", "upgrade", "--install", "obs-stack", "prometheus-community/prometheus",
            "--namespace", "boutique-demo",
            "-f", str(prom_values)
        ],
        "Deploying Lightweight Prometheus & Alertmanager to 'boutique-demo'"
    )

    print("\n==========================================================")
    print("[SUCCESS] Production Engineering Lab Workload Deployed!")
    print("Note: It may take 2-3 minutes for all containers to pull and start.")
    print("==========================================================")

if __name__ == "__main__":
    main()