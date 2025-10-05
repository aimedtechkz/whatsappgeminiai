"""
Wappi.pro API Client Wrapper
Handles all interactions with Wappi WhatsApp API
"""
import requests
import time
from typing import Dict, Any, Optional, List
from loguru import logger
from config.settings import settings


class WappiClient:
    """
    Client for interacting with Wappi.pro WhatsApp API
    """

    def __init__(self):
        self.base_url = settings.WAPPI_BASE_URL
        self.token = settings.WAPPI_TOKEN
        self.profile_id = settings.WAPPI_PROFILE_ID
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }
        self.timeout = 30  # seconds
        self.max_retries = 3

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to Wappi API with retry logic

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint
            params: URL parameters
            data: Request body data

        Returns:
            Response JSON or None if failed
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=data,
                    timeout=self.timeout
                )

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

                # Check for server errors
                if response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code}. Retry {attempt + 1}/{self.max_retries}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue

                # Check for client errors
                if response.status_code >= 400:
                    logger.error(f"Client error {response.status_code}: {response.text}")
                    return None

                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout. Retry {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed after {self.max_retries} retries")
                    return None

            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None

        return None

    def get_chats(self, limit: int = 100, offset: int = 0, show_all: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get list of chats from WhatsApp

        Args:
            limit: Number of chats to retrieve
            offset: Offset for pagination
            show_all: Show all chats including archived

        Returns:
            API response with chats or None
        """
        endpoint = "/api/sync/chats/get"
        params = {
            "profile_id": self.profile_id,
            "limit": limit,
            "offset": offset,
            "show_all": str(show_all).lower()
        }

        logger.debug(f"Fetching chats: limit={limit}, offset={offset}")
        response = self._make_request("POST", endpoint, params=params)

        if response and response.get("status") == "done":
            logger.info(f"Retrieved {len(response.get('dialogs', []))} chats")
            return response

        return None

    def get_messages(
        self,
        chat_id: str,
        limit: int = 1,
        offset: int = 0,
        mark_all: bool = False,
        order: str = "desc"
    ) -> Optional[Dict[str, Any]]:
        """
        Get messages from specific chat

        Args:
            chat_id: Chat ID or phone number
            limit: Number of messages
            offset: Offset for pagination
            mark_all: Mark all messages as read
            order: 'desc' or 'asc'

        Returns:
            API response with messages or None
        """
        endpoint = "/api/sync/messages/get"
        params = {
            "profile_id": self.profile_id,
            "chat_id": chat_id,
            "limit": limit,
            "offset": offset,
            "mark_all": str(mark_all).lower(),
            "order": order
        }

        response = self._make_request("GET", endpoint, params=params)
        return response

    def send_message(self, recipient: str, body: str) -> Optional[Dict[str, Any]]:
        """
        Send text message to WhatsApp contact

        Args:
            recipient: Phone number
            body: Message text

        Returns:
            API response or None
        """
        if not recipient or not body:
            logger.error("Recipient and body are required")
            return None

        endpoint = "/api/sync/message/send"
        params = {"profile_id": self.profile_id}
        data = {
            "recipient": recipient,
            "body": body
        }

        logger.info(f"Sending message to {recipient}")
        response = self._make_request("POST", endpoint, params=params, data=data)

        if response and response.get("status") == "done":
            logger.success(f"Message sent successfully. Message ID: {response.get('message_id')}")
            return response

        logger.error(f"Failed to send message to {recipient}")
        return None

    def reply_to_message(self, message_id: str, body: str, url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Reply to specific message

        Args:
            message_id: ID of message to reply to
            body: Reply text
            url: Optional file URL to send

        Returns:
            API response or None
        """
        if not message_id or not body:
            logger.error("Message ID and body are required")
            return None

        endpoint = "/api/sync/message/reply"
        params = {"profile_id": self.profile_id}
        data = {
            "message_id": message_id,
            "body": body
        }

        if url:
            data["url"] = url

        logger.info(f"Replying to message {message_id}")
        response = self._make_request("POST", endpoint, params=params, data=data)

        if response and response.get("status") == "done":
            logger.success(f"Reply sent successfully. Message ID: {response.get('message_id')}")
            return response

        logger.error(f"Failed to reply to message {message_id}")
        return None

    def mark_as_read(self, message_id: str, mark_all: bool = False) -> bool:
        """
        Mark message as read

        Args:
            message_id: ID of message to mark as read
            mark_all: Mark all messages in chat as read

        Returns:
            True if successful, False otherwise
        """
        endpoint = "/api/sync/message/mark/read"
        params = {
            "profile_id": self.profile_id,
            "mark_all": str(mark_all).lower()
        }
        data = {"message_id": message_id}

        logger.debug(f"Marking message {message_id} as read")
        response = self._make_request("POST", endpoint, params=params, data=data)

        if response and response.get("status") == "done":
            logger.success(f"Message {message_id} marked as read")
            return True

        logger.error(f"Failed to mark message {message_id} as read")
        return False

    def get_message_file(self, message_id: str) -> Optional[bytes]:
        """
        Download file (voice message, image, etc.) from message

        Note: WhatsApp only stores files for the last 20 days

        Args:
            message_id: ID of message containing file

        Returns:
            File bytes or None
        """
        endpoint = "/api/sync/message/media/download"
        params = {
            "profile_id": self.profile_id,
            "message_id": message_id
        }

        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.success(f"Downloaded file for message {message_id}")
                return response.content

            logger.error(f"Failed to download file: {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return None
