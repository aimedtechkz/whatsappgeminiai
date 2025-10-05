"""
Voice Transcription Service
Transcribes voice messages using local Faster-Whisper
"""
import json
import io
from datetime import datetime
from typing import Dict, Any
from loguru import logger
import pika

from services.wappi_client import WappiClient
from config.queue import QueueManager
from config.settings import settings
from config.database import get_db
from models.message_log import MessageLog

# Import Faster-Whisper for local transcription
from faster_whisper import WhisperModel


class VoiceTranscriptionService:
    """Service to transcribe voice messages using local Faster-Whisper"""

    def __init__(self):
        self.wappi_client = WappiClient()
        self.queue_manager = QueueManager()  # Dedicated instance for this consumer

        # Initialize Whisper model (downloads on first run ~150MB)
        logger.info("Loading Whisper model...")
        self.whisper_model = WhisperModel(
            "base",  # Options: tiny, base, small, medium, large-v2
            device="cpu",
            compute_type="int8"  # Optimized for CPU
        )
        logger.success("Whisper model loaded successfully")

    def download_audio(self, message_id: str) -> bytes:
        """Download audio file from Wappi API"""
        try:
            audio_bytes = self.wappi_client.get_message_file(message_id)
            if audio_bytes:
                logger.success(f"Downloaded audio for message {message_id}")
                return audio_bytes
            else:
                logger.error(f"Failed to download audio for message {message_id}")
                return None
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            return None

    def transcribe_with_whisper(self, audio_bytes: bytes) -> str:
        """Transcribe audio using local Faster-Whisper"""
        try:
            # Convert bytes to BytesIO for Whisper
            audio_buffer = io.BytesIO(audio_bytes)

            # Transcribe with Whisper
            segments, info = self.whisper_model.transcribe(
                audio_buffer,
                language="ru",  # Force Russian language
                beam_size=5,
                vad_filter=True  # Voice Activity Detection - filters silence
            )

            # Combine all segments into full transcription
            transcription = " ".join([segment.text for segment in segments]).strip()

            if transcription:
                logger.success(f"Transcribed: {transcription[:100]}...")
                return transcription
            else:
                logger.warning("Whisper returned empty transcription")
                return None

        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def publish_transcription(
        self,
        original_data: Dict[str, Any],
        transcription: str
    ) -> None:
        """Publish transcribed message to incoming queue"""
        try:
            # Create new message data with transcription
            message_data = {
                **original_data,
                "message_text": f"[ТРАНСКРИБАЦИЯ] {transcription}",
                "is_voice": True,
                "original_voice_url": original_data.get("voice_url", "")
            }

            # Publish to incoming messages queue
            queue_manager.publish(
                settings.QUEUE_INCOMING_MESSAGES,
                message_data
            )

            logger.success(f"Published transcription to incoming queue")

        except Exception as e:
            logger.error(f"Error publishing transcription: {e}")

    def process_voice_message(
        self,
        ch: pika.channel.Channel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes
    ) -> None:
        """Process voice message from queue"""
        db = next(get_db())

        try:
            # Parse message
            message_data = json.loads(body.decode())
            logger.info(f"🎤 Processing voice message: {message_data.get('message_id')}")

            message_id = message_data.get("message_id")

            if not message_id:
                logger.error("Missing message_id")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Download audio
            audio_bytes = self.download_audio(message_id)

            if not audio_bytes:
                logger.warning(f"Could not download audio for {message_id}, forwarding as text")
                # Forward to AI agent as text message with [Voice message] placeholder
                message_data_copy = message_data.copy()
                message_data_copy['message_text'] = '[Голосовое сообщение - не удалось загрузить]'
                message_data_copy['is_voice'] = False  # Treat as text since we can't transcribe

                from config.queue import queue_manager
                queue_manager.publish(settings.QUEUE_INCOMING_MESSAGES, message_data_copy)
                logger.info(f"📢 Forwarded failed voice message as text to AI agent")

                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Transcribe
            transcription = self.transcribe_with_whisper(audio_bytes)

            if transcription:
                # Update message log
                try:
                    message_log = db.query(MessageLog).filter(
                        MessageLog.message_id == message_id
                    ).first()

                    if message_log:
                        message_log.message_text = f"[ТРАНСКРИБАЦИЯ] {transcription}"
                        message_log.processed_at = datetime.now()
                        db.commit()
                except Exception as e:
                    logger.error(f"Failed to update message log: {e}")
                    db.rollback()

                # Publish to incoming queue
                self.publish_transcription(message_data, transcription)

                # Acknowledge
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.success(f"✅ Transcribed voice message {message_id}")
            else:
                # Failed to transcribe, retry
                retry_count = properties.headers.get("x-retry-count", 0) if properties.headers else 0

                if retry_count < 2:
                    logger.warning(f"Retrying transcription (attempt {retry_count + 1}/2)")

                    headers = properties.headers or {}
                    headers["x-retry-count"] = retry_count + 1

                    ch.basic_publish(
                        exchange='',
                        routing_key=settings.QUEUE_VOICE_TRANSCRIPTION,
                        body=body,
                        properties=pika.BasicProperties(headers=headers)
                    )
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    logger.error(f"❌ Failed to transcribe after 2 retries: {message_id}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        finally:
            db.close()

    def start_consuming(self) -> None:
        """Start consuming voice messages from queue"""
        logger.info(f"🚀 Started voice transcription service, consuming from {settings.QUEUE_VOICE_TRANSCRIPTION}")

        self.queue_manager.consume(
            queue_name=settings.QUEUE_VOICE_TRANSCRIPTION,
            callback=self.process_voice_message,
            prefetch_count=1
        )
