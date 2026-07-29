# scripts/force-reset-lab.py

# This script performs a complete teardown and rebuild of the AutoResolve lab
# environment. It will destroy all local infrastructure, including the k3d cluster,
# Docker images, and persistent volumes.
# ‼️⚠️WARNING: This script will destroy all local infrastructure and data.‼️
# ‼️⚠️Use with caution.‼️

# Prerequisites to be run: Docker Desktop (or equivalent Docker daemon), k3d, kubectl,
# and Poetry.
# Usage: poetry run python scripts/force-reset-lab.py

# 1. Executes destroy_k3d.py to wipe the autoresolve-lab cluster.
# 2. Executes setup_k3d.py to build a fresh cluster and apply network policies.
# 3. Executes deploy_workload.py to deploy the Google Online Boutique and Prometheus.
# 4. Executes alert_routing.py and apply_rbac.py for routing and zero-trust security.
# 5. Executes deploy_infra.py for stateful databases (Kafka, Postgres, Qdrant).
# 6. Executes deploy_core.py to build the new autoresolve:latest Docker image and deploy
#    the AI gateway/workers.
# 7. Validates the health of all namespaces.

import subprocess
import sys
from pathlib import Path


def run_phase(script_path: str, description: str):
    print(f"\n[🚀] Starting: {description}")
    try:
        # Executes the script using the current Poetry Python environment
        subprocess.run([sys.executable, script_path], check=True)
        print(f"[✅] Success: {description}")
    except subprocess.CalledProcessError as e:
        print(f"[❌] FATAL ERROR during {description}.")
        print("Halting orchestration to prevent cascading failures.")
        sys.exit(1)

def main():
    print("=======================================================")
    print("[☢️]  NUKE AND PAVE: AutoResolve K8s Native Lab Recovery")
    print("=======================================================\n")
    print("This will completely wipe your local K3d state and rebuild it natively.")
    
    # Explicit user confirmation gate
    response = input(
        "[⚠️] Are you sure you want to proceed? This cannot be undone. (y/N): "
    ).strip().lower()
    
    if response not in ['y', 'yes']:
        print("\n[*] Aborting force-reset. No changes were made to your environment.")
        sys.exit(0)

    print("\n[*] Confirmation received. Initiating destruction sequence...")

    base_dir = Path(__file__).resolve().parent.parent
    
    # Phase 1: Teardown & Provisioning
    run_phase(str(base_dir / "kubernetes/cluster/k3d/destroy_k3d.py"), "Teardown Lab")
    run_phase(str(base_dir / "kubernetes/cluster/k3d/setup_k3d.py"), "Cluster Bootstrap")
    
    # Phase 2: Workload
    run_phase(str(base_dir / "kubernetes/lab/deploy_workload.py"), "Deploy Target Workload")
    
    # Phase 3 & 4: Observability & Webhooks
    run_phase(str(base_dir / "kubernetes/lab/alert_routing.py"), "Configure Alert Routing")
    
    # Phase 5: Core AI Platform
    run_phase(str(base_dir / "scripts/apply_rbac.py"), "Apply Zero-Trust RBAC")
    run_phase(str(base_dir / "kubernetes/lab/deploy_infra.py"), "Provision Stateful Datastores")
    run_phase(str(base_dir / "kubernetes/lab/deploy_core.py"), "Build & Deploy AutoResolve Core")
    print("\n[🎉] Force Reset Complete! The lab is fully operational.")

    subprocess.run([sys.executable, str(base_dir / "scripts/validate_health.py")])

    print("Next Steps:")
    print("1. Run your tunnel automation script: poetry run python scripts/start_tunnels.py")
    print("2. Launch the SRE Console: poetry run python scripts/incident_workflow.py")


if __name__ == "__main__":
    main()