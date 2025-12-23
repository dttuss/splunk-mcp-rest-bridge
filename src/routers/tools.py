"""FastAPI router for MCP tools endpoints."""

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.mcp_client import mcp_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["tools"])


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution."""

    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the tool",
    )


class ToolInfo(BaseModel):
    """Tool information model."""

    name: str
    description: str
    inputSchema: Dict[str, Any]


class ToolListResponse(BaseModel):
    """Response model for tool listing."""

    tools: List[ToolInfo]


class ToolExecutionResponse(BaseModel):
    """Response model for tool execution."""

    content: List[Dict[str, Any]]
    isError: bool = False


@router.get("", response_model=ToolListResponse)
async def list_tools() -> ToolListResponse:
    """
    List all available tools from the Splunk MCP Server.

    Returns:
        ToolListResponse: List of available tools with their schemas
    """
    try:
        tools = await mcp_client.list_tools()
        return ToolListResponse(tools=tools)
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to communicate with MCP server: {str(e)}",
        )


@router.post("/{tool_name}", response_model=ToolExecutionResponse)
async def execute_tool(
    tool_name: str,
    request: ToolExecutionRequest,
) -> ToolExecutionResponse:
    """
    Execute a specific tool on the Splunk MCP Server.

    Args:
        tool_name: Name of the tool to execute
        request: Tool execution request with arguments

    Returns:
        ToolExecutionResponse: Result of the tool execution
    """
    try:
        logger.info(f"Executing tool '{tool_name}' with arguments: {request.arguments}")
        result = await mcp_client.call_tool(tool_name, request.arguments)
        
        # Extract content and error status from MCP result
        content = result.get("content", [])
        is_error = result.get("isError", False)
        
        return ToolExecutionResponse(content=content, isError=is_error)
    except Exception as e:
        logger.error(f"Failed to execute tool '{tool_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to execute tool on MCP server: {str(e)}",
        )
