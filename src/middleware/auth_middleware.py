"""Authentication middleware for validation API keys."""

from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from src.config import settings

# Define API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)) -> Optional[str]:
    """
    Validate the X-API-Key header against the configured secret.
    
    If BRIDGE_API_KEY is not set in config, authentication is disabled (always valid).
    """
    configured_key = settings.bridge_api_key
    
    # If no key is configured, allow all requests (Dev mode)
    if not configured_key:
        return api_key_header

    # If key is required but missing or invalid
    if api_key_header == configured_key:
        return api_key_header
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )
