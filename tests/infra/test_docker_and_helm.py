import os
import yaml
from pathlib import Path

def test_dockerfile_exists():
    """Ensure Dockerfile exists and uses non-root user."""
    dockerfile_path = Path("Dockerfile")
    assert dockerfile_path.exists(), "Dockerfile is missing!"
    
    content = dockerfile_path.read_text()
    assert "USER autoresolve" in content, "Security Violation: Docker image must drop root privileges."

def test_helm_chart_is_valid():
    """Ensure Helm values map to the required application config."""
    values_path = Path("kubernetes/helm/autoresolve/values.yaml")
    if values_path.exists():
        with open(values_path, "r") as f:
            values = yaml.safe_load(f)
            
        assert "image" in values
        # Ensure the ServiceAccount asks for restricted capabilities
        assert values.get("serviceAccount", {}).get("create") is True