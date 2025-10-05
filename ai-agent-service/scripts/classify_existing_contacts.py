"""
Script to classify existing unclassified contacts
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


def classify_existing_contacts():
    """Classify all existing contacts that have messages but are not classified"""
    db = next(get_db())

    try:
        # Initialize AI services
        ai_moderator = AIModeratorService()
        ai_sales_agent = AISalesAgentService()

        # Get all unclassified contacts
        unclassified_contacts = db.query(Contact).filter(
            Contact.is_client == None
        ).all()

        logger.info(f"Found {len(unclassified_contacts)} unclassified contacts")

        classified_count = 0
        client_count = 0

        for contact in unclassified_contacts:
            # Check if contact has any messages
            message_count = db.query(Message).filter(
                Message.contact_id == contact.id
            ).count()

            if message_count == 0:
                logger.debug(f"Skipping contact {contact.id} ({contact.phone_number}) - no messages")
                continue

            logger.info(f"Classifying contact {contact.id} ({contact.phone_number}) with {message_count} messages")

            # Classify the contact
            is_client = ai_moderator.classify_contact(contact.id, db)

            # Refresh to get updated classification
            db.refresh(contact)

            classified_count += 1

            if is_client:
                client_count += 1
                logger.success(f"✅ Contact {contact.id} classified as CLIENT")

                # Get the last message from this contact
                last_message = db.query(Message).filter(
                    Message.contact_id == contact.id,
                    Message.sender == "client"
                ).order_by(Message.created_at.desc()).first()

                if last_message:
                    # Generate response to the last message
                    logger.info(f"Generating response to last message: {last_message.message_text[:50]}...")
                    ai_sales_agent.generate_response(
                        contact.id,
                        last_message.message_text,
                        db
                    )
                    logger.success(f"✅ Response generated for contact {contact.id}")
            elif is_client is False:
                logger.info(f"❌ Contact {contact.id} classified as NOT CLIENT")
            else:
                logger.warning(f"⚠️ Contact {contact.id} classification uncertain")

        logger.success(f"\n=== Classification Complete ===")
        logger.success(f"Total classified: {classified_count}")
        logger.success(f"Clients: {client_count}")
        logger.success(f"Non-clients: {classified_count - client_count}")

    except Exception as e:
        logger.error(f"Error during classification: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting contact classification script...")
    classify_existing_contacts()
    logger.info("Classification script completed")
