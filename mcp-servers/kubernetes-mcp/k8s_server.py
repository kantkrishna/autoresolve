# mcp-servers/kubernetes-mcp/server.py
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP - this automatically handles JSON-RPC over stdio
mcp = FastMCP("Kubernetes_SRE_Tools")


@mcp.tool()
def get_pod_logs(namespace: str, pod_name: str) -> str:
    """
    Fetch the last 100 lines of logs from a Kubernetes pod.
    (Currently returning mock data for the Astronomy Shop demo)
    """
    # In production, this uses the kubernetes.client package
    # config.load_kube_config()

    if "payment" in pod_name.lower():
        return (
            f"[INFO] {pod_name} booting up...\n"
            f"[WARN] Memory limit approaching 95%\n"
            f"[FATAL] OOMKilled Exception in {namespace}/{pod_name}"
        )
    return f"[INFO] {pod_name} running normally."


if __name__ == "__main__":
    mcp.run()
