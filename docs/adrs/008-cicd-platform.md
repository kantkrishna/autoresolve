# ADR 008: CI/CD Platform Selection

## Context
AutoResolve is intended to be a GitHub portfolio-quality open-source project requiring automated testing, linting, and Docker builds on every PR.

## Alternatives Considered
1. **Azure DevOps:** Enterprise-grade pipeline system.
2. **GitHub Actions:** CI/CD tightly integrated into GitHub.

## Tradeoffs
- Azure DevOps is highly capable for closed-source enterprise teams but introduces friction for open-source contributors.
- GitHub Actions natively integrates with the repository and simplifies the authentication flow for our future GitHub MCP server (drafting PRs via GitHub Apps).

## Decision
We will use **GitHub Actions**.

## Consequences
- CI/CD workflows will be maintained within the .github/workflows/ directory.
