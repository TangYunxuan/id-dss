"""
Application configuration settings.
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "sqlite:///./id_dss.db"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        # Production (GitHub Pages custom domain)
        "https://tangyunxuan.com",
        "https://www.tangyunxuan.com",
        "https://id-dss.tangyunxuan.com",
        # (legacy typo domain, keep if you ever used it)
        "https://tangyunxaun.com",
        "https://www.tangyunxaun.com",
    ]
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "ID-DSS Backend"
    DEBUG: bool = True
    
    # LLM Configuration
    LLM_PROVIDER: LLMProvider = LLMProvider.OPENAI
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
