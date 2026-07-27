# scripts/deploy_core.py

# Automates the deployment of the core AutoResolve application components into the
# k3d cluster. This includes the FastAPI gateway and the LangGraph worker, which
# are responsible for handling incoming requests and orchestrating the AI workflows.

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Enforce UTF-8 to prevent Windows terminal crashes
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

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
    base_dir = Path(__file__).resolve().parent.parent
    core_file = base_dir / "kubernetes" / "lab" / "autoresolve-core.yaml"

    # --- BULLETPROOF .ENV LOADING ---
    env_path = base_dir / ".env"
    print(f"[DEBUG] Looking for .env file exactly at: {env_path}")
    
    if env_path.exists():
        # override=True forces Python to use the file even if a blank env var exists
        load_dotenv(dotenv_path=env_path, override=True) 
        print("[DEBUG] Successfully loaded .env file.")
    else:
        print(f"[WARNING] No .env file found at {env_path}")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("[ERROR] OPENAI_API_KEY not found in .env file or system environment.")
        sys.exit(1)

    print("==========================================================")
    print("🧠 AutoResolve - Core Application Deployment")
    print("==========================================================\n")

    # Step 1: Manage Secure Secrets
    run_command(["kubectl", "delete", "secret", "autoresolve-secrets", "-n", "autoresolve-ai"], "Cleaning up old secrets", ignore_error=True)
    run_command(
        ["kubectl", "create", "secret", "generic", "autoresolve-secrets", f"--from-literal=OPENAI_API_KEY={openai_key}", "-n", "autoresolve-ai"],
        "Injecting OPENAI_API_KEY as an encrypted Kubernetes Secret"
    )

    # Step 2: Build the Docker Image
    run_command(
        ["docker", "build", "-t", "autoresolve:latest", "."],
        "Building AutoResolve Docker Image from source"
    )

    # Step 3: Sideload Image into k3d
    run_command(
        ["k3d", "image", "import", "autoresolve:latest", "-c", "autoresolve-lab"],
        "Sideloading image into the k3d isolated registry"
    )

    # Step 4: Deploy the Application
    run_command(
        ["kubectl", "apply", "-f", str(core_file)],
        "Deploying API Gateway and LangGraph Worker to Kubernetes"
    )

    print("\n==========================================================")
    print("[SUCCESS] Core Platform Deployed Successfully!")
    print("==========================================================")

if __name__ == "__main__":
    main()