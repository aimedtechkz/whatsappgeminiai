"""
Logging configuration using loguru
"""
import sys
from loguru import logger
from config.settings import settings

# Remove default handler
logger.remove()

# Add console handler with color formatting
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True
)

# Add file handler with rotation
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # Rotate at midnight
    retention="30 days",  # Keep logs for 30 days
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    enqueue=True  # Thread-safe logging
)


def log_incoming_message(message_data: dict) -> None:
    """Log incoming message from queue"""
    logger.info(f"📥 Processing incoming message from {message_data.get('phone_number')}")


def log_outgoing_message(message_data: dict) -> None:
    """Log outgoing message to queue"""
    logger.info(f"📤 Sending response to {message_data.get('phone_number')}")


def log_classification(phone: str, is_client: bool, confidence: float) -> None:
    """Log contact classification"""
    status = "CLIENT" if is_client else "NOT CLIENT"
    logger.info(f"🏷️  Classified {phone} as {status} (confidence: {confidence:.2f})")


def log_error(service_name: str, error: Exception, context: dict = None) -> None:
    """Log error with context"""
    logger.error(f"❌ Error in {service_name}: {str(error)}")
    if context:
        logger.error(f"Context: {context}")


def log_followup(contact_id: int, touch_number: int) -> None:
    """Log follow-up activity"""
    logger.info(f"📞 Follow-up touch #{touch_number} for contact {contact_id}")
