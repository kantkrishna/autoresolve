# Contributing to AutoResolve

Thank you for helping us build the future of autonomous SRE! 

## Development Setup
We enforce a strict "Zero-Friction" setup using Make:
1. Clone the repo: `git clone https://github.com/your-org/autoresolve.git`
2. Run `make install` to set up Poetry environments.
3. Run `make test` to execute the test suite.

## Commit Standards
We strictly enforce [Conventional Commits](https://www.conventionalcommits.org/).
- `feat(agents): add resolution agent loop`
- `fix(mcp): resolve kubernetes log parsing error`
- `docs(adr): add ADR for LangGraph selection`