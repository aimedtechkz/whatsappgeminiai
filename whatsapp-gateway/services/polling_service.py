"""
Message Polling Service
Polls Wappi API every 5 seconds for new messages
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from loguru import logger

from services.wappi_client import WappiClient
from config.queue import queue_manager
from config.database import get_db
from config.settings import settings
from models.message_log import MessageLog
from models.whitelist import Whitelist


class MessagePollingService:
    """Service to poll WhatsApp messages from Wappi API"""

    def __init__(self):
        self.wappi_client = WappiClient()
        self.polling_interval = settings.POLLING_INTERVAL
        self.is_running = False

    def is_in_whitelist(self, phone_number: str, db: Session) -> bool:
        """Check if phone number is in whitelist"""
        # Remove @c.us suffix if present
        clean_phone = phone_number.replace("@c.us", "")

        whitelist_entry = db.query(Whitelist).filter(
            Whitelist.phone_number == clean_phone
        ).first()

        return whitelist_entry is not None

    def is_message_processed(self, message_id: str, db: Session) -> bool:
        """Check if message was already processed"""
        existing = db.query(MessageLog).filter(
            MessageLog.message_id == message_id
        ).first()

        return existing is not None

    def extract_phone_from_chat_id(self, chat_id: str) -> str:
        """Extract phone number from chat_id"""
        # Remove @c.us or @g.us suffix
        return chat_id.replace("@c.us", "").replace("@g.us", "")

    def process_chats(self, db: Session) -> None:
        """Get all chats and check for new messages"""
        try:
            # Get recent chats from Wappi (limit to 20 to avoid too many API calls)
            response = self.wappi_client.get_chats(limit=20, offset=0, show_all=True)

            if not response or response.get("status") != "done":
                logger.warning("Failed to get chats from Wappi")
                return

            dialogs = response.get("dialogs", [])
            logger.info(f"Retrieved {len(dialogs)} chats from API, will process first 20")

            # Limit to 20 chats to avoid API overload (Wappi API ignores limit parameter with show_all=True)
            dialogs_to_process = dialogs[:20] if len(dialogs) > 20 else dialogs

            processed = 0
            for dialog in dialogs_to_process:
                try:
                    # Skip None dialogs
                    if not dialog:
                        logger.debug("Skipping None dialog")
                        continue

                    if self.process_dialog_with_messages(dialog, db):
                        processed += 1
                except Exception as e:
                    logger.error(f"Error processing dialog: {e}")
                    logger.debug(f"Dialog data: {dialog}")
                    continue

            if processed > 0:
                logger.success(f"✅ Processed {processed} chats with new messages")

        except Exception as e:
            logger.error(f"Error in process_chats: {e}")

    def process_dialog_with_messages(self, dialog: Dict[str, Any], db: Session) -> bool:
        """
        Process a single dialog by fetching its latest messages
        Returns True if a new message was processed
        """
        # Validate dialog
        if not dialog or not isinstance(dialog, dict):
            logger.debug("Dialog is None or not a dict")
            return False

        chat_id = dialog.get("id")
        if not chat_id:
            logger.debug("Chat ID is None")
            return False

        phone_number = self.extract_phone_from_chat_id(chat_id)

        # Check whitelist
        if self.is_in_whitelist(phone_number, db):
            return False

        # Get contact info - handle None safely
        contact_info = dialog.get("contact") if dialog else None
        if not contact_info or not isinstance(contact_info, dict):
            contact_info = {}

        # Get latest messages from this chat using /messages/get endpoint
        # Get up to 20 recent messages to catch rapid sequential messages
        messages_response = self.wappi_client.get_messages(
            chat_id=chat_id,
            limit=20,  # Get last 20 messages to catch rapid sequences
            order="desc"  # From newest to oldest
        )

        if not messages_response or messages_response.get("status") != "done":
            return False

        messages = messages_response.get("messages", [])
        if not messages:
            return False

        # Process all unread messages (not already in DB and not from me)
        new_messages = []
        for msg in reversed(messages):  # Process oldest to newest
            if msg is None:
                continue

            msg_id = msg.get("id")
            from_me = msg.get("fromMe", False)

            # Skip if already processed or from bot
            if from_me or self.is_message_processed(msg_id, db):
                continue

            new_messages.append(msg)

        # If no new messages, return
        if not new_messages:
            return False

        logger.info(f"📬 Found {len(new_messages)} new messages from {phone_number}")

        # Process each new message
        processed_count = 0
        for message in new_messages:
            message_id = message.get("id")
            message_text = message.get("body", "")
            message_type = message.get("type", "chat")
            timestamp = message.get("time", int(datetime.now().timestamp()))

            # Handle media messages (body can be dict instead of string)
            if isinstance(message_text, dict):
                # For media messages, extract meaningful text description
                if "title" in message_text:
                    # PDF or document with title
                    message_text = f"[{message_text.get('mimetype', 'document')}] {message_text.get('title', 'untitled')}"
                elif "PTT" in message_text or message_type in ["ptt", "audio"]:
                    # Voice message
                    message_text = "[Voice message]"
                elif "vcard" in message_text:
                    # Contact card
                    message_text = f"[Contact] {message_text.get('display_name', 'unknown')}"
                elif "buttonText" in message_text:
                    # Interactive message
                    message_text = f"[Interactive] {message_text.get('buttonText', 'button message')}"
                elif "URL" in message_text or "url" in message_text:
                    # Image, video or other media with URL
                    mimetype = message_text.get("mimetype", "media")
                    message_text = f"[{mimetype}]"
                else:
                    # Generic media message - convert to JSON string
                    message_text = f"[Media: {message_type}]"

            # Check if voice message
            is_voice = message_type in ["ptt", "audio"]

            # Create message data
            message_data = {
                "message_id": message_id,
                "chat_id": chat_id,
                "phone_number": phone_number,
                "sender_name": contact_info.get("FirstName", ""),
                "message_text": message_text,
                "is_voice": is_voice,
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "contact_info": {
                    "FirstName": contact_info.get("FirstName", ""),
                    "FullName": contact_info.get("FullName", ""),
                    "PushName": contact_info.get("PushName", ""),
                    "BusinessName": contact_info.get("BusinessName", "")
                }
            }

            # Save to database
            try:
                # Check if message already exists
                existing_message = db.query(MessageLog).filter(
                    MessageLog.message_id == message_id
                ).first()

                if existing_message:
                    logger.debug(f"Message {message_id} already exists in database, skipping save")
                else:
                    message_log = MessageLog(
                        message_id=message_id,
                        phone_number=phone_number,
                        direction="incoming",
                        message_text=message_text,
                        is_voice=is_voice,
                        queue_status="queued",
                        wappi_status="received"
                    )
                    db.add(message_log)
                    db.commit()
                    logger.success(f"💾 Saved message from {phone_number}: {message_text[:50]}")
            except Exception as e:
                logger.error(f"Failed to save message to database: {e}")
                db.rollback()
                continue

            # Route to appropriate queue
            if is_voice:
                # Publish to voice transcription queue
                queue_manager.publish(
                    settings.QUEUE_VOICE_TRANSCRIPTION,
                    message_data
                )
                logger.info(f"📢 Published voice message to transcription queue")
            else:
                # Publish to incoming messages queue
                queue_manager.publish(
                    settings.QUEUE_INCOMING_MESSAGES,
                    message_data
                )
                logger.info(f"📢 Published text message to AI queue")

            processed_count += 1

        logger.success(f"✅ Processed {processed_count}/{len(new_messages)} messages from {phone_number}")
        return processed_count > 0

    async def start_polling(self) -> None:
        """Start continuous polling loop"""
        self.is_running = True
        logger.info(f"🚀 Started polling service (interval: {self.polling_interval}s)")

        while self.is_running:
            try:
                db = next(get_db())
                self.process_chats(db)
                db.close()
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")

            # Wait for next poll
            await asyncio.sleep(self.polling_interval)

    def stop_polling(self) -> None:
        """Stop polling service"""
        self.is_running = False
        logger.info("⏹️  Stopped polling service")
