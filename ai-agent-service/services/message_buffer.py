"""
Message Buffer Service
Buffers incoming messages to group rapid sequential messages from same contact
"""
import threading
import time
from typing import Dict, List, Callable, Any
from collections import defaultdict
from loguru import logger


class MessageBuffer:
    """
    Thread-safe message buffer with debounce mechanism
    Groups rapid messages from same contact before processing
    """

    def __init__(self, timeout: float = 4.0, max_messages: int = 10):
        """
        Initialize message buffer

        Args:
            timeout: Seconds to wait after last message before processing
            max_messages: Maximum messages to buffer before forced processing
        """
        self.timeout = timeout
        self.max_messages = max_messages

        # Thread-safe storage
        self._buffers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._timers: Dict[str, threading.Timer] = {}
        self._locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._global_lock = threading.Lock()

        # Callback for processing
        self._process_callback: Callable = None

        logger.info(f"📦 MessageBuffer initialized (timeout={timeout}s, max={max_messages})")

    def set_process_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set callback function to be called when buffer is ready to process

        Args:
            callback: Function that takes phone_number as argument
        """
        self._process_callback = callback
        logger.debug("Process callback registered")

    def add_message(self, phone_number: str, message_data: Dict[str, Any]) -> None:
        """
        Add message to buffer and manage timer

        Args:
            phone_number: Contact phone number
            message_data: Message data dictionary
        """
        with self._locks[phone_number]:
            # Add message to buffer
            self._buffers[phone_number].append(message_data)
            buffer_size = len(self._buffers[phone_number])

            logger.debug(
                f"📨 Buffered message from {phone_number} "
                f"(buffer size: {buffer_size}/{self.max_messages})"
            )

            # Cancel existing timer if present
            if phone_number in self._timers:
                self._timers[phone_number].cancel()
                logger.debug(f"⏱️  Timer reset for {phone_number}")

            # Check if buffer is full
            if buffer_size >= self.max_messages:
                logger.warning(
                    f"📦 Buffer full for {phone_number} "
                    f"({buffer_size} messages), forcing immediate processing"
                )
                self._trigger_processing(phone_number)
                return

            # Start new timer
            timer = threading.Timer(
                self.timeout,
                self._on_timer_expired,
                args=[phone_number]
            )
            timer.daemon = True
            timer.start()

            with self._global_lock:
                self._timers[phone_number] = timer

            logger.debug(
                f"⏱️  Timer started for {phone_number} "
                f"({self.timeout}s, {buffer_size} messages buffered)"
            )

    def _on_timer_expired(self, phone_number: str) -> None:
        """
        Called when timer expires - triggers processing

        Args:
            phone_number: Contact phone number
        """
        logger.info(
            f"⏰ Timer expired for {phone_number}, "
            f"triggering processing of buffered messages"
        )
        self._trigger_processing(phone_number)

    def _trigger_processing(self, phone_number: str) -> None:
        """
        Trigger processing callback for buffered messages

        Args:
            phone_number: Contact phone number
        """
        if self._process_callback:
            try:
                self._process_callback(phone_number)
            except Exception as e:
                logger.error(
                    f"❌ Error in process callback for {phone_number}: {e}"
                )
        else:
            logger.error("No process callback registered!")

    def get_messages(self, phone_number: str) -> List[Dict[str, Any]]:
        """
        Get all buffered messages for a contact (non-destructive)

        Args:
            phone_number: Contact phone number

        Returns:
            List of message data dictionaries
        """
        with self._locks[phone_number]:
            return self._buffers[phone_number].copy()

    def clear_buffer(self, phone_number: str) -> int:
        """
        Clear buffer and cancel timer for a contact

        Args:
            phone_number: Contact phone number

        Returns:
            Number of messages that were cleared
        """
        with self._locks[phone_number]:
            # Cancel timer if exists
            with self._global_lock:
                if phone_number in self._timers:
                    self._timers[phone_number].cancel()
                    del self._timers[phone_number]
                    logger.debug(f"⏱️  Timer cancelled for {phone_number}")

            # Clear buffer
            count = len(self._buffers[phone_number])
            self._buffers[phone_number].clear()

            logger.debug(f"🧹 Cleared buffer for {phone_number} ({count} messages)")
            return count

    def get_buffer_size(self, phone_number: str) -> int:
        """
        Get current buffer size for a contact

        Args:
            phone_number: Contact phone number

        Returns:
            Number of messages in buffer
        """
        with self._locks[phone_number]:
            return len(self._buffers[phone_number])

    def has_buffered_messages(self, phone_number: str) -> bool:
        """
        Check if contact has any buffered messages

        Args:
            phone_number: Contact phone number

        Returns:
            True if buffer has messages
        """
        with self._locks[phone_number]:
            return len(self._buffers[phone_number]) > 0

    def cleanup_old_buffers(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up buffers that haven't been accessed in a while
        Should be called periodically to prevent memory leaks

        Args:
            max_age_seconds: Maximum age before cleanup (default 1 hour)

        Returns:
            Number of buffers cleaned up
        """
        # This is a simple implementation - could be improved with timestamps
        # For now, just clean empty buffers
        cleaned = 0

        with self._global_lock:
            empty_numbers = [
                phone for phone, buffer in self._buffers.items()
                if len(buffer) == 0
            ]

            for phone in empty_numbers:
                # Cancel timer
                if phone in self._timers:
                    self._timers[phone].cancel()
                    del self._timers[phone]

                # Remove lock and buffer
                if phone in self._locks:
                    del self._locks[phone]
                del self._buffers[phone]
                cleaned += 1

        if cleaned > 0:
            logger.info(f"🧹 Cleaned up {cleaned} empty buffers")

        return cleaned

    def get_stats(self) -> Dict[str, Any]:
        """
        Get buffer statistics

        Returns:
            Dictionary with buffer stats
        """
        with self._global_lock:
            total_messages = sum(len(buffer) for buffer in self._buffers.values())
            active_contacts = len(self._buffers)
            active_timers = len(self._timers)

            return {
                "active_contacts": active_contacts,
                "active_timers": active_timers,
                "total_buffered_messages": total_messages,
                "timeout": self.timeout,
                "max_messages": self.max_messages
            }
