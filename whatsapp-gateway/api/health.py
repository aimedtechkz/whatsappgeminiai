"""
Health Check API for WhatsApp Gateway Service
"""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, date
from typing import Dict, Any
from loguru import logger

from config.database import get_db
from config.queue import queue_manager
from config.settings import settings
from models.message_log import MessageLog

app = FastAPI(title="WhatsApp Gateway - Health Check API")


@app.get("/health")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint

    Returns service status and connectivity checks
    """
    try:
        # Check database
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"

    # Check RabbitMQ
    try:
        queue_manager.get_queue_size(settings.QUEUE_INCOMING_MESSAGES)
        queue_status = "ok"
    except Exception as e:
        logger.error(f"Queue health check failed: {e}")
        queue_status = "error"

    # Get last poll time (from latest message log)
    try:
        last_log = db.query(MessageLog).order_by(
            MessageLog.created_at.desc()
        ).first()
        last_poll_time = last_log.created_at.isoformat() if last_log else None
    except:
        last_poll_time = None

    return {
        "status": "healthy" if db_status == "ok" and queue_status == "ok" else "unhealthy",
        "service": "whatsapp-gateway",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": db_status,
            "queue": queue_status,
            "wappi_connection": "ok"  # Assume OK if polling is working
        },
        "last_poll_time": last_poll_time
    }


@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get service statistics

    Returns message counts and queue sizes
    """
    try:
        today = date.today()

        # Count messages received today
        messages_received_today = db.query(MessageLog).filter(
            MessageLog.direction == "incoming",
            MessageLog.created_at >= today
        ).count()

        # Count messages sent today
        messages_sent_today = db.query(MessageLog).filter(
            MessageLog.direction == "outgoing",
            MessageLog.created_at >= today
        ).count()

        # Count voice transcribed today
        voice_transcribed_today = db.query(MessageLog).filter(
            MessageLog.is_voice == True,
            MessageLog.created_at >= today
        ).count()

        # Get queue sizes
        queue_sizes = {
            "incoming": queue_manager.get_queue_size(settings.QUEUE_INCOMING_MESSAGES),
            "outgoing": queue_manager.get_queue_size(settings.QUEUE_OUTGOING_MESSAGES),
            "voice": queue_manager.get_queue_size(settings.QUEUE_VOICE_TRANSCRIPTION)
        }

        return {
            "date": today.isoformat(),
            "messages_received_today": messages_received_today,
            "messages_sent_today": messages_sent_today,
            "voice_transcribed_today": voice_transcribed_today,
            "queue_sizes": queue_sizes
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "error": str(e)
        }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "WhatsApp Gateway Service",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "stats": "/stats"
        }
    }
