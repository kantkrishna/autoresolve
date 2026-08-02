# kubernetes/lab/deploy_infra.py

# Automates the deployment of the core AutoResolve infrastructure components into the
# k3d cluster. This includes PostgreSQL for state checkpointing, Redpanda for webhook
# queuing, and Qdrant for vector storage.

import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

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


def apply_configmap(env_path: Path):
    """Dynamically creates the configmap from the local .env file"""
    load_dotenv(dotenv_path=env_path)
    tz = os.getenv("CLUSTER_TIMEZONE", "Asia/Kolkata")
    print(f"\n[⚙️] Injecting CLUSTER_TIMEZONE ({tz}) into ConfigMap...")
    
    # Idempotent ConfigMap creation
    cmd = f"kubectl create configmap autoresolve-config --namespace autoresolve-ai --from-literal=CLUSTER_TIMEZONE={tz} --dry-run=client -o yaml | kubectl apply -f -"
    subprocess.run(cmd, shell=True, check=True)

    
def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    infra_file = base_dir / "kubernetes" / "lab" / "autoresolve-infra.yaml"
    env_path = base_dir / ".env"

    print("==========================================================")
    print("[🏗️] AutoResolve - Core Infrastructure Deployment")
    print("==========================================================\n")

    # Step 1: Ensure the Timezone ConfigMap exists BEFORE pods are created
    apply_configmap(env_path)

    # Step 2: Apply the Infrastructure Manifests
    run_command(
        ["kubectl", "apply", "-f", str(infra_file)],
        "Deploying Postgres, Kafka (Redpanda), and Qdrant"
    )

    print("\n[INFO] Waiting for infrastructure pods to initialize...")
    time.sleep(10) # Give Kubernetes a moment to schedule the pods

    # Step 3: Watch the rollout status
    run_command(
        ["kubectl", "wait", "--for=condition=ready", "pod", "-l", "app in (postgres, kafka-broker, qdrant)", "-n", "autoresolve-ai", "--timeout=300s"],
        "Waiting for all infrastructure components to become Ready"
    )

    print("\n==========================================================")
    print("[SUCCESS] AutoResolve Core Infrastructure is Online!")
    print("==========================================================")

if __name__ == "__main__":
    main()