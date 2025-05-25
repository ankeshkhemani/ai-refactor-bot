"""Service for handling Redis-based message queues."""

import json
import logging
from typing import Any, Dict, Optional

import redis.asyncio as redis
from redis.asyncio.client import Redis

logger = logging.getLogger(__name__)


class QueueService:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize the queue service.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis: Optional[Redis] = None

    async def connect(self):
        """Connect to Redis."""
        if not self.redis:
            self.redis = await redis.from_url(self.redis_url)
            logger.info("Connected to Redis")

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Disconnected from Redis")

    async def enqueue(self, queue_name: str, data: Dict[str, Any]):
        """Add a message to the queue.

        Args:
            queue_name: Name of the queue
            data: Data to enqueue
        """
        if not self.redis:
            await self.connect()

        message = json.dumps(data)
        await self.redis.lpush(queue_name, message)
        logger.info(f"Enqueued message to {queue_name}")

    async def dequeue(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get a message from the queue.

        Args:
            queue_name: Name of the queue

        Returns:
            The dequeued message data, or None if queue is empty
        """
        if not self.redis:
            await self.connect()

        message = await self.redis.rpop(queue_name)
        if message:
            data = json.loads(message)
            logger.info(f"Dequeued message from {queue_name}")
            return data
        return None

    async def get_queue_length(self, queue_name: str) -> int:
        """Get the length of a queue.

        Args:
            queue_name: Name of the queue

        Returns:
            Number of messages in the queue
        """
        if not self.redis:
            await self.connect()

        return await self.redis.llen(queue_name)
