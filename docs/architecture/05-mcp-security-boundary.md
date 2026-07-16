```mermaid
graph LR
    subgraph AutoResolve Worker
        LLM[LiteLLM Router] <--> Agent[Investigation Node]
    end
    
    subgraph Security Airgap
        Agent <-->|JSON-RPC over Stdio| K8sServer[K8s MCP Server]
    end
    
    subgraph Target Environment
        K8sServer -.->|kubectl / REST| Cluster[Production Cluster]
    end