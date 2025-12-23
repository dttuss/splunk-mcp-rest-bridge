"""MCP Client for connecting to Splunk MCP Server."""

import json
import logging
from typing import Any, Dict, List, Optional
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.config import settings

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with Splunk MCP Server via HTTP."""

    def __init__(self):
        """Initialize MCP client."""
        self.server_url = settings.splunk_mcp_server_url
        self.auth_token = settings.splunk_mcp_auth_token
        self.timeout = settings.splunk_mcp_server_timeout
        self.session: Optional[ClientSession] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> None:
        """Establish connection to MCP server."""
        try:
            logger.info(f"Connecting to Splunk MCP Server at {self.server_url}")
            
            headers = {}
            if self.auth_token:
                logger.info("Using Bearer token authentication")
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            # Create HTTP client for MCP communication
            verify_ssl = settings.splunk_mcp_server_verify_ssl
            
            self._http_client = httpx.AsyncClient(
                base_url=self.server_url,
                timeout=self.timeout,
                headers=headers,
                verify=verify_ssl,
            )
            
            # Initialize MCP session
            # Note: For HTTP-based MCP, we'll use direct HTTP calls
            # The MCP SDK primarily supports stdio, so we'll implement HTTP manually
            
            logger.info("Successfully connected to Splunk MCP Server")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        logger.info("Disconnected from Splunk MCP Server")

    async def _send_request(self, method: str, params: Dict[str, Any], request_id: int) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server with auditing."""
        if not self._http_client:
            await self.connect()

        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        if settings.bridge_log_payloads:
            logger.info(
                f"[AUDIT] Calling Splunk MCP: {method}\n"
                f"URL: {self.server_url}\n"
                f"Payload: {json.dumps(payload, indent=2)}"
            )

        response = await self._http_client.post("/", json=payload)
        
        if settings.bridge_log_payloads:
            try:
                result = response.json()
                resp_log = json.dumps(result, indent=2)
            except Exception:
                result = {"error": "Non-JSON response from Splunk", "raw": response.text}
                resp_log = response.text
                
            logger.info(
                f"[AUDIT] Splunk MCP Response: {method} - Status: {response.status_code}\n"
                f"Response: {resp_log}"
            )
        else:
            result = response.json()

        response.raise_for_status()

        if "error" in result:
            raise Exception(f"MCP error: {result['error']}")
        
        return result.get("result", {})

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server."""
        try:
            result = await self._send_request("tools/list", {}, 1)
            tools = result.get("tools", [])
            logger.info(f"Retrieved {len(tools)} tools from MCP server")
            return tools
        except Exception as e:
            logger.error(f"Failed to list tools from {self.server_url}: {str(e)}", exc_info=True)
            raise

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on the MCP server."""
        try:
            logger.info(f"Calling tool '{tool_name}' with arguments: {arguments}")
            return await self._send_request(
                "tools/call",
                {"name": tool_name, "arguments": arguments},
                2
            )
        except Exception as e:
            logger.error(f"Failed to call tool '{tool_name}': {e}")
            raise

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from MCP server."""
        try:
            result = await self._send_request("resources/list", {}, 3)
            resources = result.get("resources", [])
            logger.info(f"Retrieved {len(resources)} resources from MCP server")
            return resources
        except Exception as e:
            logger.error(f"Failed to list resources: {e}")
            raise

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource from MCP server."""
        try:
            logger.info(f"Reading resource: {uri}")
            return await self._send_request("resources/read", {"uri": uri}, 4)
        except Exception as e:
            logger.error(f"Failed to read resource '{uri}': {e}")
            raise


# Global MCP client instance
mcp_client = MCPClient()
