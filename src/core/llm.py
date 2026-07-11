# src/core/llm.py
from langchain_community.chat_models import ChatLiteLLM
from pydantic import SecretStr

def get_agnostic_llm(temperature: float = 0.1) -> ChatLiteLLM:
    """
    Instantiates an LLM client agnostic to the backend provider.
    Includes built-in retry logic, timeouts, and automated model failovers.
    """
    return ChatLiteLLM(
        model="claude-3-5-sonnet-20240620",
        temperature=temperature,          # Low temp for deterministic SRE logic
        max_retries=3,                    # Retry logic for network blips
        request_timeout=30.0,
        fallbacks=["gpt-4o", "gemini-1.5-pro"], # Automated failover
        model_kwargs={"top_p": 0.9}
    )