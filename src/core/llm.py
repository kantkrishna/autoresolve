# src/core/llm.py
from langchain_litellm import ChatLiteLLM
from src.core.config import settings

def get_agnostic_llm(temperature: float = 0.1) -> ChatLiteLLM:
    """
    Instantiates an LLM client agnostic to the backend provider.
    Dynamically routes between Cloud (OpenAI) and Local (Ollama).
    """
    if settings.LLM_BACKEND == "local":
        # Route to local Ollama instance
        return ChatLiteLLM(
            model=settings.LOCAL_MODEL_NAME,
            temperature=temperature,
            api_base="http://localhost:11434", # Default Ollama local port
            drop_params=True, # Drops cloud-specific params to prevent crashes
            model_kwargs={"top_p": 0.9},
        )
    else:
        # Route to Cloud Provider
        return ChatLiteLLM(
            model="openai/gpt-4o-mini", # Standard fallback
            temperature=temperature,  
            max_retries=3,  
            request_timeout=30.0,
            drop_params=True,
            # Explicitly prefix the fallbacks as well
            fallbacks=["openai/gpt-5-nano", "openai/gpt-5.4-nano"],  
            model_kwargs={"top_p": 0.9},
        )