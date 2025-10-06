"""
Voice Transcription Service
Transcribes voice messages using OpenAI Whisper API with OGG to MP3 conversion
"""
import json
from datetime import datetime
from typing import Dict, Any
from loguru import logger
import pika
import google.generativeai as genai
from openai import OpenAI
from pydub import AudioSegment
import tempfile
import os

from services.wappi_client import WappiClient
from config.queue import QueueManager
from config.settings import settings
from config.database import get_db
from models.message_log import MessageLog


class VoiceTranscriptionService:
    """Service to transcribe voice messages using OpenAI Whisper API or Google Gemini API (fallback)"""

    def __init__(self):
        self.wappi_client = WappiClient()
        self.queue_manager = QueueManager()  # Dedicated instance for this consumer

        # Initialize OpenAI Whisper API (Primary - with OGG to MP3 conversion)
        logger.info("Initializing OpenAI Whisper API for voice transcription...")
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.use_openai = True
        logger.success("OpenAI Whisper API initialized successfully")

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

    def transcribe_with_openai(self, audio_bytes: bytes) -> str:
        """Transcribe audio using OpenAI Whisper API with OGG to MP3 conversion"""
        ogg_file_path = None
        mp3_file_path = None
        try:
            # Save OGG audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as ogg_file:
                ogg_file.write(audio_bytes)
                ogg_file_path = ogg_file.name

            logger.debug(f"Saved OGG audio to temp file: {ogg_file_path}")

            # Convert OGG Opus to MP3 using pydub
            audio = AudioSegment.from_file(ogg_file_path, format="ogg")
            mp3_file_path = ogg_file_path.replace('.ogg', '.mp3')
            audio.export(mp3_file_path, format="mp3", bitrate="64k")

            logger.debug(f"Converted OGG to MP3: {mp3_file_path}")

            # Transcribe with OpenAI Whisper
            with open(mp3_file_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ru"  # Russian/Kazakh transcription
                )

            transcription = transcript.text.strip()

            if transcription:
                logger.success(f"OpenAI Whisper transcribed: {transcription[:100]}...")
                return transcription
            else:
                logger.warning("OpenAI Whisper returned empty transcription")
                return None

        except Exception as e:
            logger.error(f"OpenAI Whisper transcription error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

        finally:
            # Clean up temp files
            if ogg_file_path and os.path.exists(ogg_file_path):
                try:
                    os.unlink(ogg_file_path)
                    logger.debug(f"Cleaned up OGG temp file: {ogg_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete OGG temp file: {e}")

            if mp3_file_path and os.path.exists(mp3_file_path):
                try:
                    os.unlink(mp3_file_path)
                    logger.debug(f"Cleaned up MP3 temp file: {mp3_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete MP3 temp file: {e}")

    def transcribe_with_gemini(self, audio_bytes: bytes) -> str:
        """Transcribe audio using Google Gemini API"""
        temp_file = None
        temp_file_path = None
        try:
            # Save audio to temporary file (Gemini needs file path)
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name

            logger.debug(f"Saved audio to temp file: {temp_file_path}")

            # Upload file to Gemini with explicit MIME type
            # WhatsApp voice messages are typically Opus codec in OGG container
            audio_file = genai.upload_file(
                path=temp_file_path,
                mime_type="audio/ogg"  # Explicitly set MIME type for OGG audio
            )
            logger.debug(f"Uploaded audio file to Gemini: {audio_file.name}")

            # Generate transcription
            prompt = "Транскрибируй это голосовое сообщение на русском или казахском языке. Верни только текст транскрипции, без комментариев и пояснений."

            response = self.model.generate_content([prompt, audio_file])
            transcription = response.text.strip()

            # Delete uploaded file from Gemini to save quota
            try:
                genai.delete_file(audio_file.name)
                logger.debug(f"Deleted uploaded file from Gemini: {audio_file.name}")
            except Exception as e:
                logger.warning(f"Failed to delete file from Gemini: {e}")

            if transcription:
                logger.success(f"Gemini transcribed: {transcription[:100]}...")
                return transcription
            else:
                logger.warning("Gemini returned empty transcription")
                return None

        except Exception as e:
            logger.error(f"Gemini transcription error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

        finally:
            # Clean up temp file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temp file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")

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

            # Transcribe using OpenAI Whisper (primary) or Gemini (fallback)
            if self.use_openai:
                logger.info("Using OpenAI Whisper for transcription")
                transcription = self.transcribe_with_openai(audio_bytes)
            else:
                logger.info("Using Gemini for transcription")
                transcription = self.transcribe_with_gemini(audio_bytes)

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
