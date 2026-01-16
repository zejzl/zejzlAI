#!/usr/bin/env python3
"""
Async Message Bus AI Framework with Redis & SQL Fallback
Supports: Zai, ChatGPT, Claude, Grok, Gemini, DeepSeek, and Qwen
Configuration: TOML format (Toon-like)
Persistence: Redis (primary) + SQLite (fallback)
"""

import asyncio
import logging
import os
import sys
import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
import aiohttp
from pathlib import Path
import toml
import pickle
import hashlib

# Try to import redis libraries, make them optional
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    try:
        import aioredis
        REDIS_AVAILABLE = True
    except ImportError:
        REDIS_AVAILABLE = False
        logger = logging.getLogger("AI_Framework")
        logger.warning("Redis not available. Install with: pip install redis")

try:
    import aiosqlite
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    logger = logging.getLogger("AI_Framework")
    logger.warning("SQLite not available. Install with: pip install aiosqlite")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_framework.log')
    ]
)
logger = logging.getLogger("AI_Framework")

@dataclass
class Message:
    """Message data structure"""
    id: str
    content: str
    timestamp: datetime
    sender: str
    provider: str
    response: Optional[str] = None
    response_time: Optional[float] = None
    error: Optional[str] = None
    conversation_id: str = "default"

class PersistenceLayer(ABC):
    """Abstract base class for persistence layers"""
    
    @abstractmethod
    async def initialize(self):
        """Initialize the persistence layer"""
        pass
    
    @abstractmethod
    async def save_message(self, message: Message):
        """Save a message"""
        pass
    
    @abstractmethod
    async def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history"""
        pass
    
    @abstractmethod
    async def save_config(self, config: Dict):
        """Save configuration"""
        pass
    
    @abstractmethod
    async def load_config(self) -> Dict:
        """Load configuration"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up resources"""
        pass

class RedisPersistence(PersistenceLayer):
    """Redis persistence layer"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis is not installed. Run: pip install redis")
        self.redis_url = redis_url
        self.redis = None
        self.config_key = "ai_framework:config"
    
    async def initialize(self):
        try:
            # Try newer redis-py async syntax first
            if hasattr(redis, 'asyncio'):
                self.redis = aioredis.from_url(self.redis_url)
            else:
                # Fallback to older aioredis syntax
                self.redis = await aioredis.from_url(self.redis_url)
            await self.redis.ping()
            logger.info("Redis persistence initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    async def save_message(self, message: Message):
        if not self.redis:
            raise RuntimeError("Redis not initialized")
        
        # Save message to a list for the conversation
        conversation_key = f"conversation:{message.conversation_id}"
        message_data = pickle.dumps(asdict(message))
        await self.redis.lpush(conversation_key, message_data)
        
        # Keep only last 100 messages per conversation
        await self.redis.ltrim(conversation_key, 0, 99)
        
        # Set expiration (30 days)
        await self.redis.expire(conversation_key, 30 * 24 * 3600)
    
    async def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        if not self.redis:
            raise RuntimeError("Redis not initialized")
        
        conversation_key = f"conversation:{conversation_id}"
        message_data_list = await self.redis.lrange(conversation_key, 0, limit - 1)
        
        history = []
        for message_data in reversed(message_data_list):
            try:
                message_dict = pickle.loads(message_data)
                if message_dict.get("response"):
                    history.append({"role": "user", "content": message_dict["content"]})
                    history.append({"role": "assistant", "content": message_dict["response"]})
            except Exception as e:
                logger.error(f"Error deserializing message: {e}")
        
        return history
    
    async def save_config(self, config: Dict):
        if not self.redis:
            raise RuntimeError("Redis not initialized")
        
        config_str = toml.dumps(config)
        await self.redis.set(self.config_key, config_str)
    
    async def load_config(self) -> Dict:
        if not self.redis:
            raise RuntimeError("Redis not initialized")
        
        config_str = await self.redis.get(self.config_key)
        if config_str:
            return toml.loads(config_str)
        return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        return {
            "providers": {
                "chatgpt": {"api_key": os.environ.get("OPENAI_API_KEY", ""), "model": "gpt-3.5-turbo"},
                "claude": {"api_key": os.environ.get("ANTHROPIC_API_KEY", ""), "model": "claude-3-opus-20240229"},
                "gemini": {"api_key": os.environ.get("GEMINI_API_KEY", ""), "model": "gemini-pro"},
                "zai": {"api_key": os.environ.get("ZAI_API_KEY", ""), "model": "zai-1"},
                "grok": {"api_key": os.environ.get("GROK_API_KEY", ""), "model": "grok-1"},
                "deepseek": {"api_key": os.environ.get("DEEPSEEK_API_KEY", ""), "model": "deepseek-coder"},
                "qwen": {"api_key": os.environ.get("QWEN_API_KEY", ""), "model": "qwen-turbo"}
            },
            "default_provider": "chatgpt",
            "redis_url": "redis://localhost:6379",
            "sqlite_path": str(Path.home() / ".ai_framework.db")
        }
    
    async def cleanup(self):
        if self.redis:
            await self.redis.close()

class SQLitePersistence(PersistenceLayer):
    """SQLite persistence layer (fallback)"""
    
    def __init__(self, db_path: str = None):
        if not SQLITE_AVAILABLE:
            raise ImportError("SQLite (aiosqlite) is not installed. Run: pip install aiosqlite")
        self.db_path = db_path or str(Path.home() / ".ai_framework.db")
        self.conn = None
        self.config_path = Path.home() / ".ai_framework_config.toon"
    
    async def initialize(self):
        self.conn = await aiosqlite.connect(self.db_path)
        
        # Create tables
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                sender TEXT NOT NULL,
                provider TEXT NOT NULL,
                response TEXT,
                response_time REAL,
                error TEXT,
                conversation_id TEXT DEFAULT 'default'
            )
        """)
        
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation ON messages(conversation_id, timestamp)
        """)
        
        await self.conn.commit()
        logger.info("SQLite persistence initialized")
    
    async def save_message(self, message: Message):
        if not self.conn:
            raise RuntimeError("SQLite not initialized")
        
        await self.conn.execute(
            """
            INSERT OR REPLACE INTO messages 
            (id, content, timestamp, sender, provider, response, response_time, error, conversation_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message.id,
                message.content,
                message.timestamp.isoformat(),
                message.sender,
                message.provider,
                message.response,
                message.response_time,
                message.error,
                message.conversation_id
            )
        )
        await self.conn.commit()
    
    async def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        if not self.conn:
            raise RuntimeError("SQLite not initialized")
        
        cursor = await self.conn.execute(
            """
            SELECT content, response FROM messages 
            WHERE conversation_id = ? AND response IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (conversation_id, limit)
        )
        
        rows = await cursor.fetchall()
        history = []
        
        for content, response in reversed(rows):
            history.append({"role": "user", "content": content})
            history.append({"role": "assistant", "content": response})
        
        return history
    
    async def save_config(self, config: Dict):
        config_str = toml.dumps(config)
        with open(self.config_path, "w") as f:
            f.write(config_str)
    
    async def load_config(self) -> Dict:
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return toml.load(f)
        return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        return {
            "providers": {
                "chatgpt": {"api_key": os.environ.get("OPENAI_API_KEY", ""), "model": "gpt-3.5-turbo"},
                "claude": {"api_key": os.environ.get("ANTHROPIC_API_KEY", ""), "model": "claude-3-opus-20240229"},
                "gemini": {"api_key": os.environ.get("GEMINI_API_KEY", ""), "model": "gemini-pro"},
                "zai": {"api_key": os.environ.get("ZAI_API_KEY", ""), "model": "zai-1"},
                "grok": {"api_key": os.environ.get("GROK_API_KEY", ""), "model": "grok-1"},
                "deepseek": {"api_key": os.environ.get("DEEPSEEK_API_KEY", ""), "model": "deepseek-coder"},
                "qwen": {"api_key": os.environ.get("QWEN_API_KEY", ""), "model": "qwen-turbo"}
            },
            "default_provider": "chatgpt",
            "redis_url": "redis://localhost:6379",
            "sqlite_path": str(Path.home() / ".ai_framework.db")
        }
    
    async def cleanup(self):
        if self.conn:
            await self.conn.close()

class HybridPersistence:
    """Hybrid persistence layer with Redis primary and SQLite fallback"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", sqlite_path: str = None):
        self.redis = None
        self.sqlite = None
        self.primary = None
        self.fallback = None
        
        # Only initialize if libraries are available
        if REDIS_AVAILABLE:
            self.redis = RedisPersistence(redis_url)
        if SQLITE_AVAILABLE:
            self.sqlite = SQLitePersistence(sqlite_path)
        
        if not REDIS_AVAILABLE and not SQLITE_AVAILABLE:
            raise ImportError("Neither Redis nor SQLite is available. Install at least one: pip install redis aiosqlite")
    
    async def initialize(self):
        # Try Redis first if available
        if self.redis:
            try:
                await self.redis.initialize()
                self.primary = self.redis
                if self.sqlite:
                    self.fallback = self.sqlite
                    await self.sqlite.initialize()  # Initialize fallback too
                logger.info("Using Redis as primary persistence with SQLite fallback")
                return
            except Exception as e:
                logger.warning(f"Redis not available, trying SQLite: {e}")
        
        # Fallback to SQLite
        if self.sqlite:
            await self.sqlite.initialize()
            self.primary = self.sqlite
            self.fallback = None
            logger.info("Using SQLite as primary persistence")
        else:
            raise RuntimeError("No persistence layer available")
    
    async def save_message(self, message: Message):
        try:
            await self.primary.save_message(message)
            if self.fallback:
                try:
                    await self.fallback.save_message(message)
                except Exception as e:
                    logger.warning(f"Failed to save to fallback: {e}")
        except Exception as e:
            if self.fallback:
                logger.warning(f"Primary failed, using fallback: {e}")
                await self.fallback.save_message(message)
            else:
                raise
    
    async def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        try:
            return await self.primary.get_conversation_history(conversation_id, limit)
        except Exception as e:
            if self.fallback:
                logger.warning(f"Primary failed, using fallback: {e}")
                return await self.fallback.get_conversation_history(conversation_id, limit)
            else:
                raise
    
    async def save_config(self, config: Dict):
        try:
            await self.primary.save_config(config)
            if self.fallback:
                try:
                    await self.fallback.save_config(config)
                except Exception as e:
                    logger.warning(f"Failed to save config to fallback: {e}")
        except Exception as e:
            if self.fallback:
                logger.warning(f"Primary failed, using fallback for config: {e}")
                await self.fallback.save_config(config)
            else:
                raise
    
    async def load_config(self) -> Dict:
        try:
            return await self.primary.load_config()
        except Exception as e:
            if self.fallback:
                logger.warning(f"Primary failed, using fallback for config: {e}")
                return await self.fallback.load_config()
            else:
                raise
    
    async def cleanup(self):
        if self.redis:
            await self.redis.cleanup()
        if self.sqlite:
            await self.sqlite.cleanup()

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or self.default_model
        self.session = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model for this provider"""
        pass
    
    @abstractmethod
    async def initialize(self):
        """Initialize the provider (e.g., create session)"""
        pass
    
    @abstractmethod
    async def generate_response(self, message: str, history: List[Dict] = None) -> str:
        """Generate a response to the given message"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up resources"""
        pass

class ChatGPTProvider(AIProvider):
    """OpenAI ChatGPT provider"""
    
    @property
    def name(self) -> str:
        return "ChatGPT"
    
    @property
    def default_model(self) -> str:
        return "gpt-3.5-turbo"
    
    async def initialize(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def generate_response(self, message: str, history: List[Dict] = None) -> str:
        if not self.session:
            await self.initialize()
        
        messages = history or []
        messages.append({"role": "user", "content": message})
        
        url = "https://api.openai.com/v1/chat/completions"
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Error in {self.name} API call: {str(e)}")
            raise
    
    async def cleanup(self):
        if self.session:
            await self.session.close()

class ClaudeProvider(AIProvider):
    """Anthropic Claude provider"""
    
    @property
    def name(self) -> str:
        return "Claude"
    
    @property
    def default_model(self) -> str:
        return "claude-3-opus-20240229"
    
    async def initialize(self):
        self.session = aiohttp.ClientSession(
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
    
    async def generate_response(self, message: str, history: List[Dict] = None) -> str:
        if not self.session:
            await self.initialize()
        
        messages = history or []
        messages.append({"role": "user", "content": message})
        
        url = "https://api.anthropic.com/v1/messages"
        data = {
            "model": self.model,
            "max_tokens": 1000,
            "messages": messages
        }
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["content"][0]["text"]
                else:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Error in {self.name} API call: {str(e)}")
            raise
    
    async def cleanup(self):
        if self.session:
            await self.session.close()

class GeminiProvider(AIProvider):
    """Google Gemini provider"""
    
    @property
    def name(self) -> str:
        return "Gemini"
    
    @property
    def default_model(self) -> str:
        return "gemini-pro"
    
    async def initialize(self):
        self.session = aiohttp.ClientSession()
    
    async def generate_response(self, message: str, history: List[Dict] = None) -> str:
        if not self.session:
            await self.initialize()
        
        # Convert history to Gemini format
        contents = []
        if history:
            for item in history:
                role = "user" if item["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": item["content"]}]})
        
        contents.append({"role": "user", "parts": [{"text": message}]})
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        data = {"contents": contents}
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Error in {self.name} API call: {str(e)}")
            raise
    
    async def cleanup(self):
        if self.session:
            await self.session.close()

# Placeholder implementations for other providers
class ZaiProvider(AIProvider):
    """Zai AI provider"""
    
    @property
    def name(self) -> str: