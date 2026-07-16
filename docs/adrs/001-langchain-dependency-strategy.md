# ADR 001: LangChain Dependency Strategy

## Context
During Phase 6, importing `ChatLiteLLM` from the monolithic `langchain_community` package resulted in deprecation warnings and missing module errors. The LangChain ecosystem is actively sunsetting the massive community package to reduce import times and memory bloat.

## Alternatives Considered
1. **Pin to an older LangChain version:** Keeps the code working as-is, but introduces technical debt and blocks future security patches.
2. **Modular Partner Packages:** Explicitly declare `langchain-core` and specific provider packages (e.g., `langchain-litellm`) in the `pyproject.toml`.

## Decision
We will utilize the **Modular Partner Packages** strategy. We explicitly bypass deprecated `__init__.py` files and install dedicated sub-packages.

## Tradeoffs & Justification
- **Tradeoff:** Requires slightly more verbose import statements and explicit dependency management in `pyproject.toml`.
- **Justification:** This drastically reduces the size of our deployment Docker images (the API Gateway won't install hundreds of unused community integrations). It also ensures deterministic builds and enterprise-grade stability.
"@ | Out-File -FilePath "docs/adrs/001-langchain-dependency-strategy.md" -Encoding utf8