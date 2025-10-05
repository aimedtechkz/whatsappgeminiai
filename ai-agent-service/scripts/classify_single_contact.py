"""
Script to classify a single contact
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from loguru import logger

from config.database import get_db
from models.contact import Contact
from models.message import Message
from services.ai_moderator import AIModeratorService
from services.ai_sales_agent import AISalesAgentService


def classify_contact(contact_id: int):
    """Classify a specific contact by ID"""
    db = next(get_db())

    try:
        # Initialize AI services
        ai_moderator = AIModeratorService()
        ai_sales_agent = AISalesAgentService()

        # Get the contact
        contact = db.query(Contact).filter(Contact.id == contact_id).first()

        if not contact:
            logger.error(f"Contact {contact_id} not found")
            return

        # Check message count
        message_count = db.query(Message).filter(
            Message.contact_id == contact.id
        ).count()

        logger.info(f"Contact {contact.id} ({contact.phone_number}) has {message_count} messages")
        logger.info(f"Current classification: {contact.is_client}")

        # Classify
        logger.info(f"Classifying contact {contact.id}...")
        is_client = ai_moderator.classify_contact(contact.id, db)

        # Refresh
        db.refresh(contact)

        logger.info(f"Classification result: {is_client}")
        logger.info(f"Contact is_client field: {contact.is_client}")

        if is_client:
            logger.success(f"✅ Contact classified as CLIENT")

            # Get last message
            last_message = db.query(Message).filter(
                Message.contact_id == contact.id,
                Message.sender == "client"
            ).order_by(Message.created_at.desc()).first()

            if last_message:
                logger.info(f"Generating response to: {last_message.message_text[:100]}")
                ai_sales_agent.generate_response(
                    contact.id,
                    last_message.message_text,
                    db
                )
                logger.success(f"✅ Response generated")
        elif is_client is False:
            logger.info(f"❌ Contact classified as NOT CLIENT")
        else:
            logger.warning(f"⚠️ Classification uncertain")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    contact_id = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    logger.info(f"Classifying contact ID: {contact_id}")
    classify_contact(contact_id)
