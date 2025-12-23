"""Initialize routers package."""

from src.routers.tools import router as tools_router
from src.routers.resources import router as resources_router

__all__ = ["tools_router", "resources_router"]
