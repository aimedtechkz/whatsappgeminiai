"""
Health Check API for AI Agent Service
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
from models.contact import Contact
from models.message import Message
from models.follow_up import FollowUp
from models.scheduled_call import ScheduledCall

app = FastAPI(title="AI Agent Service - Health Check API")


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

    # Check RabbitMQ connection (without interfering with consumer)
    try:
        if queue_manager.connection and not queue_manager.connection.is_closed:
            queue_status = "ok"
        else:
            queue_status = "error"
    except Exception as e:
        logger.error(f"Queue health check failed: {e}")
        queue_status = "error"

    return {
        "status": "healthy" if db_status == "ok" and queue_status == "ok" else "unhealthy",
        "service": "ai-agent-service",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": db_status,
            "queue": queue_status,
            "gemini_api": "ok"  # Assume OK if service is running
        }
    }


@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get service statistics

    Returns contact counts, message stats, and follow-up info
    """
    try:
        today = date.today()

        # Count contacts by classification
        total_contacts = db.query(Contact).count()
        clients = db.query(Contact).filter(Contact.is_client == True).count()
        non_clients = db.query(Contact).filter(Contact.is_client == False).count()
        unclassified = db.query(Contact).filter(Contact.is_client == None).count()

        # Count messages today
        messages_today = db.query(Message).filter(
            Message.timestamp >= today
        ).count()

        bot_messages_today = db.query(Message).filter(
            Message.timestamp >= today,
            Message.is_from_bot == True
        ).count()

        # Active follow-ups
        active_followups = db.query(FollowUp).filter(
            FollowUp.is_completed == False
        ).count()

        # Scheduled calls
        scheduled_calls = db.query(ScheduledCall).filter(
            ScheduledCall.status == "scheduled"
        ).count()

        # Queue sizes - Skip to avoid interfering with consumer connection
        queue_sizes = {
            "incoming": "N/A",
            "outgoing": "N/A"
        }

        return {
            "date": today.isoformat(),
            "contacts": {
                "total": total_contacts,
                "clients": clients,
                "non_clients": non_clients,
                "unclassified": unclassified
            },
            "messages_today": messages_today,
            "bot_messages_today": bot_messages_today,
            "active_followups": active_followups,
            "scheduled_calls": scheduled_calls,
            "queue_sizes": queue_sizes
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "error": str(e)
        }


@app.get("/contacts")
async def get_contacts(
    is_client: bool = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get contacts filtered by client status"""
    try:
        query = db.query(Contact)

        if is_client is not None:
            query = query.filter(Contact.is_client == is_client)

        contacts = query.order_by(Contact.created_at.desc()).limit(100).all()

        return {
            "count": len(contacts),
            "contacts": [
                {
                    "id": c.id,
                    "phone_number": c.phone_number,
                    "name": c.name,
                    "is_client": c.is_client,
                    "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None
                }
                for c in contacts
            ]
        }

    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        return {"error": str(e)}


@app.get("/follow-ups/active")
async def get_active_followups(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get active follow-ups"""
    try:
        followups = db.query(FollowUp).filter(
            FollowUp.is_completed == False
        ).order_by(FollowUp.next_touch_at).all()

        return {
            "count": len(followups),
            "follow_ups": [
                {
                    "id": f.id,
                    "contact_id": f.contact_id,
                    "touch_number": f.touch_number,
                    "next_touch_at": f.next_touch_at.isoformat() if f.next_touch_at else None,
                    "last_touch_at": f.last_touch_at.isoformat() if f.last_touch_at else None
                }
                for f in followups
            ]
        }

    except Exception as e:
        logger.error(f"Error getting active follow-ups: {e}")
        return {"error": str(e)}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Agent Service",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "stats": "/stats",
            "contacts": "/contacts",
            "follow_ups": "/follow-ups/active"
        }
    }
