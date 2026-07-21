"""
tests/production/test_prod_resilience.py

Unit tests for enterprise resilience patterns.
"""

import asyncio

import pytest

from src.production.prod_resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)


@pytest.fixture
def circuit_breaker():
    config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
    return CircuitBreaker("LLM_API", config)

@pytest.mark.asyncio
async def test_circuit_breaker_success(circuit_breaker):
    """Test that a successful call does not trip the breaker."""
    async def mock_call():
        return "success"
    
    result = await circuit_breaker.call(mock_call)
    assert result == "success"
    assert circuit_breaker.state == CircuitState.CLOSED

@pytest.mark.asyncio
async def test_circuit_breaker_trips_open(circuit_breaker):
    """Test that the breaker opens after threshold failures."""
    async def mock_fail():
        raise ValueError("API Timeout")

    with pytest.raises(ValueError):
        await circuit_breaker.call(mock_fail)
    
    assert circuit_breaker.state == CircuitState.CLOSED # 1 failure
    
    with pytest.raises(ValueError):
        await circuit_breaker.call(mock_fail)
        
    assert circuit_breaker.state == CircuitState.OPEN # 2 failures triggers OPEN

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_recovery(circuit_breaker):
    """Test the recovery timeout logic."""
    async def mock_fail():
        raise ValueError("API Timeout")
    
    async def mock_success():
        return "recovered"

    # Trip the breaker
    for _ in range(2):
        with pytest.raises(ValueError):
            await circuit_breaker.call(mock_fail)
            
    assert circuit_breaker.state == CircuitState.OPEN

    # Wait for recovery timeout
    await asyncio.sleep(1.1)

    # Breaker should now allow a test request (HALF_OPEN) and recover (CLOSED)
    result = await circuit_breaker.call(mock_success)
    assert result == "recovered"
    assert circuit_breaker.state == CircuitState.CLOSED