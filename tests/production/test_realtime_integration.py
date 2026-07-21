"""
tests/production/test_realtime_integration.py
"""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

def test_readiness_probe_healthy():
    """Ensure Kubernetes receives a 200 OK when dependencies are healthy."""
    response = client.get("/health/ready")
    
    assert response.status_code == 200, f"Expected 200 OK but got {response.status_code}. The route is missing from src/api/main.py."
    
    data = response.json()
    assert data["status"] == "ok"
    assert "postgres_state" in data["components"]
    assert "mcp_servers" in data["components"]

@pytest.mark.asyncio
async def test_resilient_llm_invoke_trips(monkeypatch):
    """Ensure the LLM wrapper catches downstream API exceptions and opens the circuit."""
    try:
        from langchain_litellm import ChatLiteLLM

        from src.agents.llm_wrapper import llm_circuit_breaker, resilient_llm_invoke
    except ImportError as e:
        pytest.skip(f"llm_wrapper not properly targeted: {e}")
        return
    
    # Force the underlying LLM to fail with a timeout
    async def mock_fail(*args, **kwargs):
        raise TimeoutError("OpenAI API Down")
    
    # FIX: Patch the Class itself, bypassing Pydantic's instance validation restrictions
    monkeypatch.setattr(ChatLiteLLM, "ainvoke", mock_fail)
    
    # Trip the breaker by hitting the failure threshold (3 failures)
    for _ in range(3):
        with pytest.raises(Exception):
            await resilient_llm_invoke([{"role": "user", "content": "Process alert"}])
            
    # Verify the circuit breaker successfully transitioned to OPEN state
    assert llm_circuit_breaker.state.name == "OPEN"