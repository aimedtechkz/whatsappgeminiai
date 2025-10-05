"""
AI Moderator Service
Classifies contacts as clients or non-clients using Gemini AI
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime

from services.gemini_client import GeminiClient
from config.database import get_db
from models.contact import Contact
from models.message import Message


class AIModeratorService:
    """Service to classify contacts using AI"""

    def __init__(self):
        self.gemini_client = GeminiClient()
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load moderator prompt from file"""
        try:
            with open("prompts/moderator_prompt.txt", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error("Moderator prompt file not found")
            return ""

    def get_conversation_history(self, contact_id: int, db: Session, limit: int = 20) -> List[Message]:
        """Get last N messages for contact"""
        messages = db.query(Message).filter(
            Message.contact_id == contact_id
        ).order_by(Message.timestamp.desc()).limit(limit).all()

        return list(reversed(messages))  # Chronological order

    def format_conversation_for_prompt(self, messages: List[Message]) -> str:
        """Format messages for prompt"""
        if not messages:
            return "Нет сообщений в переписке"

        formatted = []
        for msg in messages:
            sender = "БОТ" if msg.is_from_bot else "КЛИЕНТ"
            text = msg.message_text or ""
            if msg.is_voice and msg.voice_transcription:
                text = f"[ГОЛОСОВОЕ] {msg.voice_transcription}"
            formatted.append(f"{sender}: {text}")

        return "\n".join(formatted)

    def parse_classification_result(self, json_result: Dict[str, Any]) -> tuple:
        """
        Parse classification JSON result

        Returns:
            (is_client, confidence, reasoning)
        """
        try:
            is_client = json_result.get("isClient")
            confidence = float(json_result.get("confidence", 0.0))
            reasoning = json_result.get("reasoning", "")

            # Validate
            if is_client not in [True, False, None]:
                logger.warning(f"Invalid isClient value: {is_client}")
                return None, 0.0, "Invalid classification result"

            return is_client, confidence, reasoning

        except Exception as e:
            logger.error(f"Error parsing classification result: {e}")
            return None, 0.0, str(e)

    def save_classification(
        self,
        contact_id: int,
        is_client: bool,
        confidence: float,
        reasoning: str,
        db: Session
    ) -> None:
        """Save classification result to database"""
        try:
            contact = db.query(Contact).filter(Contact.id == contact_id).first()

            if contact:
                contact.is_client = is_client
                contact.classification_confidence = confidence
                contact.classification_reasoning = reasoning
                contact.updated_at = datetime.now()
                db.commit()
                logger.success(f"Saved classification for contact {contact_id}: is_client={is_client}")
            else:
                logger.error(f"Contact {contact_id} not found")

        except Exception as e:
            logger.error(f"Error saving classification: {e}")
            db.rollback()

    def classify_contact(self, contact_id: int, db: Session = None) -> Optional[bool]:
        """
        Classify contact as client or not

        Args:
            contact_id: Contact ID
            db: Database session

        Returns:
            True if client, False if not, None if uncertain
        """
        if db is None:
            db = next(get_db())

        try:
            # Get contact
            contact = db.query(Contact).filter(Contact.id == contact_id).first()

            if not contact:
                logger.error(f"Contact {contact_id} not found")
                return None

            # Get conversation history
            messages = self.get_conversation_history(contact_id, db)

            if len(messages) < 1:
                logger.info(f"Not enough messages ({len(messages)}) to classify contact {contact_id}")
                return None

            # Format conversation
            conversation_text = self.format_conversation_for_prompt(messages)

            # Prepare prompt
            prompt = self.prompt_template.format(
                contact_name=contact.name or "Неизвестно",
                full_name=contact.full_name or "Неизвестно",
                business_name=contact.business_name or "Нет",
                conversation_history=conversation_text
            )

            # Call Gemini
            logger.info(f"Classifying contact {contact_id}...")
            result = self.gemini_client.classify_json(prompt, temperature=0.1)

            if not result:
                logger.error(f"Failed to get classification result for contact {contact_id}")
                return None

            logger.debug(f"Raw Gemini result: {result}")
            logger.debug(f"isClient type: {type(result.get('isClient'))}, value: {repr(result.get('isClient'))}")

            # Parse result
            is_client, confidence, reasoning = self.parse_classification_result(result)

            # Save to database
            if is_client is not None:
                self.save_classification(contact_id, is_client, confidence, reasoning, db)

            logger.info(f"Classification result for {contact.phone_number}: is_client={is_client}, confidence={confidence:.2f}")
            logger.info(f"Reasoning: {reasoning}")

            return is_client

        except Exception as e:
            import traceback
            logger.error(f"Error in classify_contact: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
