"""
Message Consumer Service
Consumes incoming messages from queue and routes to appropriate handler
"""
import json
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger
import pika

from services.ai_moderator import AIModeratorService
from services.ai_sales_agent import AISalesAgentService
from services.follow_up_scheduler import FollowUpSchedulerService
from services.message_buffer import MessageBuffer
from config.queue import QueueManager
from config.settings import settings
from config.database import get_db
from models.contact import Contact
from models.message import Message


class MessageConsumerService:
    """Service to consume and process incoming messages"""

    def __init__(self):
        self.ai_moderator = AIModeratorService()
        self.ai_sales_agent = AISalesAgentService()
        self.follow_up_scheduler = FollowUpSchedulerService()
        # Create dedicated queue manager for this consumer (thread-safe)
        self.queue_manager = QueueManager()

        # Initialize message buffer with debounce
        self.message_buffer = MessageBuffer(
            timeout=settings.MESSAGE_GROUP_TIMEOUT,
            max_messages=settings.MAX_MESSAGES_IN_GROUP
        )
        # Set callback for when buffer is ready to process
        self.message_buffer.set_process_callback(self.process_buffered_messages)

    def get_or_create_contact(
        self,
        phone_number: str,
        contact_info: Dict[str, Any],
        db: Session
    ) -> Contact:
        """Get existing contact or create new one"""
        try:
            # Check if contact exists
            contact = db.query(Contact).filter(
                Contact.phone_number == phone_number
            ).first()

            if contact:
                # Update last message time
                contact.last_message_at = datetime.now()
                db.commit()
                logger.debug(f"Found existing contact: {phone_number}")
                return contact

            # Create new contact
            contact = Contact(
                phone_number=phone_number,
                name=contact_info.get("FirstName", ""),
                full_name=contact_info.get("FullName", ""),
                business_name=contact_info.get("BusinessName", ""),
                is_client=None,  # Will be classified later
                last_message_at=datetime.now()
            )
            db.add(contact)
            db.commit()
            logger.success(f"Created new contact: {phone_number}")
            return contact

        except Exception as e:
            logger.error(f"Error in get_or_create_contact: {e}")
            db.rollback()
            return None

    def save_message(
        self,
        contact_id: int,
        message_data: Dict[str, Any],
        db: Session
    ) -> Message:
        """Save incoming message to database"""
        try:
            message_id = message_data.get("message_id")

            # Check if message already exists
            existing_message = db.query(Message).filter(
                Message.message_id == message_id
            ).first()

            if existing_message:
                logger.debug(f"Message {message_id} already exists in database, skipping")
                return existing_message

            # Create new message
            message = Message(
                contact_id=contact_id,
                phone_number=message_data.get("phone_number"),
                message_id=message_id,
                message_text=message_data.get("message_text"),
                is_from_bot=False,
                is_voice=message_data.get("is_voice", False),
                voice_transcription=message_data.get("message_text") if message_data.get("is_voice") else None,
                timestamp=datetime.now()
            )
            db.add(message)
            db.commit()
            logger.success(f"Saved message for contact {contact_id}")
            return message

        except Exception as e:
            logger.error(f"Error saving message: {e}")
            db.rollback()
            return None

    def send_engagement_message(
        self,
        contact_id: int,
        last_message: str,
        db: Session
    ) -> None:
        """
        Send an engaging message to gather more information when classification is uncertain
        """
        try:
            contact = db.query(Contact).filter(Contact.id == contact_id).first()
            if not contact:
                logger.error(f"Contact {contact_id} not found")
                return

            # Get conversation history to understand context
            messages = db.query(Message).filter(
                Message.contact_id == contact_id
            ).order_by(Message.timestamp.desc()).limit(5).all()

            conversation_history = "\n".join([
                f"{'БОТ' if msg.is_from_bot else 'КЛИЕНТ'}: {msg.message_text}"
                for msg in reversed(messages)
            ])

            # Create engagement prompt
            engagement_prompt = f"""
Ты - дружелюбный AI-ассистент компании.

Клиент написал: "{last_message}"

Но из этого сообщения непонятно, чем именно мы можем помочь.

Твоя задача: Написать КОРОТКОЕ (1-2 предложения), дружелюбное сообщение, чтобы:
1. Поприветствовать клиента
2. Вежливо узнать, чем конкретно вы можете помочь
3. Побудить его рассказать о своих потребностях

История переписки:
{conversation_history}

ВАЖНО:
- Пиши по-русски
- Будь вежливым и дружелюбным
- НЕ используй эмодзи
- Напиши ТОЛЬКО текст сообщения, без пояснений
"""

            # Generate engagement response using Gemini
            import google.generativeai as genai
            from config.settings import settings

            genai.configure(api_key=settings.GEMINI_API_KEY)

            try:
                # Create model without system instruction (not supported in older version)
                model = genai.GenerativeModel(
                    model_name=settings.GEMINI_MODEL,
                    generation_config=genai.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=512,
                    )
                )

                response = model.generate_content(engagement_prompt)
                response_text = response.text.strip()
                logger.debug(f"Gemini engagement response: {response_text}")
            except Exception as e:
                logger.error(f"Gemini error generating engagement: {e}")
                response_text = None

            if not response_text:
                # Fallback message if AI fails
                response_text = "Здравствуйте! Подскажите, пожалуйста, чем мы можем вам помочь?"

            # Save bot message
            bot_message = Message(
                contact_id=contact_id,
                phone_number=contact.phone_number,
                message_text=response_text,
                is_from_bot=True,
                timestamp=datetime.now()
            )
            db.add(bot_message)
            db.commit()

            # Publish to outgoing queue
            outgoing_data = {
                "phone_number": contact.phone_number,
                "message_text": response_text,
                "contact_id": contact_id
            }

            self.queue_manager.publish(
                settings.QUEUE_OUTGOING_MESSAGES,
                outgoing_data
            )

            logger.success(f"✅ Sent engagement message to {contact.phone_number}")

        except Exception as e:
            logger.error(f"Error sending engagement message: {e}")
            db.rollback()

    def process_buffered_messages(self, phone_number: str) -> None:
        """
        Process all buffered messages for a contact
        Called by MessageBuffer when timer expires or buffer is full

        Args:
            phone_number: Contact phone number
        """
        db = next(get_db())

        try:
            # Get all buffered messages
            buffered_messages = self.message_buffer.get_messages(phone_number)

            if not buffered_messages:
                logger.warning(f"No buffered messages found for {phone_number}")
                return

            logger.info(
                f"🔄 Processing {len(buffered_messages)} buffered messages for {phone_number}"
            )

            # Get contact info from first message
            first_message_data = buffered_messages[0]
            contact_info = first_message_data.get("contact_info", {})

            # Get or create contact
            contact = self.get_or_create_contact(phone_number, contact_info, db)

            if not contact:
                logger.error(f"Failed to get/create contact for {phone_number}")
                self.message_buffer.clear_buffer(phone_number)
                return

            # Save all messages to database
            saved_messages = []
            for message_data in buffered_messages:
                message = self.save_message(contact.id, message_data, db)
                if message:
                    saved_messages.append(message)

            if not saved_messages:
                logger.error(f"Failed to save any messages for contact {contact.id}")
                self.message_buffer.clear_buffer(phone_number)
                return

            logger.success(f"💾 Saved {len(saved_messages)} messages for {phone_number}")

            # Combine message texts
            combined_text = "\n".join([
                msg.message_text for msg in saved_messages
            ])

            # Create a synthetic "combined" message object for routing
            # Use the last message as base, but with combined text
            combined_message = saved_messages[-1]
            combined_message.message_text = combined_text

            logger.debug(f"Combined message text ({len(combined_text)} chars): {combined_text[:200]}...")

            # Route to handler with combined message
            self.route_to_handler(contact, combined_message, db)

            # Clear buffer after successful processing
            cleared = self.message_buffer.clear_buffer(phone_number)
            logger.success(f"✅ Processed {len(saved_messages)} messages for {phone_number}, cleared {cleared} from buffer")

        except Exception as e:
            logger.error(f"Error processing buffered messages for {phone_number}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Clear buffer even on error to prevent stuck messages
            self.message_buffer.clear_buffer(phone_number)

        finally:
            db.close()

    def route_to_handler(
        self,
        contact: Contact,
        message: Message,
        db: Session
    ) -> None:
        """Route message to appropriate handler based on contact classification"""
        try:
            # Check if follow-up is active and stop it if client responded
            from models.follow_up import FollowUp
            active_followup = db.query(FollowUp).filter(
                FollowUp.contact_id == contact.id,
                FollowUp.is_completed == False
            ).first()

            if active_followup:
                # Client responded, stop follow-up
                logger.info(f"Client responded, stopping follow-up for contact {contact.id}")
                self.follow_up_scheduler.stop_followup(
                    contact.id,
                    "client_responded",
                    db
                )

            # Route based on classification
            if contact.is_client is None:
                # Not classified yet
                logger.info(f"Contact {contact.id} not classified, sending to moderator")

                # Classify if enough messages
                messages_count = db.query(Message).filter(
                    Message.contact_id == contact.id
                ).count()

                if messages_count >= 1:
                    is_client = self.ai_moderator.classify_contact(contact.id, db)

                    # Refresh contact
                    db.refresh(contact)

                    if is_client:
                        # Now classified as client, generate response
                        logger.info(f"Contact {contact.id} classified as CLIENT, generating response")
                        self.ai_sales_agent.generate_response(
                            contact.id,
                            message.message_text,
                            db
                        )
                    elif is_client is False:
                        logger.info(f"Contact {contact.id} classified as NOT CLIENT, ignoring")
                    else:
                        # Classification uncertain - proactively engage to gather more information
                        logger.info(f"Contact {contact.id} classification uncertain, sending engagement message")
                        self.send_engagement_message(contact.id, message.message_text, db)
                else:
                    logger.info(f"Not enough messages ({messages_count}/1) to classify contact {contact.id}")

            elif contact.is_client is False:
                # Not a client, ignore
                logger.info(f"Contact {contact.id} is NOT a client, ignoring message")

            elif contact.is_client is True:
                # Is a client, generate response
                logger.info(f"Contact {contact.id} is a CLIENT, generating sales response")
                self.ai_sales_agent.generate_response(
                    contact.id,
                    message.message_text,
                    db
                )

        except Exception as e:
            logger.error(f"Error routing message: {e}")

    def process_incoming_message(
        self,
        ch: pika.channel.Channel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes
    ) -> None:
        """
        Receive incoming message from queue and add to buffer
        Messages are grouped and processed after debounce timeout
        """
        try:
            # Parse message
            message_data = json.loads(body.decode())
            phone_number = message_data.get("phone_number")

            if not phone_number:
                logger.error("Missing phone_number in message")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            logger.info(f"📥 Received message from {phone_number}, adding to buffer")

            # Add to buffer (will trigger processing after timeout or when buffer is full)
            self.message_buffer.add_message(phone_number, message_data)

            # Acknowledge immediately - don't block queue
            ch.basic_ack(delivery_tag=method.delivery_tag)

            # Log buffer stats
            buffer_size = self.message_buffer.get_buffer_size(phone_number)
            logger.debug(f"Buffer size for {phone_number}: {buffer_size}")

        except Exception as e:
            logger.error(f"Error receiving incoming message: {e}")
            # Acknowledge to remove from queue even on error
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def start_consuming(self) -> None:
        """Start consuming messages from incoming queue"""
        logger.info(f"🚀 Started message consumer, consuming from {settings.QUEUE_INCOMING_MESSAGES}")

        self.queue_manager.consume(
            queue_name=settings.QUEUE_INCOMING_MESSAGES,
            callback=self.process_incoming_message,
            prefetch_count=1
        )
