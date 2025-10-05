"""
WhatsApp Gateway Service - Main Application
Handles WhatsApp message polling, sending, and voice transcription
"""
import asyncio
import signal
import sys
import threading
from loguru import logger
import uvicorn

from config.settings import settings
from config.database import init_db
from services.polling_service import MessagePollingService
from services.sender_service import MessageSenderService
from services.voice_service import VoiceTranscriptionService
from api.health import app as health_app


# Global services
polling_service = None
sender_service = None
voice_service = None
shutdown_event = asyncio.Event()


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("🛑 Shutdown signal received")
    shutdown_event.set()


def run_health_api():
    """Run health check API in separate thread"""
    uvicorn.run(
        health_app,
        host="0.0.0.0",
        port=settings.HEALTH_CHECK_PORT,
        log_level="info"
    )


def run_sender_service():
    """Run sender service in separate thread"""
    global sender_service
    sender_service = MessageSenderService()
    sender_service.start_consuming()


def run_voice_service():
    """Run voice transcription service in separate thread"""
    global voice_service
    voice_service = VoiceTranscriptionService()
    voice_service.start_consuming()


async def run_polling_service():
    """Run polling service"""
    global polling_service
    polling_service = MessagePollingService()
    await polling_service.start_polling()


async def main():
    """Main application entry point"""
    # Validate settings
    try:
        settings.validate_required()
        logger.info("✅ Settings validated successfully")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        sys.exit(1)

    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 60)
    logger.info("🚀 Starting WhatsApp Gateway Service")
    logger.info("=" * 60)
    logger.info(f"Project: {settings.PROJECT_NAME}")
    logger.info(f"Polling Interval: {settings.POLLING_INTERVAL}s")
    logger.info(f"Health Check Port: {settings.HEALTH_CHECK_PORT}")
    logger.info(f"Timezone: {settings.TIMEZONE}")
    logger.info("=" * 60)

    # Start health check API in separate thread
    health_thread = threading.Thread(target=run_health_api, daemon=True)
    health_thread.start()
    logger.info(f"✅ Health API started on port {settings.HEALTH_CHECK_PORT}")

    # Start sender service in separate thread
    sender_thread = threading.Thread(target=run_sender_service, daemon=True)
    sender_thread.start()
    logger.info("✅ Sender service started")

    # Start voice service in separate thread
    voice_thread = threading.Thread(target=run_voice_service, daemon=True)
    voice_thread.start()
    logger.info("✅ Voice transcription service started")

    # Run polling service in main thread
    try:
        await run_polling_service()
    except Exception as e:
        logger.error(f"❌ Polling service error: {e}")

    # Wait for shutdown
    await shutdown_event.wait()

    # Cleanup
    logger.info("🧹 Cleaning up services...")
    if polling_service:
        polling_service.stop_polling()

    logger.info("👋 WhatsApp Gateway Service stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
