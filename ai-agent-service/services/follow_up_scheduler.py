"""
Follow-up Scheduler Service
Manages 5-touch follow-up sequences for clients
"""
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from loguru import logger

from services.gemini_client import GeminiClient
from config.queue import queue_manager
from config.settings import settings
from config.database import get_db
from models.contact import Contact
from models.message import Message
from models.follow_up import FollowUp
from utils.timezone_helper import (
    get_current_time_astana,
    hours_since,
    format_datetime_for_user
)


class FollowUpSchedulerService:
    """Scheduler for follow-up sequences"""

    def __init__(self):
        self.gemini_client = GeminiClient()
        self.prompt_template = self._load_prompt_template()
        self.is_running = False

    def _load_prompt_template(self) -> str:
        """Load follow-up prompt from file"""
        try:
            with open("prompts/follow_up_prompt.txt", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error("Follow-up prompt file not found")
            return ""

    def should_start_followup(self, contact: Contact, db: Session) -> bool:
        """
        Determine if contact needs follow-up

        Returns:
            True if follow-up should start
        """
        # Get last messages
        last_messages = db.query(Message).filter(
            Message.contact_id == contact.id
        ).order_by(Message.timestamp.desc()).limit(2).all()

        if len(last_messages) < 1:
            return False

        last_message = last_messages[0]

        # Check if last message was from bot
        if not last_message.is_from_bot:
            return False

        # Check time since last message
        hours_passed = hours_since(last_message.timestamp)
        if hours_passed < 24:
            return False

        # Check if client responded after bot's message
        if len(last_messages) >= 2:
            second_last = last_messages[1]
            # If client responded after bot, no follow-up needed
            if second_last.timestamp > last_message.timestamp and not second_last.is_from_bot:
                return False

        # Check for active follow-up
        active_followup = db.query(FollowUp).filter(
            FollowUp.contact_id == contact.id,
            FollowUp.is_completed == False
        ).first()

        if active_followup:
            return False

        # Analyze last client response if exists
        client_messages = [m for m in last_messages if not m.is_from_bot]
        if client_messages:
            last_client_msg = client_messages[0].message_text.lower()

            # Check for definitive YES
            yes_keywords = ["да", "согласен", "готов", "давайте", "хорошо", "ок", "окей"]
            if any(keyword in last_client_msg for keyword in yes_keywords):
                logger.info(f"Client said YES, no follow-up needed for contact {contact.id}")
                return False

            # Check for definitive NO
            no_keywords = ["нет", "не надо", "не интересно", "не сейчас", "откажусь", "отказываюсь"]
            if any(keyword in last_client_msg for keyword in no_keywords):
                logger.info(f"Client said NO, no follow-up needed for contact {contact.id}")
                return False

        return True

    def analyze_last_response(self, message_text: str) -> str:
        """Analyze client's last response type"""
        if not message_text:
            return "ignored"

        text_lower = message_text.lower()

        # YES responses
        yes_keywords = ["да", "согласен", "готов", "давайте", "хорошо", "ок"]
        if any(keyword in text_lower for keyword in yes_keywords):
            return "yes"

        # NO responses
        no_keywords = ["нет", "не надо", "не интересно", "не сейчас"]
        if any(keyword in text_lower for keyword in no_keywords):
            return "no"

        # Uncertain responses
        uncertain_keywords = ["посмотрю", "подумаю", "может быть", "возможно"]
        if any(keyword in text_lower for keyword in uncertain_keywords):
            return "uncertain"

        return "ignored"

    def create_followup_chain(self, contact_id: int, db: Session) -> FollowUp:
        """Create new follow-up chain"""
        try:
            current_time = get_current_time_astana()
            # First touch after 24 hours
            next_touch_at = current_time + timedelta(hours=settings.FOLLOW_UP_INTERVALS[0])

            follow_up = FollowUp(
                contact_id=contact_id,
                touch_number=1,
                next_touch_at=next_touch_at,
                is_completed=False
            )
            db.add(follow_up)
            db.commit()
            logger.success(f"Created follow-up chain for contact {contact_id}, next touch at {next_touch_at}")
            return follow_up
        except Exception as e:
            logger.error(f"Error creating follow-up chain: {e}")
            db.rollback()
            return None

    def generate_followup_message(
        self,
        contact_id: int,
        touch_number: int,
        db: Session
    ) -> Optional[str]:
        """Generate follow-up message using AI"""
        try:
            # Get conversation history
            messages = db.query(Message).filter(
                Message.contact_id == contact_id
            ).order_by(Message.timestamp.desc()).limit(20).all()

            messages = list(reversed(messages))

            # Find last bot and client messages
            bot_messages = [m for m in messages if m.is_from_bot]
            client_messages = [m for m in messages if not m.is_from_bot]

            last_bot_message = bot_messages[-1].message_text if bot_messages else ""
            last_client_message = client_messages[-1].message_text if client_messages else ""

            # Format conversation
            conversation = "\n".join([
                f"{'БОТ' if m.is_from_bot else 'КЛИЕНТ'}: {m.message_text}"
                for m in messages
            ])

            # Determine reason
            response_type = self.analyze_last_response(last_client_message)
            reasons = {
                "ignored": "Клиент проигнорировал сообщение",
                "uncertain": "Клиент дал неопределенный ответ",
                "yes": "Клиент согласился",
                "no": "Клиент отказался"
            }
            follow_up_reason = reasons.get(response_type, "Неизвестно")

            # Calculate hours since last message
            hours_passed = hours_since(messages[-1].timestamp) if messages else 24

            # Current datetime
            current_datetime = format_datetime_for_user(get_current_time_astana())

            # Prepare prompt
            prompt = self.prompt_template.format(
                touch_number=touch_number,
                conversation_history=conversation,
                last_bot_message=last_bot_message,
                last_client_message=last_client_message,
                follow_up_reason=follow_up_reason,
                hours_since_last_message=hours_passed,
                current_datetime=current_datetime
            )

            # Generate with Gemini
            response = self.gemini_client.generate_response(
                system_prompt=prompt,
                conversation_history=[],
                temperature=0.8
            )

            if response:
                logger.success(f"Generated follow-up message for touch #{touch_number}: {response[:100]}...")
                return response
            else:
                logger.error(f"Failed to generate follow-up message")
                return None

        except Exception as e:
            logger.error(f"Error generating follow-up message: {e}")
            return None

    def send_followup(self, contact_id: int, message_text: str, db: Session) -> None:
        """Send follow-up message"""
        try:
            contact = db.query(Contact).filter(Contact.id == contact_id).first()

            if not contact:
                logger.error(f"Contact {contact_id} not found")
                return

            # Save to messages
            message = Message(
                contact_id=contact_id,
                phone_number=contact.phone_number,
                message_text=message_text,
                is_from_bot=True,
                timestamp=datetime.now()
            )
            db.add(message)
            db.commit()

            # Publish to outgoing queue
            message_data = {
                "phone_number": contact.phone_number,
                "message_text": message_text,
                "mark_as_read": False
            }
            queue_manager.publish(settings.QUEUE_OUTGOING_MESSAGES, message_data)

            logger.success(f"Sent follow-up message to {contact.phone_number}")

        except Exception as e:
            logger.error(f"Error sending follow-up: {e}")
            db.rollback()

    def process_touch(self, follow_up: FollowUp, db: Session) -> None:
        """Process a single follow-up touch"""
        try:
            # Generate message
            message = self.generate_followup_message(
                follow_up.contact_id,
                follow_up.touch_number,
                db
            )

            if not message:
                logger.error(f"Failed to generate message for touch #{follow_up.touch_number}")
                return

            # Send message
            self.send_followup(follow_up.contact_id, message, db)

            # Update follow-up record
            follow_up.last_touch_at = get_current_time_astana()

            if follow_up.touch_number < 5:
                # Schedule next touch
                follow_up.touch_number += 1
                hours_to_next = settings.FOLLOW_UP_INTERVALS[follow_up.touch_number - 1]
                follow_up.next_touch_at = get_current_time_astana() + timedelta(hours=hours_to_next)
                logger.info(f"Scheduled touch #{follow_up.touch_number} for {follow_up.next_touch_at}")
            else:
                # Completed all touches
                follow_up.is_completed = True
                follow_up.stop_reason = "completed_5_touches"
                logger.info(f"Completed all 5 touches for contact {follow_up.contact_id}")

            db.commit()

        except Exception as e:
            logger.error(f"Error processing touch: {e}")
            db.rollback()

    def stop_followup(self, contact_id: int, reason: str, db: Session) -> None:
        """Stop active follow-up for contact"""
        try:
            follow_up = db.query(FollowUp).filter(
                FollowUp.contact_id == contact_id,
                FollowUp.is_completed == False
            ).first()

            if follow_up:
                follow_up.is_completed = True
                follow_up.stop_reason = reason
                db.commit()
                logger.info(f"Stopped follow-up for contact {contact_id}, reason: {reason}")

        except Exception as e:
            logger.error(f"Error stopping follow-up: {e}")
            db.rollback()

    async def check_contacts_for_followup(self, db: Session) -> None:
        """Check all contacts that might need follow-up"""
        try:
            # Get clients without active follow-up
            contacts = db.query(Contact).filter(
                Contact.is_client == True
            ).all()

            for contact in contacts:
                if self.should_start_followup(contact, db):
                    logger.info(f"Starting follow-up for contact {contact.id}")
                    self.create_followup_chain(contact.id, db)

        except Exception as e:
            logger.error(f"Error checking contacts for follow-up: {e}")

    async def check_pending_touches(self, db: Session) -> None:
        """Check and process pending follow-up touches"""
        try:
            current_time = get_current_time_astana()

            # Get follow-ups due for next touch
            pending = db.query(FollowUp).filter(
                FollowUp.is_completed == False,
                FollowUp.next_touch_at <= current_time
            ).all()

            for follow_up in pending:
                logger.info(f"Processing touch #{follow_up.touch_number} for contact {follow_up.contact_id}")
                self.process_touch(follow_up, db)

        except Exception as e:
            logger.error(f"Error checking pending touches: {e}")

    async def start_scheduler(self) -> None:
        """Start the follow-up scheduler loop"""
        self.is_running = True
        logger.info("🚀 Started follow-up scheduler")

        while self.is_running:
            try:
                db = next(get_db())

                # Check for new follow-ups
                await self.check_contacts_for_followup(db)

                # Check pending touches
                await self.check_pending_touches(db)

                db.close()

            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")

            # Check every minute
            await asyncio.sleep(60)

    def stop_scheduler(self) -> None:
        """Stop the scheduler"""
        self.is_running = False
        logger.info("⏹️  Stopped follow-up scheduler")
