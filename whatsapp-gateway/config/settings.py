"""
Configuration settings for WhatsApp Gateway Service
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Project
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "whatsapp-gateway")

    # Wappi API
    WAPPI_TOKEN: str = os.getenv("WAPPI_TOKEN", "")
    WAPPI_PROFILE_ID: str = os.getenv("WAPPI_PROFILE_ID", "")
    WAPPI_PHONE_NUMBER: str = os.getenv("WAPPI_PHONE_NUMBER", "77752837306")
    WAPPI_BASE_URL: str = os.getenv("WAPPI_BASE_URL", "https://wappi.pro")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "")
    QUEUE_INCOMING_MESSAGES: str = os.getenv("QUEUE_INCOMING_MESSAGES", "incoming_messages")
    QUEUE_OUTGOING_MESSAGES: str = os.getenv("QUEUE_OUTGOING_MESSAGES", "outgoing_messages")
    QUEUE_VOICE_TRANSCRIPTION: str = os.getenv("QUEUE_VOICE_TRANSCRIPTION", "voice_transcription")

    # Gemini API (for voice transcription)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

    # Settings
    POLLING_INTERVAL: int = int(os.getenv("POLLING_INTERVAL", "5"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Almaty")
    HEALTH_CHECK_PORT: int = int(os.getenv("HEALTH_CHECK_PORT", "8000"))

    def validate_required(self) -> bool:
        """Validate that all required settings are present"""
        required = {
            "WAPPI_TOKEN": self.WAPPI_TOKEN,
            "WAPPI_PROFILE_ID": self.WAPPI_PROFILE_ID,
            "DATABASE_URL": self.DATABASE_URL,
            "RABBITMQ_URL": self.RABBITMQ_URL,
            "GEMINI_API_KEY": self.GEMINI_API_KEY
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
