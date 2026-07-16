import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    FastAPI Dependency to validate the incoming API key against environment variables.
    """
    expected_api_key = os.getenv("AUTORESOLVE_API_KEY", "dev-secret-key")
    if not api_key or api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key
