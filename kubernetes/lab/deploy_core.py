# kubernetes/lab/deploy_core.py

# Automates the deployment of the core AutoResolve application components into the
# k3d cluster. This includes the FastAPI gateway, the LangGraph worker, and automated
# CoreDNS public DNS forwarding configuration for seamless external API resolution.

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

# Enforce UTF-8 to prevent Windows terminal crashes
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def build_and_load_image(base_dir: Path):
    print("\n[📦] Building AutoResolve core Docker image (autoresolve:latest)...")
    try:
        # Assuming your Dockerfile is at the root or in a docker/ dir. Adjust path if necessary.
        subprocess.run(
            ["docker", "build", "-t", "autoresolve:latest", str(base_dir)], 
            check=True
        )
        
        print("\n[🚀] Importing image into k3d cluster 'autoresolve-lab'...")
        subprocess.run(
            ["k3d", "image", "import", "autoresolve:latest", "-c", "autoresolve-lab"], 
            check=True
        )
    except subprocess.CalledProcessError:
        print("[❌] Failed to build or load Docker image. Aborting deployment.")
        sys.exit(1)


def apply_configmap(env_path: Path):
    """Dynamically creates the configmap from the local .env file"""
    load_dotenv(dotenv_path=env_path)
    tz = os.getenv("CLUSTER_TIMEZONE", "Asia/Kolkata")
    print(f"\n[⚙️] Injecting CLUSTER_TIMEZONE ({tz}) into ConfigMap...")
    
    # Idempotent ConfigMap creation
    cmd = f"kubectl create configmap autoresolve-config --namespace autoresolve-ai --from-literal=CLUSTER_TIMEZONE={tz} --dry-run=client -o yaml | kubectl apply -f -"
    subprocess.run(cmd, shell=True, check=True)


def apply_secrets_idempotently(env_path: str):
    """
    Forces Kubernetes to drop stale secrets and ingest the current .env file.
    (Upgraded from 'create-if-missing' to 'force-sync' for soft rebuilds)
    """
    print("\n[🔒] [SECURITY] Syncing Kubernetes Secrets from local .env...")
    
    # 1. Gracefully delete the old secret (fails silently if it doesn't exist yet on a fresh install)
    subprocess.run(
        ["kubectl", "delete", "secret", "autoresolve-secrets", "-n", "autoresolve-ai", "--ignore-not-found"], 
        check=False
    )
    
    # 2. Recreate the secret freshly from the host .env file
    subprocess.run(
        ["kubectl", "create", "secret", "generic", "autoresolve-secrets", f"--from-env-file={env_path}", "-n", "autoresolve-ai"],
        check=True
    )


def patch_coredns_for_external_resolution():
    print("\n[🌐] Ensuring CoreDNS is configured for public internet DNS forwarding...")
    import yaml
    try:
        # Get current CoreDNS config
        result = subprocess.run(
            ["kubectl", "get", "configmap", "coredns", "-n", "kube-system", "-o", "yaml"],
            check=True, capture_output=True, text=True, encoding="utf-8"
        )
        
        doc = yaml.safe_load(result.stdout)
        corefile = doc["data"]["Corefile"]
        
        if "8.8.8.8" not in corefile:
            new_corefile = corefile.replace("forward . /etc/resolv.conf", "forward . 8.8.8.8 8.8.4.4")
            doc["data"]["Corefile"] = new_corefile
            
            # Apply updated config safely
            patch_process = subprocess.Popen(
                ["kubectl", "apply", "-f", "-"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                text=True, encoding="utf-8"
            )
            out, err = patch_process.communicate(input=yaml.dump(doc))
            
            if patch_process.returncode == 0:
                print("  [+] CoreDNS ConfigMap successfully patched.")
            else:
                print(f"  [!] Failed to apply CoreDNS patch: {err}")
        else:
            print("  [+] CoreDNS is already patched with public resolvers.")
            
    except Exception as e:
        print(f"  [!] Warning: Automated CoreDNS patching encountered an issue: {e}")


def run_command(command: list, description: str, ignore_error: bool = False):
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
        if not ignore_error:
            print(f"[ERROR] Command failed: {' '.join(command)}")
            print(e.stdout)
            sys.exit(1)
        return False


def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    
    core_file = base_dir / "kubernetes" / "lab" / "autoresolve-core.yaml"

    # --- BULLETPROOF .ENV LOADING ---
    env_path = base_dir / ".env"
    print(f"[DEBUG] Looking for .env file exactly at: {env_path}")
    
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True) 
        print("[DEBUG] Successfully loaded .env file.")
    else:
        print(f"[WARNING] No .env file found at {env_path}")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("[ERROR] OPENAI_API_KEY not found in .env file or system environment.")
        sys.exit(1)

    print("==========================================================")
    print("[🧠] AutoResolve - Core Application Deployment")
    print("==========================================================\n")

    # Step 1: Ensure the Timezone ConfigMap exists BEFORE pods are created
    apply_configmap(env_path)

    # Step 2: Manage Secure Secrets
    apply_secrets_idempotently(str(env_path))

    # Step 3: Build the Docker Image and Sideload into k3d
    build_and_load_image(base_dir)

    # Step 4: Automatically Patch CoreDNS for Public External API Resolution
    patch_coredns_for_external_resolution()

    # Step 5: Deploy the Application Manifests
    run_command(
        ["kubectl", "apply", "-f", str(core_file)],
        "Deploying API Gateway and LangGraph Worker to Kubernetes"
    )
    
    print("\n[🔄] Forcing rollout restart to apply new image...")
    subprocess.run(["kubectl", "rollout", "restart", "deployment/autoresolve-api-gateway", "-n", "autoresolve-ai"], check=True)
    subprocess.run(["kubectl", "rollout", "restart", "deployment/autoresolve-ai-worker", "-n", "autoresolve-ai"], check=True)

    print("\n==========================================================")
    print("[SUCCESS] Core Platform Deployed Successfully!")
    print("==========================================================")

if __name__ == "__main__":
    main()