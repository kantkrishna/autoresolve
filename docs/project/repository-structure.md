# Enterprise Monorepo Structure

AutoResolve follows an **Enterprise Monorepo** pattern, structured using Domain-Driven Design (DDD) principles. This ensures strict isolation between the API ingestion gateway, the AI reasoning engine, and the external Model Context Protocol (MCP) tool servers.

## Directory Tree

\`\`\`text
autoresolve/
├── .github/                  # CI/CD pipelines, PR/Issue templates
├── docs/                     # Architecture, ADRs, PRDs (Docs-as-Code)
├── kubernetes/               # 
│   └── base/
│       └── kustomization.yaml
├── mcp-servers/              # Isolated JSON-RPC tool servers (Air-gapped from AI)
│   ├── kubernetes-mcp/       # K8s API integration
│   └── prometheus-mcp/       # Metrics querying
├── scripts/                  # 
│   └── bootstrap.sh
├── src/                      # Core Application Logic
│   ├── api/                  # FastAPI webhook receivers & Kafka producers
│   ├── agents/               # LangGraph cyclical state machines (The Brain)
│   ├── core/                 # Shared configurations, LLM routers, guardrails
│   └── rag/                  # Vector database and FastEmbed hybrid search
├── terraform/                # 
│   └── environments/dev/
│       └── main.tf
├── tests/                    # Unit and integration tests
├── .env                      # Local secrets (Not checked into source control)
└── pyproject.toml            # Global dependency and MyPy/Ruff governance
└── README.md                 # 
\`\`\`

## Design Philosophy
* **Atomic Deployability:** Prompts, agent logic, and tool schemas are versioned together. If an MCP server's required schema changes, the LangGraph prompt is updated in the exact same commit.
* **Modular Dependencies:** The root `pyproject.toml` handles global governance (linting/formatting), while directories like `/mcp-servers` manage their own isolated dependencies to prevent Docker image bloat.
