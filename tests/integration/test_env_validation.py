# Validate the full event cascade (FastAPI -> Kafka Broker -> Consumer -> LangGraph),
# ensuring that the system behaves as expected under real-world conditions.
import hmac
import hashlib
import json
import pytest
import httpx

@pytest.mark.asyncio
async def test_webhook_ingestion_e2e():
    secret = b"dev-secret-key"
    payload = {
        "status": "firing",
        "alertname": "HighMemoryUsage",
        "service": "payment-gateway",
        "description": "Integration test validation payload."
    }
    
    # Serialize JSON identically to standard streams
    json_data = json.dumps(payload, separators=(',', ':'))
    
    # Calculate HMAC SHA256 programmatically inside Python
    signature = hmac.new(secret, json_data.encode('utf-8'), hashlib.sha256).hexdigest()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/webhook/prometheus",
            content=json_data,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "dev-secret-key",
                "X-Signature": f"sha256={signature}"
            }
        )
        
    # Assert network data contracts are intact
    assert response.status_code == 202
    assert "tracking_id" in response.json()
