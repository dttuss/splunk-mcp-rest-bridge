# Splunk MCP REST Bridge

**Splunk MCP REST Bridge** is a lightweight middleware that exposes the **Splunk Model Context Protocol (MCP)** server as a standard **REST API**.

It enables **Power Automate Desktop (PAD)** and other HTTP clients to execute Splunk searches and manage resources without needing native MCP support.

**Key Capabilities:**
*   **Protocol Translation**: Converts simple HTTP POST/GET requests into complex JSON-RPC over stdio/SSE.
*   **Universal Compatibility**: Designed for PAD, but works with *any* REST client.
*   **Splunk Execution**: Run searches (`run_splunk_query`) and manage knowledge objects via API.
*   **Enterprise Features**: Includes built-in request auditing, API Key authentication, and health monitoring.

> **Use Case**: This project was originally built to enable **Power Automate Desktop** flows to query Splunk, but it serves as a generic gateway for any integration.

## Architecture

```
Cloud Copilot/Power Automate → PAD (unattended) → Bridge (REST) → Splunk MCP Server (HTTP)
```

The bridge service acts as a translator between:
- **REST API**: Simple HTTP endpoints that PAD can call
- **MCP Protocol**: JSON-RPC 2.0 messages for Splunk MCP Server

## Features

- ✅ **REST API** for listing and executing Splunk MCP tools
- ✅ **REST API** for listing and reading Splunk MCP resources
- ✅ **Async HTTP** communication with MCP server
- ✅ **Error handling** with consistent JSON responses
- ✅ **CORS support** for cross-origin requests
- ✅ **Health check** endpoint for monitoring
- ✅ **Configurable** via environment variables

## Installation

### Prerequisites

- Python 3.11 or higher
- Access to a running Splunk MCP Server

### Setup

1. **Clone or navigate to the project directory**:
   ```bash
   cd splunk-mcp-bridge
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Alternatively, for development:*
   ```bash
   pip install -e .
   ```

4. **Configure environment variables**:
   ```bash
   copy .env.example .env
   ```
   
   Edit `.env` and set your Splunk MCP Server URL:
   ```env
   SPLUNK_MCP_SERVER_URL=http://localhost:3001/mcp
   ```

## Usage

### Starting the Bridge Service

```bash
python -m src.main
```

The service will start on `http://localhost:8000` by default.

### API Endpoints

#### Health Check
```http
GET /health
```

Returns the health status and MCP connection state.

#### List Tools
```http
GET /api/tools
```

Returns all available Splunk tools from the MCP server.

**Example Response**:
```json
{
  "tools": [
    {
      "name": "search",
      "description": "Execute Splunk search",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": {"type": "string"},
          "earliest_time": {"type": "string"}
        }
      }
    }
  ]
}
```

#### Execute Tool
```http
POST /api/tools/{tool_name}
Content-Type: application/json

{
  "arguments": {
    "query": "index=main | head 10",
    "earliest_time": "-1h"
  }
}
```

**Example Response**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "Search results..."
    }
  ],
  "isError": false
}
```

#### List Resources
```http
GET /api/resources
```

Returns all available resources from the MCP server.

#### Read Resource
```http
GET /api/resources/{uri}
```

Reads a specific resource by URI.

## Configuration

All configuration is done via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `BRIDGE_HOST` | `0.0.0.0` | Host to bind the bridge service |
| `BRIDGE_PORT` | `8000` | Port for the bridge service |
| `SPLUNK_MCP_SERVER_URL` | `http://localhost:3001/mcp` | Splunk MCP Server URL |
| `SPLUNK_MCP_AUTH_TOKEN` | (empty) | Splunk MCP Bearer Token (must have 'mcp' audience) |
| `SPLUNK_MCP_SERVER_TIMEOUT` | `30` | Request timeout in seconds |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |

## Integration with Power Automate Desktop

### Example PAD Flow

1. **HTTP Request Action** to list tools:
   ```
   URL: http://localhost:8000/api/tools
   Method: GET
   ```

2. **Call from PAD**: Use the "Invoke HTTP Request" action in PAD (or curl for Windows testing):
    ```powershell
    # Windows PowerShell Example
    curl.exe -X POST http://localhost:8000/api/tools/search `
      -H "Content-Type: application/json" `
      -d "{\"arguments\": {\"query\": \"index=main | head 5\"}}"
    ```
   **PAD "Invoke HTTP Request" Action**:
   ```
   URL: http://localhost:8000/api/tools/search
   Method: POST
   Headers: Content-Type: application/json
   Body: {"arguments": {"query": "index=main | head 5"}}
   ```

3. **Parse JSON** to extract results from the response

## Development

### Project Structure

```
Splunk_MCP_Bridge/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── mcp_client.py        # MCP client implementation
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── error_handler.py # Error handling
│   └── routers/
│       ├── __init__.py
│       ├── tools.py         # Tools endpoints
│       └── resources.py     # Resources endpoints
├── pyproject.toml           # Project configuration
├── .env.example             # Environment template
├── .gitignore
└── README.md
```

### Running in Development Mode

```bash
python -m src.main
```

This starts the server with auto-reload enabled.

### Testing

Test the API using curl or any HTTP client:

```bash
# Health check
curl http://localhost:8000/health

# List tools
curl http://localhost:8000/api/tools

# Execute tool (Windows PowerShell example)
curl.exe -X POST http://localhost:8000/api/tools/search `
  -H "Content-Type: application/json" `
  -d "{\"arguments\": {\"query\": \"index=main | head 5\"}}"
```

## Troubleshooting

### Connection Issues

If the bridge cannot connect to the Splunk MCP Server:

1. Verify the `SPLUNK_MCP_SERVER_URL` in `.env`
2. Ensure the Splunk MCP Server is running
3. Check network connectivity
4. Review logs for detailed error messages

### CORS Errors

If you encounter CORS errors from a web browser:

1. Update `CORS_ORIGINS` in `.env` to include your origin
2. Restart the bridge service

## License

This project is provided as-is for integration with Splunk MCP Server and Power Automate Desktop.
