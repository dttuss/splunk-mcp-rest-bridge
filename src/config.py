"""Configuration management for Splunk MCP Bridge."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server Configuration
    bridge_host: str = Field(default="0.0.0.0", description="Bridge service host")
    bridge_port: int = Field(default=8000, description="Bridge service port")

    # Splunk MCP Server Configuration
    splunk_mcp_server_url: str = Field(
        default="http://localhost:3001/mcp",
        description="Splunk MCP Server URL",
    )
    splunk_mcp_auth_token: str = Field(
        default="",
        description="Splunk MCP Authentication Token (Bearer)",
    )
    splunk_mcp_server_timeout: int = Field(default=30, description="MCP server request timeout in seconds")
    splunk_mcp_server_verify_ssl: bool = Field(default=True, description="Verify SSL certificate for MCP server")
    
    # Bridge Security Configuration
    bridge_api_key: Optional[str] = Field(default=None, description="API Key for securing bridge endpoints")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    bridge_log_payloads: bool = Field(
        default=False,
        description="Whether to log full request/response payloads for auditing",
    )

    # CORS Configuration
    cors_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
