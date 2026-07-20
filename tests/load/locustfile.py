import hashlib
import hmac
import json
import time

from locust import HttpUser, between, task

SECRET_KEY = b"dev-secret-key"


class PrometheusAlertStorm(HttpUser):
    """Simulates a massive cascading failure emitting hundreds of alerts."""

    wait_time = between(0.01, 0.1)

    @task
    def trigger_alert(self):
        payload = {
            "status": "firing",
            "alertname": "HighMemoryUsage",
            "service": "payment-gateway",
            "description": "Load test generated alert",
            "tracking_id": f"LOCUST-{int(time.time() * 1000)}",
        }

        json_body = json.dumps(payload)
        signature = hmac.new(
            SECRET_KEY, json_body.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": "dev-secret-key",
            "X-Signature": f"sha256={signature}",
        }

        self.client.post("/webhook/prometheus", data=json_body, headers=headers)
