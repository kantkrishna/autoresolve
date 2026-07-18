# Stage 1: Builder
FROM python:3.12-slim AS builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# FIX: Install Poetry 2.0+ to support modern PEP-621 [project] syntax
RUN pip install "poetry>=2.4.1"

# Cache dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# Stage 2: Production Runtime
FROM python:3.12-slim AS runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-root user for security
RUN groupadd -r autoresolve && useradd -r -m -g autoresolve autoresolve

# Copy virtual environment from builder
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy application code
COPY src/ ./src/
COPY mcp-servers/ ./mcp-servers/

RUN chown -R autoresolve:autoresolve /app
USER autoresolve

# Default to API Gateway (can be overridden in compose/k8s)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]