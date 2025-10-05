"""
AI Agent Service - Main Application
Handles AI classification, sales responses, and follow-up sequences
"""
import asyncio
import signal
import sys
import threading
from loguru import logger
import uvicorn

from config.settings import settings
from config.database import init_db
from services.message_consumer import MessageConsumerService
from services.follow_up_scheduler import FollowUpSchedulerService
from api.health import app as health_app


# Global services
consumer_service = None
scheduler_service = None
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


def run_consumer_service():
    """Run message consumer service in separate thread"""
    global consumer_service
    consumer_service = MessageConsumerService()
    consumer_service.start_consuming()


async def run_scheduler_service():
    """Run follow-up scheduler service"""
    global scheduler_service
    scheduler_service = FollowUpSchedulerService()
    await scheduler_service.start_scheduler()


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
    logger.info("🚀 Starting AI Agent Service")
    logger.info("=" * 60)
    logger.info(f"Project: {settings.PROJECT_NAME}")
    logger.info(f"Max Context Messages: {settings.MAX_CONTEXT_MESSAGES}")
    logger.info(f"Follow-ups Enabled: {settings.ENABLE_FOLLOW_UPS}")
    logger.info(f"Working Hours: {settings.WORKING_HOURS_START}:00 - {settings.WORKING_HOURS_END}:00")
    logger.info(f"Health Check Port: {settings.HEALTH_CHECK_PORT}")
    logger.info(f"Timezone: {settings.TIMEZONE}")
    logger.info("=" * 60)

    # Start health check API in separate thread
    health_thread = threading.Thread(target=run_health_api, daemon=True)
    health_thread.start()
    logger.info(f"✅ Health API started on port {settings.HEALTH_CHECK_PORT}")

    # Start consumer service in separate thread
    consumer_thread = threading.Thread(target=run_consumer_service, daemon=True)
    consumer_thread.start()
    logger.info("✅ Message consumer service started")

    # Run scheduler service in main thread (if enabled)
    if settings.ENABLE_FOLLOW_UPS:
        try:
            await run_scheduler_service()
        except Exception as e:
            logger.error(f"❌ Scheduler service error: {e}")
    else:
        logger.warning("⚠️  Follow-up scheduler is disabled")
        # Just wait for shutdown
        await shutdown_event.wait()

    # Cleanup
    logger.info("🧹 Cleaning up services...")
    if scheduler_service:
        scheduler_service.stop_scheduler()

    logger.info("👋 AI Agent Service stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
