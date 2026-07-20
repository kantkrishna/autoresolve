from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


@pytest.mark.security
def test_gateway_survives_kafka_outage(monkeypatch):
    """
    Chaos Test: If Kafka dies during an alert storm, the API must not crash.
    It must catch the timeout and return a 503 to force Prometheus to alert a human.
    """
    monkeypatch.setenv("AUTORESOLVE_API_KEY", "test-secret")

    # Inject a critical failure into the publisher
    with patch(
        "src.api.main.publisher.publish_alert", new_callable=AsyncMock
    ) as mock_pub:
        mock_pub.side_effect = Exception("Kafka Broker Connection Refused")

        payload = {
            "status": "firing",
            "alertname": "ChaosTest",
            "service": "payment-gateway",
            "description": "Testing Kafka outage",
        }

        response = client.post(
            "/webhook/prometheus", json=payload, headers={"X-API-Key": "test-secret"}
        )

        # System MUST degrade gracefully and signal failure to upstream
        assert response.status_code == 503
        assert "Event broker unavailable" in response.json()["detail"]
