# AutoResolve: Autonomous Incident Response & Remediation Engine

![AutoResolve Architecture](docs/architecture/04-ai-swarm-state-machine.md)

AutoResolve is a production-grade, AI-augmented Site Reliability Engineering (SRE) platform. It autonomously intercepts production alerts, retrieves contextual logs/metrics via the Model Context Protocol (MCP), and utilizes a LangGraph multi-agent swarm to diagnose and propose remediations for infrastructure and code-level incidents.

## 🏗 Architecture
AutoResolve utilizes an event-driven, decoupled architecture:
1. **Ingestion Gateway:** FastAPI + Kafka buffer to handle alert storms.
2. **AI Orchestration:** LangGraph state machine with strict Pydantic typed memory.
3. **Knowledge Retrieval:** Hybrid RAG pipeline (Dense + BM25) powered by Qdrant.
4. **Action Execution:** Air-gapped MCP Stdio servers for secure Kubernetes/Prometheus interaction.

## ✨ Features
- **Zero-Hallucination Metrics:** Strict schema enforcement on Prometheus telemetry.
- **Local LLM Support:** Fully privacy-compliant execution via Ollama (e.g., qwen2.5-coder).
- **Human-in-the-Loop (HITL):** Drafts GitHub PRs and Terraform patches, waiting for explicit Slack approval.
- **Enterprise Security:** Subprocess isolation for API keys via MCP.

## 🚀 Installation & Local Development

### Prerequisites
- Python 3.12+
- Poetry
- Docker & Docker Compose
- Qdrant (Local Vector DB)

### Setup
1. Clone the repository:
   \\\ash
   git clone https://github.com/your-org/autoresolve.git
   cd autoresolve
   \\\
2. Install dependencies via Poetry:
   \\\ash
   poetry install
   \\\
3. Configure the environment:
   \\\ash
   cp .env.example .env
   # Update LLM_BACKEND to 'anthropic', 'openai', or 'local'
   \\\

## 🔌 Running MCP Servers
MCP Servers run as isolated subprocesses. AutoResolve handles their lifecycle dynamically during the investigation_node execution. See mcp-servers/ for individual tool definitions.

## 🧪 Testing
We enforce strict MyPy typing and 100% core test coverage.
\\\ash
poetry run pytest
poetry run mypy src/
poetry run ruff check .
\\\
