"""
RabbitMQ Queue Manager for WhatsApp Gateway Service
"""
import pika
import json
import time
from typing import Callable, Dict, Any
from loguru import logger
from config.settings import settings


class QueueManager:
    """Manage RabbitMQ connections and operations"""

    def __init__(self):
        self.connection = None
        self.channel = None
        self.rabbitmq_url = settings.RABBITMQ_URL
        self._connect()

    def _connect(self, max_retries: int = 5) -> None:
        """Establish connection to RabbitMQ with retry logic"""
        for attempt in range(max_retries):
            try:
                parameters = pika.URLParameters(self.rabbitmq_url)
                parameters.heartbeat = 600
                parameters.blocked_connection_timeout = 300

                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()

                # Declare all queues with configurations
                self._declare_queues()

                logger.info("Successfully connected to RabbitMQ")
                return
            except Exception as e:
                logger.warning(f"RabbitMQ connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("Failed to connect to RabbitMQ after all retries")
                    raise

    def _declare_queues(self) -> None:
        """Declare all required queues with specific configurations"""
        queues_config = {
            settings.QUEUE_INCOMING_MESSAGES: {
                'durable': True,
                'arguments': {
                    'x-message-ttl': 86400000,  # 24 hours in milliseconds
                    'x-max-length': 10000
                }
            },
            settings.QUEUE_OUTGOING_MESSAGES: {
                'durable': True,
                'arguments': {
                    'x-message-ttl': 3600000,  # 1 hour
                    'x-max-length': 5000
                }
            },
            settings.QUEUE_VOICE_TRANSCRIPTION: {
                'durable': True,
                'arguments': {
                    'x-message-ttl': 7200000,  # 2 hours
                    'x-max-length': 1000
                }
            }
        }

        for queue_name, config in queues_config.items():
            self.channel.queue_declare(
                queue=queue_name,
                durable=config['durable'],
                arguments=config['arguments']
            )
            logger.info(f"Declared queue: {queue_name}")

    def publish(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """
        Publish a message to specified queue

        Args:
            queue_name: Name of the queue
            message: Message data as dictionary

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.channel or self.connection.is_closed:
                self._connect()

            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message, ensure_ascii=False),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            logger.debug(f"Published message to queue '{queue_name}': {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message to queue '{queue_name}': {e}")
            return False

    def consume(self, queue_name: str, callback: Callable, prefetch_count: int = 1) -> None:
        """
        Start consuming messages from queue

        Args:
            queue_name: Name of the queue to consume from
            callback: Function to process messages
            prefetch_count: Number of messages to prefetch
        """
        try:
            if not self.channel or self.connection.is_closed:
                self._connect()

            self.channel.basic_qos(prefetch_count=prefetch_count)
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=False
            )
            logger.info(f"Started consuming from queue: {queue_name}")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping queue consumer...")
            self.stop_consuming()
        except Exception as e:
            logger.error(f"Error consuming from queue '{queue_name}': {e}")
            raise

    def stop_consuming(self) -> None:
        """Stop consuming messages"""
        if self.channel:
            self.channel.stop_consuming()
        logger.info("Stopped consuming messages")

    def get_queue_size(self, queue_name: str) -> int:
        """Get the current size of a queue"""
        try:
            if not self.channel or self.connection.is_closed:
                self._connect()

            method = self.channel.queue_declare(queue=queue_name, passive=True)
            return method.method.message_count
        except Exception as e:
            logger.error(f"Failed to get queue size for '{queue_name}': {e}")
            return 0

    def close(self) -> None:
        """Close the connection gracefully"""
        try:
            if self.channel:
                self.channel.close()
            if self.connection:
                self.connection.close()
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")


# Global queue manager instance
queue_manager = QueueManager()
