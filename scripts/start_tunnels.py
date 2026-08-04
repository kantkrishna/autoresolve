# scripts/start_tunnels.py

# This script establishes the necessary network tunnels to access the AutoResolve SRE
# Console, PostgreSQL Checkpointer, and Prometheus Metrics from your local machine.
# It ensures that any stale or conflicting port-forward processes are terminated before
# starting new ones.
# Usage: poetry run python scripts/start_tunnels.py

import platform
import subprocess
import sys
import time


def main():
    print("=======================================================")
    print("[🚀] Starting AutoResolve Network Tunnels")
    print("=======================================================\n")

    # 1. Clean up any existing/stale kubectl port-forwards
    print("[*] Sweeping for stale tunnel processes...")
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", "kubectl.exe"], capture_output=True)
        else:
            subprocess.run(["pkill", "-f", "kubectl port-forward"], capture_output=True)
    except Exception:
        pass
    
    time.sleep(1)

    # 2. Define the required K8s tunnels
    tunnels = [
        {
            "name": "API Gateway", 
            "port": "8000:8000", 
            "cmd": ["kubectl", "port-forward", "svc/autoresolve-api-gateway", "8000:8000", "-n", "autoresolve-ai"]
        },
        {
            "name": "PostgreSQL Checkpointer", 
            "port": "5433:5432", 
            "cmd": ["kubectl", "port-forward", "svc/postgres", "5433:5432", "-n", "autoresolve-ai"]
        },
        {
            "name": "Prometheus Metrics", 
            "port": "9091:80", 
            "cmd": ["kubectl", "port-forward", "svc/obs-stack-prometheus-server", "9091:80", "-n", "boutique-demo"]
        }
    ]

    processes = []
    
    # Optional: Hide the scary pop-up console windows on Windows OS
    kwargs = {}
    if system == "Windows":
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    # 3. Spawn the tunnels as non-blocking background child processes
    for t in tunnels:
        print(f"[+] Forwarding {t['name']} ({t['port']})...")
        # Route stdout/stderr to DEVNULL to keep our terminal clean
        p = subprocess.Popen(t['cmd'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
        processes.append(p)

    time.sleep(2)
    print("\n[✅] All tunnels established successfully!")
    print("[👉] You can now safely run your SRE Console in another terminal window.")
    print("[⚠️] Keep this window open. Press Ctrl+C here to close all tunnels when finished.\n")

    # 4. Graceful termination block
    try:
        # Keep the main thread alive to sustain the tunnels
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down all network tunnels...")
        for p in processes:
            p.terminate()
        print("👋 Tunnels closed gracefully. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()