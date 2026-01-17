#!/usr/bin/env python3
"""
Async Message Bus for zejzl.net
Clean, minimal, fast - extracted from Grokputer
"""

import asyncio
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
import pickle

import redis.asyncio as aioredis

logger = logging.getLogger("MessageBus")


@dataclass
class Message:
    """Message structure for the bus"""
    id: str
    content: str
    timestamp: datetime
    sender: str
    provider: str
    response: Optional[str] = None
    response_time: Optional[float] = None
    error: Optional[str] = None
    conversation_id: str = "default"
    
    @classmethod
    def create(cls, content: str, sender: str, provider: str, conversation_id: str = "default"):
        """Factory method to create a new message"""
        return cls(
            id=str(uuid4()),
            content=content,
            timestamp=datetime.now(),
            sender=sender,
            provider=provider,
            conversation_id=conversation_id
        )


class AsyncMessageBus:
    """
    High-performance async message bus with Redis persistence
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.running = False
        self.message_queue = asyncio.Queue()
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        self.conversation_cache: Dict[str, List[Dict]] = {}
        
    async def initialize(self):
        """Initialize the message bus and Redis connection"""
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=False)
            await self.redis.ping()
            self.running = True
            logger.info(f"✓ Message bus initialized (Redis: {self.redis_url})")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Redis: {e}")
            raise
    
    async def publish(self, channel: str, message: Message):
        """Publish message to a channel"""
        if not self.running:
            raise RuntimeError("Message bus not running")
        
        # Serialize and publish to Redis
        message_data = pickle.dumps(asdict(message))
        await self.redis.publish(channel, message_data)
        
        # Notify local subscribers
        if channel in self.subscribers:
            for queue in self.subscribers[channel]:
                await queue.put(message)
        
        logger.debug(f"Published to {channel}: {message.id}")
    
    async def subscribe(self, channel: str) -> asyncio.Queue:
        """Subscribe to a channel, returns queue for receiving messages"""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        
        queue = asyncio.Queue()
        self.subscribers[channel].append(queue)
        logger.debug(f"Subscribed to channel: {channel}")
        return queue
    
    async def unsubscribe(self, channel: str, queue: asyncio.Queue):
        """Unsubscribe from a channel"""
        if channel in self.subscribers and queue in self.subscribers[channel]:
            self.subscribers[channel].remove(queue)
            if not self.subscribers[channel]:
                del self.subscribers[channel]
    
    async def save_message(self, message: Message):
        """Persist message to Redis"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")
        
        conversation_key = f"conversation:{message.conversation_id}"
        message_data = pickle.dumps(asdict(message))
        
        # Add to list (newest first)
        await self.redis.lpush(conversation_key, message_data)
        
        # Keep only last 100 messages
        await self.redis.ltrim(conversation_key, 0, 99)
        
        # Set 30-day expiration
        await self.redis.expire(conversation_key, 30 * 24 * 3600)
    
    async def get_history(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """Retrieve conversation history"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")
        
        # Check cache first
        if conversation_id in self.conversation_cache:
            cached = self.conversation_cache[conversation_id]
            if len(cached) >= limit:
                return cached[:limit]
        
        # Fetch from Redis
        conversation_key = f"conversation:{conversation_id}"
        message_data_list = await self.redis.lrange(conversation_key, 0, limit - 1)
        
        history = []
        for message_data in reversed(message_data_list):
            try:
                msg_dict = pickle.loads(message_data)
                if msg_dict.get("response"):
                    history.append({"role": "user", "content": msg_dict["content"]})
                    history.append({"role": "assistant", "content": msg_dict["response"]})
            except Exception as e:
                logger.error(f"Error deserializing message: {e}")
        
        # Update cache
        self.conversation_cache[conversation_id] = history
        return history
    
    async def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.redis:
            await self.redis.aclose()
        logger.info("Message bus shut down")