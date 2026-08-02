# scripts/validate_health.py

# This script validates the health of the AutoResolve lab environment by checking the
# readiness of all pods in the critical namespaces.

# Usage: poetry run python scripts/validate_health.py

import subprocess
import sys


def check_namespace_health(namespace: str, timeout_seconds: int = 300):
    print(f"\n[⏳] Validating health of namespace: {namespace}...")

    try:
        # 1. Dynamically get all deployments in the target namespace
        deps_output = subprocess.check_output(
            ["kubectl", "get", "deployments", "-n", namespace, "-o", "jsonpath={.items[*].metadata.name}"],
            text=True,
            encoding="utf-8"
        ).strip()
        
        if not deps_output:
            print(f"[ℹ️] No deployments found in '{namespace}'.")
            return
            
        deployments = deps_output.split()
        
        # 2. Check rollout status for each deployment individually
        for dep in deployments:
            print(f"  -> Waiting for deployment/{dep}...")
            cmd = [
                "kubectl", "rollout", "status", f"deployment/{dep}",
                "-n", namespace, f"--timeout={timeout_seconds}s"
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            if process.stdout:
                for raw_line in iter(process.stdout.readline, ""):
                    # Clean up carriage returns and leading/trailing whitespace
                    clean_line = raw_line.replace("\r", "").strip()
                    if clean_line:
                        print(f"     {clean_line}")

            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)
        
        print(f"[✅] Namespace '{namespace}' is completely healthy.")
        
    except subprocess.CalledProcessError:
        print(f"\n[❌] FATAL: Timeout or failure waiting for deployments in {namespace} to become Ready.")
        print(f"--- Diagnosing {namespace} Pod States ---")
        subprocess.run(["kubectl", "get", "pods", "-n", namespace])
        
        print(f"\n--- Fetching Events for {namespace} ---")
        subprocess.run(["kubectl", "get", "events", "-n", namespace, "--sort-by=.metadata.creationTimestamp"])
        sys.exit(1)

def main():
    print("Initiating Global Infrastructure Validation...")
    
    # 1. Check AI Infrastructure Domain
    check_namespace_health("autoresolve-ai")
    
    # 2. Check Target Workload Domain
    check_namespace_health("boutique-demo")
    
    print("\n[🎉] GLOBAL VALIDATION COMPLETE: All systems GO! AutoResolve is fully operational.")

if __name__ == "__main__":
    main()