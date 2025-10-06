"""
Message Sender Service
Consumes messages from outgoing queue and sends via Wappi API
"""
import json
import time
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from loguru import logger
import pika

from services.wappi_client import WappiClient
from config.queue import QueueManager
from config.database import get_db
from config.settings import settings
from models.message_log import MessageLog


class MessageSenderService:
    """Service to send WhatsApp messages via Wappi API"""

    def __init__(self):
        self.wappi_client = WappiClient()
        self.queue_manager = QueueManager()  # Dedicated instance for this consumer
        self.max_messages_per_minute = 20
        self.message_count = 0
        self.minute_start = time.time()

    def throttle_if_needed(self) -> None:
        """Implement rate limiting (20 messages per minute)"""
        current_time = time.time()
        elapsed = current_time - self.minute_start

        # Reset counter every minute
        if elapsed >= 60:
            self.message_count = 0
            self.minute_start = current_time
            return

        # Check if limit reached
        if self.message_count >= self.max_messages_per_minute:
            wait_time = 60 - elapsed
            logger.warning(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
            self.message_count = 0
            self.minute_start = time.time()

    def send_via_wappi(
        self,
        phone_number: str,
        message_text: str,
        reply_to_id: str = None
    ) -> bool:
        """
        Send message via Wappi API

        Args:
            phone_number: Recipient phone number
            message_text: Message text
            reply_to_id: Optional message ID to reply to

        Returns:
            bool: True if successful
        """
        try:
            # Throttle if needed
            self.throttle_if_needed()

            # Send message
            if reply_to_id:
                response = self.wappi_client.reply_to_message(reply_to_id, message_text)
            else:
                response = self.wappi_client.send_message(phone_number, message_text)

            if response and response.get("status") == "done":
                self.message_count += 1
                logger.success(f"✅ Sent message to {phone_number}")
                return True

            logger.error(f"❌ Failed to send message to {phone_number}")
            return False

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    def mark_message_as_sent(self, message_id: str, db: Session, status: str = "sent") -> None:
        """Update message status in database"""
        try:
            msg_id = message_id or f"outgoing_{int(datetime.now().timestamp())}"

            # Check if message already exists
            existing_message = db.query(MessageLog).filter(
                MessageLog.message_id == msg_id
            ).first()

            if existing_message:
                # Update existing message
                existing_message.queue_status = status
                existing_message.wappi_status = status
                existing_message.processed_at = datetime.now()
                db.commit()
                logger.debug(f"Updated existing message {msg_id} status to {status}")
            else:
                # Create new message log
                message_log = MessageLog(
                    message_id=msg_id,
                    phone_number="unknown",
                    direction="outgoing",
                    message_text="",
                    queue_status=status,
                    wappi_status=status,
                    processed_at=datetime.now()
                )
                db.add(message_log)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update message status: {e}")
            db.rollback()

    def process_outgoing_message(
        self,
        ch: pika.channel.Channel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes
    ) -> None:
        """Process message from outgoing queue"""
        db = next(get_db())

        try:
            # Parse message
            message_data = json.loads(body.decode())
            logger.info(f"📤 Processing outgoing message: {message_data}")

            phone_number = message_data.get("phone_number")
            message_text = message_data.get("message_text")
            reply_to_id = message_data.get("reply_to_message_id")
            mark_as_read = message_data.get("mark_as_read", False)

            if not phone_number or not message_text:
                logger.error("Missing phone_number or message_text")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Send message
            success = self.send_via_wappi(phone_number, message_text, reply_to_id)

            if success:
                # Mark as read if requested
                if mark_as_read and reply_to_id:
                    self.wappi_client.mark_as_read(reply_to_id)

                # Update database
                self.mark_message_as_sent(reply_to_id, db, "sent")

                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.success(f"✅ Message sent successfully to {phone_number}")
            else:
                # Retry logic: reject and requeue (will retry up to 3 times)
                retry_count = properties.headers.get("x-retry-count", 0) if properties.headers else 0

                if retry_count < 3:
                    logger.warning(f"Retrying message (attempt {retry_count + 1}/3)")

                    # Update retry count
                    headers = properties.headers or {}
                    headers["x-retry-count"] = retry_count + 1

                    # Requeue with updated headers
                    ch.basic_publish(
                        exchange='',
                        routing_key=settings.QUEUE_OUTGOING_MESSAGES,
                        body=body,
                        properties=pika.BasicProperties(headers=headers)
                    )
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    # Max retries reached, log as failed
                    logger.error(f"❌ Failed to send after 3 retries: {phone_number}")
                    self.mark_message_as_sent(reply_to_id, db, "failed")
                    ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"Error processing outgoing message: {e}")
            # Acknowledge to remove from queue
            ch.basic_ack(delivery_tag=method.delivery_tag)

        finally:
            db.close()

    def start_consuming(self) -> None:
        """Start consuming messages from outgoing queue"""
        logger.info(f"🚀 Started sender service, consuming from {settings.QUEUE_OUTGOING_MESSAGES}")

        self.queue_manager.consume(
            queue_name=settings.QUEUE_OUTGOING_MESSAGES,
            callback=self.process_outgoing_message,
            prefetch_count=1
        )
