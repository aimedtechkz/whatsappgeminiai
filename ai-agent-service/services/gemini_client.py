"""
Google Gemini API Client Wrapper
Handles all interactions with Gemini 2.5 Pro API
"""
import google.generativeai as genai
import json
import time
from typing import List, Dict, Any, Optional
from loguru import logger
from config.settings import settings


class GeminiClient:
    """
    Client for interacting with Google Gemini 2.5 Pro API
    """

    def __init__(self):
        """Initialize Gemini client with API key"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL
        self.max_retries = 3

    def generate_response(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate AI response based on system prompt and conversation history

        Args:
            system_prompt: System instruction for the AI
            conversation_history: List of messages in format [{"role": "user/model", "parts": [{"text": "..."}]}]
            temperature: Creativity level (0.0 - 1.0)

        Returns:
            Generated text response or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                # Create model (system_instruction not supported in older version)
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=genai.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=2048,
                    )
                )

                # Prepend system prompt to conversation history
                full_history = [
                    {"role": "user", "parts": [{"text": system_prompt}]},
                    {"role": "model", "parts": [{"text": "Понял, буду следовать инструкциям."}]}
                ]
                full_history.extend(conversation_history)

                # Create chat session with history
                chat = model.start_chat(history=full_history)

                # Generate response
                response = chat.send_message("")  # Empty message since we have history

                text = response.text
                logger.success(f"Generated response ({len(text)} chars)")

                # Log token usage if available
                if hasattr(response, 'usage_metadata'):
                    logger.debug(f"Tokens used: {response.usage_metadata}")

                return text

            except Exception as e:
                error_msg = str(e)

                # Handle rate limiting
                if "429" in error_msg or "quota" in error_msg.lower():
                    wait_time = 5 * (attempt + 1)
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue

                # Handle other errors
                logger.error(f"Gemini API error (attempt {attempt + 1}/{self.max_retries}): {error_msg}")

                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None

        return None

    def classify_json(
        self,
        prompt: str,
        temperature: float = 0.1
    ) -> Optional[Dict[str, Any]]:
        """
        Generate structured JSON response for classification tasks

        Args:
            prompt: Classification prompt
            temperature: Low temperature for consistent results

        Returns:
            Parsed JSON dict or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=genai.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=1024,
                    )
                )

                response = model.generate_content(prompt)
                text = response.text

                logger.debug(f"Raw Gemini response: {text[:500]}")

                # Strip markdown code blocks if present
                import re
                text = text.strip()
                if text.startswith('```'):
                    # Remove markdown code blocks
                    text = re.sub(r'^```(?:json)?\s*\n', '', text)
                    text = re.sub(r'\n```\s*$', '', text)
                    text = text.strip()

                # Parse JSON - try to extract JSON from text if needed
                try:
                    result = json.loads(text)
                except json.JSONDecodeError:
                    # Try to find JSON in the text
                    json_match = re.search(r'\{[^{}]*"isClient"[^{}]*\}', text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group(0))
                    else:
                        raise

                logger.success(f"Classification result: {result}")

                return result

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {text}")

                if attempt < self.max_retries - 1:
                    continue
                else:
                    return None

            except Exception as e:
                error_msg = str(e)

                # Handle rate limiting
                if "429" in error_msg or "quota" in error_msg.lower():
                    wait_time = 5 * (attempt + 1)
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue

                logger.error(f"Gemini API error (attempt {attempt + 1}/{self.max_retries}): {error_msg}")

                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None

        return None

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> Optional[str]:
        """
        Transcribe audio file to text using Gemini

        Args:
            audio_bytes: Audio file bytes
            mime_type: MIME type of audio file

        Returns:
            Transcribed text or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                model = genai.GenerativeModel(model_name=self.model_name)

                # Upload audio file
                audio_file = genai.upload_file(
                    audio_bytes,
                    mime_type=mime_type
                )

                # Generate transcription
                prompt = "Транскрибируй это голосовое сообщение на русском языке. Верни только текст транскрипции, без комментариев."

                response = model.generate_content([prompt, audio_file])
                transcription = response.text.strip()

                logger.success(f"Transcribed audio: {transcription[:100]}...")
                return transcription

            except Exception as e:
                error_msg = str(e)

                # Handle rate limiting
                if "429" in error_msg or "quota" in error_msg.lower():
                    wait_time = 5 * (attempt + 1)
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue

                logger.error(f"Audio transcription error (attempt {attempt + 1}/{self.max_retries}): {error_msg}")

                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None

        return None
