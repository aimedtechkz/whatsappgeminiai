"""
Configuration settings for AI Agent Service
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Project
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "ai-agent-service")

    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "")
    QUEUE_INCOMING_MESSAGES: str = os.getenv("QUEUE_INCOMING_MESSAGES", "incoming_messages")
    QUEUE_OUTGOING_MESSAGES: str = os.getenv("QUEUE_OUTGOING_MESSAGES", "outgoing_messages")

    # Settings
    MAX_CONTEXT_MESSAGES: int = int(os.getenv("MAX_CONTEXT_MESSAGES", "20"))
    ENABLE_FOLLOW_UPS: bool = os.getenv("ENABLE_FOLLOW_UPS", "true").lower() == "true"
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Almaty")
    WORKING_HOURS_START: int = int(os.getenv("WORKING_HOURS_START", "10"))
    WORKING_HOURS_END: int = int(os.getenv("WORKING_HOURS_END", "18"))

    # Follow-up intervals (in hours)
    @property
    def FOLLOW_UP_INTERVALS(self) -> List[int]:
        intervals_str = os.getenv("FOLLOW_UP_INTERVALS", "24,72,168,336,720")
        return [int(x.strip()) for x in intervals_str.split(",")]

    # Knowledge Base
    KNOWLEDGE_BASE_PATH: str = os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge_base/")
    PDF_CACHE_ENABLED: bool = os.getenv("PDF_CACHE_ENABLED", "true").lower() == "true"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    HEALTH_CHECK_PORT: int = int(os.getenv("HEALTH_CHECK_PORT", "8001"))

    def validate_required(self) -> bool:
        """Validate that all required settings are present"""
        required = {
            "GEMINI_API_KEY": self.GEMINI_API_KEY,
            "DATABASE_URL": self.DATABASE_URL,
            "RABBITMQ_URL": self.RABBITMQ_URL
        }

        missing = [key for key, value in required.items() if not value]

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return True

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env parsing


# Global settings instance
settings = Settings()
