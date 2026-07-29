# scripts/validate_health.py

# This script validates the health of the AutoResolve lab environment by checking the
# readiness of all pods in the critical namespaces.

# Usage: poetry run python scripts/validate_health.py

import subprocess
import sys


def check_namespace_health(namespace: str, timeout_seconds: int = 300):
    print(f"\n[⏳] Validating health of namespace: {namespace}...")

    cmd = [
        "kubectl", "wait", "--for=condition=Ready", "pod",
        "--all", "-n", namespace, f"--timeout={timeout_seconds}s"
    ]

    try:
        # Stream and capture output line by line
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
                    print(clean_line)

        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
        
        print(f"[✅] Namespace '{namespace}' is completely healthy.")
    except subprocess.CalledProcessError:
        print(f"\n[❌] FATAL: Timeout waiting for pods in {namespace} to become Ready.")
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