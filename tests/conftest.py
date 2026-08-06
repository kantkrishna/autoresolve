"""
tests/conftest.py

Global pytest configuration and early-execution hooks.
"""
import warnings

# 1. Silence the LangChain Community sunset warning
warnings.filterwarnings("ignore", message=".*langchain-community.*")

# 2. Silence the Starlette/FastAPI httpx deprecation warning
warnings.filterwarnings("ignore", message=".*starlette.testclient.*")
warnings.filterwarnings("ignore", module="fastapi.*")

# 3. Blanket catch for all lingering ecosystem deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)