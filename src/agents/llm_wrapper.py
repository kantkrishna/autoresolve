"""
src/agents/llm_wrapper.py
"""
from typing import Any

from langchain_litellm import ChatLiteLLM

from src.production.prod_resilience import CircuitBreaker, CircuitBreakerConfig

# Initialize a global circuit breaker for external LLM calls
llm_circuit_config = CircuitBreakerConfig(
    failure_threshold=3, 
    recovery_timeout=60, 
    expected_exceptions=(Exception,) 
)
llm_circuit_breaker = CircuitBreaker("LLM_API", llm_circuit_config)
llm = ChatLiteLLM(model="gpt-4o")

async def resilient_llm_invoke(messages: list) -> Any:
    """
    Safely executes LLM calls wrapped in a resilience circuit breaker.
    """
    try:
        response = await llm_circuit_breaker.call(llm.ainvoke, messages)
        return response
    except RuntimeError as e:
        # Circuit is OPEN - Fail Fast
        raise e