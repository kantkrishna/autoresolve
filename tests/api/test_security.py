from typing import Any

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.api.auth import verify_api_key
from src.api.rate_limit import RateLimiter
from src.core.security.authorization import RBACProvider, Role

app = FastAPI()
rate_limiter = RateLimiter(requests_per_minute=2)


@app.get(
    "/secure-endpoint", dependencies=[Depends(verify_api_key), Depends(rate_limiter)]
)
async def secure_route() -> dict[str, str]:
    return {"status": "success"}


client = TestClient(app)


def test_api_key_authentication_failure() -> None:
    response = client.get("/secure-endpoint", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401


def test_api_key_authentication_success(monkeypatch: Any) -> None:
    monkeypatch.setenv("AUTORESOLVE_API_KEY", "test-secret")
    response = client.get("/secure-endpoint", headers={"X-API-Key": "test-secret"})
    assert response.status_code == 200


def test_rate_limiting(monkeypatch: Any) -> None:
    monkeypatch.setenv("AUTORESOLVE_API_KEY", "test-secret")
    headers = {"X-API-Key": "test-secret"}

    # Reset global state to ensure test isolation
    rate_limiter.clients.clear()

    assert client.get("/secure-endpoint", headers=headers).status_code == 200
    assert client.get("/secure-endpoint", headers=headers).status_code == 200
    response = client.get("/secure-endpoint", headers=headers)
    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_rbac_authorization() -> None:
    rbac = RBACProvider()
    assert rbac.evaluate_permission(Role.ADMIN, "terraform", "write") is True
    assert rbac.evaluate_permission(Role.AGENT, "kubernetes_mcp", "execute") is True
    assert rbac.evaluate_permission(Role.AGENT, "user_db", "drop") is False
