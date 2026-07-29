# scripts/soft-rebuild-lab.py

# This script performs a non-destructive rebuild of the AutoResolve lab environment.
# It gracefully stops the existing Docker containers, restarts the Kubernetes cluster,
# and rebuilds the Docker Compose infrastructure while preserving the database volumes.

# Prerequisites to be run: Docker Desktop (or equivalent Docker daemon), k3d, kubectl,
# and Poetry.
# Usage: poetry run python scripts/soft-rebuild-lab.py

# 1. Gracefully stops the autoresolve-lab k3d cluster and any local docker-compose
#    containers.
# 2. Restarts the cluster (preserving persistent volumes and databases).
# 3. Synchronizes network routing and RBAC idempotently.
# 4. Triggers deploy_core.py to build a fresh Docker image with your new Python code and
#    perform a rollout restart of the AI worker pods.
# 5. Validates the health of all namespaces.

import subprocess
import sys
from pathlib import Path

def run_command(cmd_list: list, description: str):
    print(f"\n[🔄] {description}...")
    try:
        subprocess.run(cmd_list, check=True)
    except subprocess.CalledProcessError:
        print(f"[❌] Failed: {description}")
        sys.exit(1)

def main():
    base_dir = Path(__file__).resolve().parent.parent
    sys_exe = sys.executable
    
    print("Initiating Non-Destructive Soft Rebuild...")
    
    # 1. Graceful Stop
    run_command(["k3d", "cluster", "stop", "autoresolve-lab"], "Stopping k3d cluster")
    # If a local docker-compose was used for testing, bring it down safely
    subprocess.run(["docker", "compose", "down"], cwd=str(base_dir), capture_output=True)
    
    # 2. Restart Cluster (Preserves PVs/Databases)
    run_command(["k3d", "cluster", "start", "autoresolve-lab"], "Starting k3d cluster")
    
    # 3. Synchronize Routing & RBAC (Non-destructive idempotency)
    subprocess.run([sys_exe, str(base_dir / "kubernetes/lab/alert_routing.py")], check=True)
    subprocess.run([sys_exe, str(base_dir / "scripts/apply_rbac.py")], check=True)
    
    # 4. Rebuild & Redeploy Core Application
    print("\n[📦] Rebuilding AI Core Docker Images with new code...")
    subprocess.run([sys_exe, str(base_dir / "kubernetes/lab/deploy_core.py")], check=True)

    subprocess.run([sys.executable, str(base_dir / "scripts/validate_health.py")])
    print("\n[🎉] Soft Rebuild Complete! Persistent data preserved.")

    print("Next Steps:")
    print("1. Run your tunnel automation script: poetry run python scripts/start_tunnels.py")
    print("2. Launch the SRE Console: poetry run python scripts/incident_workflow.py")

    
if __name__ == "__main__":
    main()