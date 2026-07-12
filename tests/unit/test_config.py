# tests/unit/test_config.py

import pytest
from pydantic import ValidationError

from src.core.config import AutoResolveConfig


def test_missing_kafka_fails_validation(monkeypatch):
    """Ensure the system refuses to start without the Kafka broker configured."""
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-mock-key")

    # Explicitly remove the mock environment variable set by conftest.py
    monkeypatch.delenv("KAFKA_BOOTSTRAP_SERVERS", raising=False)

    # Missing KAFKA_BOOTSTRAP_SERVERS
    with pytest.raises(ValidationError) as exc_info:
        AutoResolveConfig()

    assert "KAFKA_BOOTSTRAP_SERVERS" in str(exc_info.value)


def test_valid_configuration_loads(monkeypatch):
    """Ensure valid tech stack configuration initializes properly."""
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-mock-key")

    config = AutoResolveConfig()
    assert config.KAFKA_BOOTSTRAP_SERVERS == "kafka:9092"
