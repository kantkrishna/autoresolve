# src/core/llm.py
from langchain_litellm import ChatLiteLLM

def get_agnostic_llm(temperature: float = 0.1) -> ChatLiteLLM:
    """
    Instantiates an LLM client agnostic to the backend provider.
    Includes built-in retry logic, timeouts, and automated model failovers.
    """
    return ChatLiteLLM(
        # FIX: Explicitly prefix with the provider name
        model="openai/gpt-4o-mini",
        temperature=temperature,  
        max_retries=3,  
        request_timeout=30.0,
        # FIX: Explicitly prefix the fallbacks as well
        fallbacks=["openai/gpt-5-nano", "openai/gpt-5.4-nano"],  
        model_kwargs={"top_p": 0.9},
    )