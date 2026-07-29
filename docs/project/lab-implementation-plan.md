# Implementation Plan: Decoupled Production Engineering Lab

## Overview
This document outlines the phase-wise user stories, acceptance criteria, and dependency mapping required to transition AutoResolve from a static mock setup to a fully decoupled, cloud-native Production Engineering Lab using Google Online Boutique as the target workload.

---

## Phase-wise User Stories & Acceptance Criteria

### Phase 1: Lightweight Local Cluster Provisioning
**User Story 1.1: Local Cluster & Namespace Isolation**
As a Platform Engineer, I want a lightweight local Kubernetes cluster provisioned via k3d with dedicated, isolated namespaces, so that the AI platform and the target workload operate securely without cross-contamination.

**Acceptance Criteria:**
- A local Kubernetes cluster is successfully provisioned using k3d with optimized limits suitable for a developer laptop.
- Two distinct namespaces are created: `boutique-demo` (for the target workload) and `autoresolve-ai` (for the AutoResolve platform).
- Kubernetes NetworkPolicies are applied to strictly govern traffic flow and permit strictly unidirectional communication from the `boutique-demo` namespace to the AutoResolve ingress gateway.

### Phase 2: Google Online Boutique & Observability Stack Deployment
**User Story 2.1: Workload and Telemetry Deployment**
As a Site Reliability Engineer, I want to deploy the Google Online Boutique alongside an observability stack (Prometheus, Loki, Tempo), so that realistic microservice telemetry is centrally collected without modifying AutoResolve's core logic.

**Acceptance Criteria:**
- Google Online Boutique is deployed into the `boutique-demo` namespace, functioning entirely as an external cloud-native application.
- The deployment configuration explicitly avoids heavy background databases to keep the overall RAM footprint under acceptable limits for local environments.
- The observability stack is configured to actively scrape metrics and collect container logs from the microservices.

### Phase 3: Alertmanager Webhook Routing
**User Story 3.1: Dynamic Webhook Injection**
As a Site Reliability Engineer, I need Prometheus to evaluate metrics and Alertmanager to route critical events to AutoResolve, so that incidents automatically trigger the AI triage workflow.

**Acceptance Criteria:**
- The Prometheus Alertmanager component is explicitly enabled and running in the cluster.
- A PromQL alerting rule is defined to evaluate resource constraints (e.g., `container_memory_working_set_bytes`) across the `boutique-demo` namespace.
- The Alertmanager route is configured with a webhook receiver pointing to the AutoResolve FastAPI endpoint, injecting required authentication tokens.

### Phase 4: MCP Server Refactoring (Live Data Integration)
**User Story 4.1: Cluster-Aware Tool Execution**
As an AI Engineer, I want the Model Context Protocol (MCP) servers to interface with live Kubernetes and Prometheus APIs, so that the investigation agents query real-time infrastructure state instead of static mock data.

**Acceptance Criteria:**
- Hardcoded strings and static mock JSON payloads are completely purged from the Kubernetes MCP server implementation.
- The Kubernetes MCP server utilizes the official Python Kubernetes client to retrieve live pod logs dynamically.
- Log retrieval functions implement truncation rules (`tail_lines`) to protect the language model's context window from overflow.
- The Prometheus MCP server utilizes an asynchronous HTTP client to execute dynamic PromQL queries against the live time-series database.

### Phase 5: AutoResolve Core Deployment & RBAC Configuration
**User Story 5.1: Zero-Trust AI Swarm Deployment**
As a Security Engineer, I want AutoResolve deployed with strict least-privilege access controls, so that the AI platform can securely observe and query the target workload without risking unauthorized cluster modifications.

**Acceptance Criteria:**
- AutoResolve core components (FastAPI engine, Kafka broker, Postgres, and LangGraph workers) are deployed exclusively into the `autoresolve-ai` namespace.
- A dedicated Kubernetes ServiceAccount is created and securely mounted to the AI worker pods.
- Role-Based Access Control (RBAC) rules bind the ServiceAccount to a tightly scoped, read-only role, restricting permissions strictly to listing pods and reading logs within designated target namespaces.

### Phase 6: End-to-End Validation & Fault Injection
**User Story 6.1: Autonomous Incident Response Validation**

**Acceptance Criteria:**
- A synthetic failure or load generator is triggered to simulate a live issue (e.g., a memory leak or CPU spike) in the Google Online Boutique environment.
- Prometheus detects the metric anomaly and Alertmanager successfully fires the webhook payload to AutoResolve.
- The investigation agent queries live metrics and container crash logs using the newly refactored, application-agnostic MCP servers.
- The platform successfully drafts an accurate root cause analysis and a valid remediation Pull Request based on the findings.
---

## Implementation Artifacts & Dependency Mapping

| Phase | Artefact | Parent (Prerequisites) | Dependants | Phase Execution Instructions |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | `kubernetes/cluster/k3d/k3d-config.yaml` | None | `kubernetes/cluster/k3d/setup_k3d.py` | `k3d cluster delete autoresolve-lab` <br> `poetry run python kubernetes/cluster/k3d/setup_k3d.py` |
| **Phase 1** | `kubernetes/lab/namespaces.yaml` | None | `network-policy.yaml`, `setup_k3d.py`, `deploy_workload.py`, `autoresolve-infra.yaml` | Enforces namespace domain isolation. Applied via `setup_k3d.py`. |
| **Phase 1** | `kubernetes/lab/network-policy.yaml` | `namespaces.yaml` | `setup_k3d.py`, `alert_routing.py` | Establishes zero-trust egress boundary. |
| **Phase 1** | `kubernetes/cluster/k3d/setup_k3d.py` | `k3d-config.yaml`, `namespaces.yaml`, `network-policy.yaml` | `deploy_workload.py`, `destroy_k3d.py` | Provisions the foundational cluster architecture. |
| **Phase 1** | `kubernetes/cluster/k3d/destroy_k3d.py` | `setup_k3d.py` | None | Destroys the cluster. |
| **Phase 2** | `kubernetes/lab/prometheus-lite-values.yaml`| None | `deploy_workload.py`, `alert_routing.py` | Helm values for resource-constrained monitoring. |
| **Phase 2** | `kubernetes/lab/deploy_workload.py` | `setup_k3d.py`, `prometheus-lite-values.yaml`| `alert_routing.py`, `k8s_server.py` | `poetry run python kubernetes/lab/deploy_workload.py` <br> `kubectl get pods -n boutique-demo -w` |
| **Phase 3/4** | `kubernetes/lab/alert_routing.py` | `deploy_workload.py`, `network-policy.yaml`, `prometheus-lite-values.yaml` | `scripts/incident_workflow.py` | `poetry run python kubernetes/lab/alert_routing.py` |
| **Phase 3/4** | `mcp-servers/kubernetes-mcp/k8s_server.py` | `deploy_workload.py` | `scripts/test_live_mcp.py`, `rbac.yaml` | Refactored for live log queries. |
| **Phase 3/4** | `mcp-servers/prometheus-mcp/prom_server.py` | `deploy_workload.py` | `scripts/test_live_mcp.py` | Refactored for live PromQL execution. |
| **Phase 3/4** | `scripts/test_live_mcp.py` | MCP Servers (`k8s_server.py`, `prom_server.py`) | None | `poetry run python scripts/test_live_mcp.py` |
| **Phase 5** | `kubernetes/lab/rbac.yaml` | `namespaces.yaml` | `autoresolve-core.yaml`, `k8s_server.py` | `poetry run python scripts/apply_rbac.py` |
| **Phase 5** | `kubernetes/lab/autoresolve-infra.yaml` | `namespaces.yaml` | `deploy_infra.py`, `autoresolve-core.yaml` | Stateful infra definition (Kafka, Postgres). |
| **Phase 5** | `scripts/deploy_infra.py` | `autoresolve-infra.yaml`, `setup_k3d.py` | `scripts/deploy_core.py` | `poetry run python scripts/deploy_infra.py` |
| **Phase 5** | `kubernetes/lab/autoresolve-core.yaml` | `autoresolve-infra.yaml`, `rbac.yaml`, `k8s_server.py` | `scripts/deploy_core.py` | Core gateway and AI worker manifests. |
| **Phase 5** | `scripts/deploy_core.py` | `autoresolve-core.yaml`, `deploy_infra.py`, `rbac.yaml` | `scripts/incident_workflow.py` | `poetry run python scripts/deploy_core.py` |
| **Phase 5** | `scripts/incident_workflow.py` | `deploy_core.py`, `alert_routing.py` | Phase 6 (Validation) | `poetry run python scripts/incident_workflow.py` |
