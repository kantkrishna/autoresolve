"""
autoresolve/production/resilience.py

Implements enterprise-grade resilience patterns including Circuit Breakers
and Health Readiness checks for LangGraph and MCP integrations.
"""

import logging
import time
from enum import Enum
from typing import Any, Callable, Dict

from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class CircuitState(Enum):
    CLOSED = "CLOSED"     # Normal operation
    OPEN = "OPEN"         # Failing, rejecting requests
    HALF_OPEN = "HALF_OPEN" # Testing if recovered

class CircuitBreakerConfig(BaseModel):
    """Configuration for the Circuit Breaker."""
    failure_threshold: int = Field(default=3, description="Number of failures before opening.")
    recovery_timeout: int = Field(default=30, description="Seconds to wait before trying HALF_OPEN.")
    expected_exceptions: tuple = Field(default=(Exception,), description="Exceptions that count as failures.")

class CircuitBreaker:
    """
    Prevents cascading failures when LLMs or MCP servers go down.
    Ensures AutoResolve degrades gracefully rather than hanging.
    """
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    async def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Executes the function depending on the circuit state."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.config.recovery_timeout:
                logger.info(f"Circuit {self.name} transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
            else:
                logger.warning(f"Circuit {self.name} is OPEN. Rejecting request.")
                raise RuntimeError(f"CircuitBreaker {self.name} is OPEN")

        try:
            result = await func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit {self.name} recovered. Transitioning to CLOSED")
                self._reset()
            return result
        except self.config.expected_exceptions as e:
            self._record_failure()
            raise e

    def _record_failure(self):
        """Records a failure and transitions state if threshold is met."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.error(f"Circuit {self.name} failure {self.failure_count}/{self.config.failure_threshold}")
        
        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.config.failure_threshold:
            logger.critical(f"Circuit {self.name} transitioning to OPEN")
            self.state = CircuitState.OPEN

    def _reset(self):
        """Resets the circuit breaker to a healthy state."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

class SystemHealthManager:
    """
    Evaluates system readiness for Kubernetes deployment.
    """
    def __init__(self):
        self.dependencies: Dict[str, Callable] = {}

    def register_dependency(self, name: str, check_func: Callable):
        """Registers an MCP server or Database for health checks."""
        self.dependencies[name] = check_func

    async def check_readiness(self) -> Dict[str, Any]:
        """Runs all checks to ensure the system is ready to process alerts."""
        health_status = {"status": "ok", "components": {}}
        for name, check in self.dependencies.items():
            try:
                is_healthy = await check()
                health_status["components"][name] = "healthy" if is_healthy else "unhealthy"
                if not is_healthy:
                    health_status["status"] = "degraded"
            except Exception as e:
                health_status["components"][name] = f"error: {str(e)}"
                health_status["status"] = "degraded"
        
        return health_status