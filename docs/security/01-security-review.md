# AutoResolve Enterprise Security Review

## Threat Model & Mitigations
1. **Prompt Injection:** Mitigated via `Pydantic` schema validation at the ingestion edge and strict adherence to structural JSON output configurations (`with_structured_output`) in LiteLLM.
2. **Secret Leakage:** Secrets are injected exclusively at runtime via environment variables (`.env` is git-ignored). The LLM reasoning loop never receives infrastructure credentials; MCP servers hold the credentials locally.
3. **Container Security:** `Dockerfile` enforces a non-root `autoresolve` user. We utilize distroless/slim base images to minimize the CVE attack surface.
4. **Supply Chain:** Dependencies are strictly pinned via `poetry.lock` to prevent dependency confusion attacks.

## Compliance (SOC2 / GDPR)
* **Data Minimization:** Logs fetched from Kubernetes are passed through `PIIScrubber` before reaching external LLMs.
* **Auditability:** All state mutations are captured via `log_audit_event` in an append-only JSON format, ready for ingestion by SIEMs (Datadog/Splunk).