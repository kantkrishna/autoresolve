# kubernetes/lab/deploy_infra.py

# Automates the deployment of the core AutoResolve infrastructure components into the
# k3d cluster. This includes PostgreSQL for state checkpointing, Redpanda for webhook
# queuing, and Qdrant for vector storage.

import sys
import time
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
    base_dir = Path(__file__).resolve().parent.parent.parent
    infra_file = base_dir / "kubernetes" / "lab" / "autoresolve-infra.yaml"

    print("==========================================================")
    print("🏗️ AutoResolve - Core Infrastructure Deployment")
    print("==========================================================\n")

    # Step 1: Apply the Infrastructure Manifests
    run_command(
        ["kubectl", "apply", "-f", str(infra_file)],
        "Deploying Postgres, Kafka (Redpanda), and Qdrant"
    )

    print("\n[INFO] Waiting for infrastructure pods to initialize...")
    time.sleep(10) # Give Kubernetes a moment to schedule the pods

    # Step 2: Watch the rollout status
    run_command(
        ["kubectl", "wait", "--for=condition=ready", "pod", "-l", "app in (postgres, kafka-broker, qdrant)", "-n", "autoresolve-ai", "--timeout=120s"],
        "Waiting for all infrastructure components to become Ready"
    )

    print("\n==========================================================")
    print("[SUCCESS] AutoResolve Core Infrastructure is Online!")
    print("==========================================================")

if __name__ == "__main__":
    main()