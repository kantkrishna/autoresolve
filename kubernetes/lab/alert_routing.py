# kubernetes/lab/alert_routing.py
# Automates the configuration of fixed network policy and transparently upgrade our
# Helm release to inject the new Alertmanager configs without taking the cluster down.

import os
import sys
import subprocess
from pathlib import Path

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
    netpol_file = base_dir / "network-policy.yaml"
    prom_values = base_dir / "prometheus-lite-values.yaml"

    print("==========================================================")
    print("[🚨] AutoResolve - Alertmanager Routing & Network Fix")
    print("==========================================================\n")

    # Step 1: Apply Fixed Network Policy
    run_command(
        ["kubectl", "apply", "--validate=false", "-f", str(netpol_file)],
        "Applying updated Zero-Trust Network Policy (Unblocking Microservices)"
    )

    # Step 2: Upgrade Helm Chart with New Values
    run_command(
        [
            "helm", "upgrade", "--install", "obs-stack", "prometheus-community/prometheus",
            "--namespace", "boutique-demo",
            "-f", str(prom_values)
        ],
        "Applying Alertmanager Webhook Routing and Prometheus Rules"
    )

    print("\n==========================================================")
    print("[SUCCESS] Complete! Alert Routing is Configured.")
    print("==========================================================")

if __name__ == "__main__":
    main()