# scripts/wake-up-lab.py

# This script is designed to wake up the AutoResolve Lab after a system sleep or
# hibernation event. It ensures that the k3d cluster is restarted, the kubeconfig is
# refreshed, and the Kubernetes API is responsive.

import subprocess
import sys

print("[INFO] Waking up AutoResolve Lab after system sleep...")

try:
    # 1. Gracefully stop the cluster
    subprocess.run(["k3d", "cluster", "stop", "autoresolve-lab"], check=True)
    
    # 2. Start it back up (this forces Docker to refresh the network bridge)
    subprocess.run(["k3d", "cluster", "start", "autoresolve-lab"], check=True)
    
    # 3. Force-write the fresh, corrected connection into kubeconfig
    subprocess.run(["k3d", "kubeconfig", "write", "autoresolve-lab", "--overwrite"], check=True)
    subprocess.run(["k3d", "kubeconfig", "merge", "autoresolve-lab", "--kubeconfig-switch-context"], check=True)
    
    # 4. Verify connection
    print("\n[SUCCESS] Lab is awake and API is responsive:")
    subprocess.run(["kubectl", "get", "nodes"])

except subprocess.CalledProcessError as e:
    print("[ERROR] Failed to wake up the lab. Ensure Docker Desktop is running.")
    sys.exit(1)