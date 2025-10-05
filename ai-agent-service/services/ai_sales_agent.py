"""
AI Sales Agent Service
Generates sales responses using Gemini AI and SPIN selling methodology
"""
import re
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime

from services.gemini_client import GeminiClient
from services.knowledge_loader import KnowledgeBaseLoader
from config.queue import queue_manager
from config.settings import settings
from config.database import get_db
from models.contact import Contact
from models.message import Message
from models.scheduled_call import ScheduledCall
from utils.timezone_helper import (
    get_current_time_astana,
    is_working_hours,
    format_datetime_for_user,
    get_next_working_time
)


class AISalesAgentService:
    """AI Sales Agent for generating client responses"""

    def __init__(self):
        self.gemini_client = GeminiClient()
        self.knowledge_loader = KnowledgeBaseLoader()
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load sales agent prompt from file"""
        try:
            with open("prompts/sales_agent_prompt.txt", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error("Sales agent prompt file not found")
            return ""

    def get_conversation_context(self, contact_id: int, db: Session, limit: int = 20) -> List[Message]:
        """Get last N messages for context"""
        messages = db.query(Message).filter(
            Message.contact_id == contact_id
        ).order_by(Message.timestamp.desc()).limit(limit).all()

        return list(reversed(messages))  # Chronological order

    def format_context_for_gemini(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Format messages in Gemini conversation format"""
        formatted = []

        for msg in messages:
            role = "model" if msg.is_from_bot else "user"
            text = msg.message_text or ""

            if msg.is_voice and msg.voice_transcription:
                text = f"[ГОЛОСОВОЕ] {msg.voice_transcription}"

            formatted.append({
                "role": role,
                "parts": [{"text": text}]
            })

        return formatted

    def check_for_call_scheduling(self, response_text: str, contact: Contact, db: Session) -> None:
        """Check if response mentions scheduling a call and save it"""
        # Keywords that indicate call scheduling
        call_keywords = [
            "записал на",
            "созвонимся",
            "позвоним",
            "запланировал созвон",
            "назначил встречу"
        ]

        if any(keyword in response_text.lower() for keyword in call_keywords):
            # Try to extract date/time
            # This is a simple implementation - can be enhanced
            logger.info(f"Detected call scheduling in response for contact {contact.id}")

            # For now, just create a placeholder scheduled call
            try:
                # Get next working time
                next_time = get_next_working_time()

                scheduled_call = ScheduledCall(
                    contact_id=contact.id,
                    scheduled_at=next_time,
                    timezone="Asia/Almaty",
                    status="scheduled",
                    notes=f"Автоматически создано из ответа бота: {response_text[:200]}"
                )
                db.add(scheduled_call)
                db.commit()
                logger.success(f"Created scheduled call for contact {contact.id} at {next_time}")
            except Exception as e:
                logger.error(f"Failed to create scheduled call: {e}")
                db.rollback()

    def publish_response(
        self,
        phone_number: str,
        response_text: str,
        reply_to_id: str = None
    ) -> None:
        """Publish response to outgoing messages queue"""
        message_data = {
            "phone_number": phone_number,
            "message_text": response_text,
            "reply_to_message_id": reply_to_id,
            "mark_as_read": True
        }

        queue_manager.publish(settings.QUEUE_OUTGOING_MESSAGES, message_data)
        logger.success(f"Published response to outgoing queue for {phone_number}")

    def generate_response(
        self,
        contact_id: int,
        new_message: str,
        db: Session = None
    ) -> Optional[str]:
        """
        Generate AI sales response

        Args:
            contact_id: Contact ID
            new_message: New message from client
            db: Database session

        Returns:
            Generated response text
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
            messages = self.get_conversation_context(contact_id, db)

            # Load knowledge base
            knowledge_base = self.knowledge_loader.get_full_knowledge()

            # Get current time
            current_time = get_current_time_astana()
            current_datetime_str = format_datetime_for_user(current_time)

            # Format conversation history for display
            conversation_display = "\n".join([
                f"{'БОТ' if msg.is_from_bot else 'КЛИЕНТ'}: {msg.message_text}"
                for msg in messages
            ])

            # Prepare system prompt
            system_prompt = self.prompt_template.format(
                knowledge_base=knowledge_base[:3000],  # Limit to avoid token limits
                conversation_history=conversation_display,
                new_message=new_message,
                current_datetime=current_datetime_str
            )

            # Format for Gemini API
            gemini_history = self.format_context_for_gemini(messages)

            # Add new message
            gemini_history.append({
                "role": "user",
                "parts": [{"text": new_message}]
            })

            # Generate response
            logger.info(f"Generating sales response for contact {contact_id}...")
            response = self.gemini_client.generate_response(
                system_prompt=system_prompt,
                conversation_history=gemini_history[:-1],  # Exclude last message (it's in prompt)
                temperature=0.7
            )

            if not response:
                logger.error(f"Failed to generate response for contact {contact_id}")
                return None

            # Save response to database
            response_message = Message(
                contact_id=contact_id,
                phone_number=contact.phone_number,
                message_text=response,
                is_from_bot=True,
                timestamp=datetime.now()
            )
            db.add(response_message)
            db.commit()

            logger.success(f"Generated response for contact {contact_id}: {response[:100]}...")

            # Check for call scheduling
            self.check_for_call_scheduling(response, contact, db)

            # Publish to outgoing queue
            self.publish_response(contact.phone_number, response)

            return response

        except Exception as e:
            logger.error(f"Error generating sales response: {e}")
            return None
