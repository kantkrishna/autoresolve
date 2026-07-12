# src/core/llm.py
from langchain_litellm import ChatLiteLLM


def get_agnostic_llm(temperature: float = 0.1) -> ChatLiteLLM:
    """
    Instantiates an LLM client agnostic to the backend provider.
    Includes built-in retry logic, timeouts, and automated model failovers.
    """
    return ChatLiteLLM(
        model="claude-3-5-sonnet-20240620",
        temperature=temperature,
        max_retries=3,
        request_timeout=30.0,
        fallbacks=["gpt-4o", "gemini-1.5-pro"],
        model_kwargs={"top_p": 0.9},
    )
