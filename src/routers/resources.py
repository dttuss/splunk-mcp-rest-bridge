"""FastAPI router for MCP resources endpoints."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.mcp_client import mcp_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resources", tags=["resources"])


class ResourceInfo(BaseModel):
    """Resource information model."""

    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None


class ResourceListResponse(BaseModel):
    """Response model for resource listing."""

    resources: List[ResourceInfo]


class ResourceContent(BaseModel):
    """Resource content model."""

    uri: str
    mimeType: Optional[str] = None
    text: Optional[str] = None
    blob: Optional[str] = None


class ResourceReadResponse(BaseModel):
    """Response model for resource reading."""

    contents: List[ResourceContent]


@router.get("", response_model=ResourceListResponse)
async def list_resources() -> ResourceListResponse:
    """
    List all available resources from the Splunk MCP Server.

    Returns:
        ResourceListResponse: List of available resources
    """
    try:
        resources = await mcp_client.list_resources()
        return ResourceListResponse(resources=resources)
    except Exception as e:
        logger.error(f"Failed to list resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to communicate with MCP server: {str(e)}",
        )


@router.get("/{uri:path}", response_model=ResourceReadResponse)
async def read_resource(uri: str) -> ResourceReadResponse:
    """
    Read a specific resource from the Splunk MCP Server.

    Args:
        uri: URI of the resource to read

    Returns:
        ResourceReadResponse: Content of the resource
    """
    try:
        logger.info(f"Reading resource: {uri}")
        result = await mcp_client.read_resource(uri)
        
        # Extract contents from MCP result
        contents = result.get("contents", [])
        
        return ResourceReadResponse(contents=contents)
    except Exception as e:
        logger.error(f"Failed to read resource '{uri}': {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to read resource from MCP server: {str(e)}",
        )
