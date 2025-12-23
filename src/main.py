"""Main FastAPI application for Splunk MCP Bridge."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config import settings
from src.mcp_client import mcp_client
from src.routers import tools_router, resources_router
from src.middleware import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    RequestLoggingMiddleware,
)
from src.middleware.auth_middleware import get_api_key

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None during application runtime
    """
    # Startup
    logger.info("Starting Splunk MCP Bridge...")
    logger.info(f"Bridge service running on {settings.bridge_host}:{settings.bridge_port}")
    logger.info(f"Connecting to Splunk MCP Server at {settings.splunk_mcp_server_url}")
    
    try:
        await mcp_client.connect()
        logger.info("Successfully connected to Splunk MCP Server")
    except Exception as e:
        logger.error(f"Failed to connect to MCP server: {e}")
        logger.warning("Bridge will attempt to connect on first request")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Splunk MCP Bridge...")
    await mcp_client.disconnect()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Splunk MCP Bridge",
    description="REST API bridge for Power Automate Desktop to Splunk MCP Server",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Register exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Register routers
app.include_router(tools_router, dependencies=[Depends(get_api_key)])
app.include_router(resources_router, dependencies=[Depends(get_api_key)])


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Splunk MCP Bridge",
        "version": "0.1.0",
        "status": "running",
        "mcp_server": settings.splunk_mcp_server_url,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Try to list tools to verify MCP connection
        await mcp_client.list_tools()
        return {
            "status": "healthy",
            "mcp_connection": "connected",
        }
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "mcp_connection": "disconnected",
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.bridge_host,
        port=settings.bridge_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
