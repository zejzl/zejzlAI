#!/usr/bin/env python3
"""
Async Message Bus AI Framework with Redis & SQL Fallback
Supports: Zai, ChatGPT, Claude, Grok, Gemini, DeepSeek, and Qwen
Configuration: Python-Toon annotated format
Persistence: Redis (primary) + SQLite (fallback)
"""

# --- 1. Future Imports (Must be first) ---
from __future__ import annotations

# --- 2. Standard Library Imports ---
import asyncio
import json
import logging
import os
import pickle
import sys
import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from datetime import datetime
from pathlib import Path
import pickle
import hashlib

# --- 3. Third-Party Library Imports ---
import aiohttp
try:
    import toon
except ImportError:
    import toml as toon  # Fallback to standard toml
import redis.asyncio as aioredis
import aiosqlite

# --- 4. Local Application Imports ---
from dotenv import load_dotenv
from rate_limiter import get_rate_limiter
from telemetry import get_telemetry
from src.magic import FairyMagic
from src.security import EnterpriseSecurity
from src.performance import record_metric
from src.logging_debug import logger, debug_monitor, log_execution, log_ai_interaction, setup_logging

# (The sys.path fix you added)
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

# --- USE ABSOLUTE IMPORTS HERE ---
# These point to the full path from the project root.
from src.agents.observer import ObserverAgent
from src.cost_calculator import CostCalculator, TokenUsage
from src.agents.actor import ActorAgent
from src.agents.analyzer import AnalyzerAgent
from src.agents.executor import ExecutorAgent
from src.agents.improver import ImproverAgent
from src.agents.learner import LearnerAgent
from src.agents.memory import MemoryAgent
from src.agents.reasoner import ReasonerAgent
from src.agents.validator import ValidatorAgent

# etc...

async def run_interactive_session():
    observer = ObserverAgent()

    while True:
        choice = run_interactive_menu()
        if choice == "1":
            task = input("Enter a task for the Observer: ")
            obs = await observer.observe(task)
            print(f"\n[Observer Output]: {obs}\n")
        elif choice == "9":
            print("Exiting interactive mode.")
            break
        else:
            print(f"Option {choice} not implemented yet.")

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
    token_usage: Optional[TokenUsage] = None
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
        self.redis_url = redis_url
        self.redis = None
        self.config_key = "ai_framework:config"

    async def initialize(self):
        try:
            self.redis = aioredis.from_url(self.redis_url)
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

        config_str = toon.dumps(config)
        await self.redis.set(self.config_key, config_str)
    
    async def load_config(self) -> Dict:
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        config_str = await self.redis.get(self.config_key)
        if config_str:
            return toon.loads(config_str)
        return self.get_default_config()

    async def save_magic_state(self, magic_state: Dict):
        """Save magic system state to Redis"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        magic_key = "ai_framework:magic_state"
        state_str = pickle.dumps(magic_state)
        await self.redis.set(magic_key, state_str)

    async def load_magic_state(self) -> Dict:
        """Load magic system state from Redis"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        magic_key = "ai_framework:magic_state"
        state_data = await self.redis.get(magic_key)
        if state_data:
            return pickle.loads(state_data)
        return {}  # Return empty dict if no state saved

    async def save_learner_patterns(self, patterns_state: Dict):
        """Save learner patterns to Redis"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        patterns_key = "ai_framework:learner_patterns"
        patterns_data = pickle.dumps(patterns_state)
        await self.redis.set(patterns_key, patterns_data)

    async def load_learner_patterns(self) -> Dict:
        """Load learner patterns from Redis"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        patterns_key = "ai_framework:learner_patterns"
        patterns_data = await self.redis.get(patterns_key)
        if patterns_data:
            return pickle.loads(patterns_data)
        return {}  # Return empty dict if no patterns saved

    def get_default_config(self) -> Dict:
        return {
            "providers": {
                "chatgpt": {"api_key": os.environ.get("OPENAI_API_KEY", ""), "model": "gpt-3.5-turbo"},
                "claude": {"api_key": os.environ.get("ANTHROPIC_API_KEY", ""), "model": "claude-3-5-sonnet-20241022"},
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

    async def save_magic_state(self, magic_state: Dict):
        """Save magic system state to SQLite database"""
        if not self.conn:
            raise RuntimeError("SQLite not initialized")

        # Store as JSON in a magic_state table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS magic_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        state_json = json.dumps(magic_state)
        await self.conn.execute("""
            INSERT OR REPLACE INTO magic_state (key, value, updated_at)
            VALUES (?, ?, ?)
        """, ("state", state_json, datetime.now().isoformat()))

        await self.conn.commit()

    async def load_magic_state(self) -> Dict:
        """Load magic system state from SQLite database"""
        if not self.conn:
            raise RuntimeError("SQLite not initialized")

        cursor = await self.conn.execute("""
            SELECT value FROM magic_state WHERE key = 'state'
        """)

        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return {}  # Return empty dict if no state saved

    async def save_learner_patterns(self, patterns_state: Dict):
        """Save learner patterns to SQLite database"""
        if not self.conn:
            raise RuntimeError("SQLite not initialized")

        # Store as JSON in a learner_patterns table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS learner_patterns (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        patterns_json = json.dumps(patterns_state)
        await self.conn.execute("""
            INSERT OR REPLACE INTO learner_patterns (key, value, updated_at)
            VALUES (?, ?, ?)
        """, ("patterns", patterns_json, datetime.now().isoformat()))

        await self.conn.commit()

    async def load_learner_patterns(self) -> Dict:
        """Load learner patterns from SQLite database"""
        if not self.conn:
            raise RuntimeError("SQLite not initialized")

        cursor = await self.conn.execute("""
            SELECT value FROM learner_patterns WHERE key = 'patterns'
        """)

        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return {}  # Return empty dict if no patterns saved

    async def cleanup(self):
        if self.redis:
            await self.redis.aclose()

class SQLitePersistence(PersistenceLayer):
    """SQLite persistence layer (fallback)"""
    
    def __init__(self, db_path: str = None):
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

        # Add token usage columns if they don't exist (schema migration)
        try:
            await self.conn.execute("ALTER TABLE messages ADD COLUMN token_usage_provider TEXT")
        except:
            pass  # Column might already exist
        try:
            await self.conn.execute("ALTER TABLE messages ADD COLUMN token_usage_model TEXT")
        except:
            pass
        try:
            await self.conn.execute("ALTER TABLE messages ADD COLUMN prompt_tokens INTEGER DEFAULT 0")
        except:
            pass
        try:
            await self.conn.execute("ALTER TABLE messages ADD COLUMN completion_tokens INTEGER DEFAULT 0")
        except:
            pass
        try:
            await self.conn.execute("ALTER TABLE messages ADD COLUMN total_tokens INTEGER DEFAULT 0")
        except:
            pass
        try:
            await self.conn.execute("ALTER TABLE messages ADD COLUMN cost_usd REAL DEFAULT 0.0")
        except:
            pass
        
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation ON messages(conversation_id, timestamp)
        """)

        # Create usage analytics tables
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_usage (
                date TEXT PRIMARY KEY,
                total_requests INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                total_cost_usd REAL DEFAULT 0.0,
                avg_response_time REAL DEFAULT 0.0,
                success_rate REAL DEFAULT 0.0
            )
        """)

        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS provider_usage (
                provider TEXT,
                model TEXT,
                date TEXT,
                requests INTEGER DEFAULT 0,
                tokens INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0,
                avg_response_time REAL DEFAULT 0.0,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                PRIMARY KEY (provider, model, date)
            )
        """)

        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS hourly_usage (
                hour TEXT PRIMARY KEY,  -- Format: YYYY-MM-DD-HH
                requests INTEGER DEFAULT 0,
                tokens INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0,
                peak_concurrent INTEGER DEFAULT 0
            )
        """)

        await self.conn.commit()
        logger.info("SQLite persistence initialized with usage analytics")
    
    async def save_message(self, message: Message):
        if not self.conn:
            raise RuntimeError("SQLite not initialized")

        await self.conn.execute(
            """
            INSERT OR REPLACE INTO messages
            (id, content, timestamp, sender, provider, response, response_time, error, conversation_id,
             token_usage_provider, token_usage_model, prompt_tokens, completion_tokens, total_tokens, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                message.conversation_id,
                message.token_usage.provider if message.token_usage else None,
                message.token_usage.model if message.token_usage else None,
                message.token_usage.prompt_tokens if message.token_usage else 0,
                message.token_usage.completion_tokens if message.token_usage else 0,
                message.token_usage.total_tokens if message.token_usage else 0,
                message.token_usage.cost_usd if message.token_usage else 0.0
            )
        )

        # Update usage analytics
        await self._update_usage_analytics(message)

        # Prune old messages - keep only last 100 per conversation (matching Redis behavior)
        await self.conn.execute(
            """
            DELETE FROM messages
            WHERE conversation_id = ?
            AND id NOT IN (
                SELECT id FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp DESC
                LIMIT 100
            )
            """,
            (message.conversation_id, message.conversation_id)
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
        config_str = toon.dumps(config)
        with open(self.config_path, "w") as f:
            f.write(config_str)
    
    async def load_config(self) -> Dict:
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return toon.load(f)
        return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        return {
            "providers": {
                "chatgpt": {"api_key": os.environ.get("OPENAI_API_KEY", ""), "model": "gpt-3.5-turbo"},
                "claude": {"api_key": os.environ.get("ANTHROPIC_API_KEY", ""), "model": "claude-3-5-sonnet-20241022"},
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

    async def _update_usage_analytics(self, message: Message):
        """Update usage analytics tables with message data"""
        if not message.token_usage:
            return

        date = message.timestamp.strftime("%Y-%m-%d")
        hour = message.timestamp.strftime("%Y-%m-%d-%H")

        # Update daily usage
        await self.conn.execute("""
            INSERT OR REPLACE INTO daily_usage (date, total_requests, total_tokens, total_cost_usd, avg_response_time, success_rate)
            SELECT
                ?,
                COALESCE((SELECT total_requests FROM daily_usage WHERE date = ?), 0) + 1,
                COALESCE((SELECT total_tokens FROM daily_usage WHERE date = ?), 0) + ?,
                COALESCE((SELECT total_cost_usd FROM daily_usage WHERE date = ?), 0) + ?,
                CASE WHEN COALESCE((SELECT total_requests FROM daily_usage WHERE date = ?), 0) > 0
                     THEN ((SELECT avg_response_time FROM daily_usage WHERE date = ?) * (SELECT total_requests FROM daily_usage WHERE date = ?) + ?) / ((SELECT total_requests FROM daily_usage WHERE date = ?) + 1)
                     ELSE ?
                END,
                1.0  -- Placeholder for success rate calculation
            """, (
                date, date, date, message.token_usage.total_tokens, date, message.token_usage.cost_usd,
                date, date, date, message.response_time or 0, date, message.response_time or 0
            ))

        # Update provider usage
        provider = message.token_usage.provider
        model = message.token_usage.model
        is_success = message.error is None

        await self.conn.execute("""
            INSERT OR REPLACE INTO provider_usage
            (provider, model, date, requests, tokens, cost_usd, avg_response_time, success_count, error_count)
            SELECT
                ?, ?, ?,
                COALESCE((SELECT requests FROM provider_usage WHERE provider = ? AND model = ? AND date = ?), 0) + 1,
                COALESCE((SELECT tokens FROM provider_usage WHERE provider = ? AND model = ? AND date = ?), 0) + ?,
                COALESCE((SELECT cost_usd FROM provider_usage WHERE provider = ? AND model = ? AND date = ?), 0) + ?,
                CASE WHEN COALESCE((SELECT requests FROM provider_usage WHERE provider = ? AND model = ? AND date = ?), 0) > 0
                     THEN ((SELECT avg_response_time FROM provider_usage WHERE provider = ? AND model = ? AND date = ?) * (SELECT requests FROM provider_usage WHERE provider = ? AND model = ? AND date = ?) + ?) / ((SELECT requests FROM provider_usage WHERE provider = ? AND model = ? AND date = ?) + 1)
                     ELSE ?
                END,
                COALESCE((SELECT success_count FROM provider_usage WHERE provider = ? AND model = ? AND date = ?), 0) + ?,
                COALESCE((SELECT error_count FROM provider_usage WHERE provider = ? AND model = ? AND date = ?), 0) + ?
            """, (
                provider, model, date,
                provider, model, date,
                provider, model, date, message.token_usage.total_tokens,
                provider, model, date, message.token_usage.cost_usd,
                provider, model, date,
                provider, model, date, provider, model, date, message.response_time or 0,
                provider, model, date, message.response_time or 0,
                provider, model, date, 1 if is_success else 0,
                provider, model, date, 0 if is_success else 1
            ))

        # Update hourly usage
        await self.conn.execute("""
            INSERT OR REPLACE INTO hourly_usage (hour, requests, tokens, cost_usd, peak_concurrent)
            SELECT
                ?,
                COALESCE((SELECT requests FROM hourly_usage WHERE hour = ?), 0) + 1,
                COALESCE((SELECT tokens FROM hourly_usage WHERE hour = ?), 0) + ?,
                COALESCE((SELECT cost_usd FROM hourly_usage WHERE hour = ?), 0) + ?,
                GREATEST(COALESCE((SELECT peak_concurrent FROM hourly_usage WHERE hour = ?), 0), 1)
            """, (
                hour, hour, hour, message.token_usage.total_tokens, hour, message.token_usage.cost_usd, hour
            ))

    async def cleanup(self):
        if self.conn:
            await self.conn.close()

class HybridPersistence:
    """Hybrid persistence layer with Redis primary and SQLite fallback"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", sqlite_path: str = None):
        self.redis = RedisPersistence(redis_url)
        self.sqlite = SQLitePersistence(sqlite_path)
        self.primary = None
        self.fallback = None
    
    async def initialize(self):
        # Try Redis first
        try:
            await self.redis.initialize()
            self.primary = self.redis
            self.fallback = self.sqlite
            await self.sqlite.initialize()  # Initialize fallback too
            logger.info("Using Redis as primary persistence with SQLite fallback")
        except Exception as e:
            logger.warning(f"Redis not available, using SQLite: {e}")
            await self.sqlite.initialize()
            self.primary = self.sqlite
            self.fallback = None
            logger.info("Using SQLite as primary persistence")
    
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
    
    async def save_magic_state(self, magic_state: Dict):
        """Save magic system state to persistence"""
        try:
            await self.primary.save_magic_state(magic_state)
            if self.fallback:
                try:
                    await self.fallback.save_magic_state(magic_state)
                except Exception as e:
                    logger.warning(f"Failed to save magic state to fallback: {e}")
        except Exception as e:
            if self.fallback:
                logger.warning(f"Primary failed, using fallback for magic state: {e}")
                await self.fallback.save_magic_state(magic_state)
            else:
                raise

    async def load_magic_state(self) -> Dict:
        """Load magic system state from persistence"""
        try:
            return await self.primary.load_magic_state()
        except Exception as e:
            if self.fallback:
                logger.warning(f"Primary failed, using fallback for magic state: {e}")
                return await self.fallback.load_magic_state()
            else:
                raise

    async def save_learner_patterns(self, patterns_state: Dict):
        """Save learner patterns to persistence"""
        try:
            await self.primary.save_learner_patterns(patterns_state)
            if self.fallback:
                try:
                    await self.fallback.save_learner_patterns(patterns_state)
                except Exception as e:
                    logger.warning(f"Failed to save learner patterns to fallback: {e}")
        except Exception as e:
            if self.fallback:
                logger.warning(f"Primary failed, using fallback for learner patterns: {e}")
                await self.fallback.save_learner_patterns(patterns_state)
            else:
                raise

    async def load_learner_patterns(self) -> Dict:
        """Load learner patterns from persistence"""
        try:
            return await self.primary.load_learner_patterns()
        except Exception as e:
            if self.fallback:
                logger.warning(f"Primary failed, using fallback for learner patterns: {e}")
                return await self.fallback.load_learner_patterns()
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
    async def generate_response(self, message: str, history: List[Dict] = None) -> Tuple[str, TokenUsage]:
        """Generate a response to the given message with token usage"""
        pass

    async def generate_response_stream(self, message: str, history: List[Dict] = None):
        """Generate a streaming response to the given message (default implementation yields full response)"""
        response = await self.generate_response(message, history)
        yield response

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
    
    @log_ai_interaction("chatgpt", "generate_response")
    async def generate_response(self, message: str, history: List[Dict] = None) -> Tuple[str, TokenUsage]:
        if not self.session:
            await self.initialize()

        messages = history or []
        messages.append({"role": "user", "content": message})

        logger.debug(f"ChatGPT API call", message_length=len(message), history_length=len(messages))

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
                    response_content = result["choices"][0]["message"]["content"]

                    # Extract token usage from OpenAI response
                    usage = result.get("usage", {})
                    token_usage = TokenUsage(
                        provider=self.name,
                        model=self.model,
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                        total_tokens=usage.get("total_tokens", 0)
                    )

                    logger.debug(f"ChatGPT API success", response_length=len(response_content), model=self.model, tokens=token_usage.total_tokens)
                    return response_content, token_usage
                else:
                    error_text = await response.text()
                    logger.error(f"ChatGPT API error", status=response.status, error=error_text[:200])
                    raise Exception(f"API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Error in {self.name} API call", error=str(e), model=self.model)
            raise

    async def generate_response_stream(self, message: str, history: List[Dict] = None):
        """Generate streaming response from OpenAI API"""
        if not self.session:
            await self.initialize()

        messages = history or []
        messages.append({"role": "user", "content": message})

        url = "https://api.openai.com/v1/chat/completions"
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "stream": True
        }

        try:
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # Remove 'data: ' prefix
                            if data_str == '[DONE]':
                                break
                            try:
                                chunk_data = json.loads(data_str)
                                if 'choices' in chunk_data and chunk_data['choices']:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Error in {self.name} streaming API call: {str(e)}")
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
        return "claude-3-5-sonnet-20241022"
    
    async def initialize(self):
        self.session = aiohttp.ClientSession(
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
    
    async def generate_response(self, message: str, history: List[Dict] = None) -> Tuple[str, TokenUsage]:
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
                    response_content = result["content"][0]["text"]

                    # Extract token usage from Claude response
                    usage = result.get("usage", {})
                    token_usage = TokenUsage(
                        provider=self.name,
                        model=self.model,
                        prompt_tokens=usage.get("input_tokens", 0),
                        completion_tokens=usage.get("output_tokens", 0)
                    )

                    return response_content, token_usage
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
    
    async def generate_response(self, message: str, history: List[Dict] = None) -> Tuple[str, TokenUsage]:
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
                    response_content = result["candidates"][0]["content"]["parts"][0]["text"]

                    # Gemini doesn't provide detailed token usage, create basic tracking
                    # Estimate tokens roughly (this is approximate)
                    prompt_tokens = len(message) // 4  # Rough estimate
                    completion_tokens = len(response_content) // 4
                    token_usage = TokenUsage(
                        provider=self.name,
                        model=self.model,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens
                    )

                    return response_content, token_usage
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
        return "Zai"
    
    @property
    def default_model(self) -> str:
        return "zai-1"
    
    async def initialize(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def generate_response(self, message: str, history: List[Dict] = None) -> Tuple[str, TokenUsage]:
        await asyncio.sleep(1)
        response = f"Zai response to: {message}"
        token_usage = TokenUsage(
            provider=self.name,
            model=self.model,
            prompt_tokens=len(message) // 4,
            completion_tokens=len(response) // 4
        )
        return response, token_usage
    
    async def cleanup(self):
        if self.session:
            await self.session.close()

class GrokProvider(AIProvider):
    """xAI Grok provider"""
    
    @property
    def name(self) -> str:
        return "Grok"
    
    @property
    def default_model(self) -> str:
        return "grok-1"
    
    async def initialize(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def generate_response(self, message: str, history: List[Dict] = None) -> Tuple[str, TokenUsage]:
        await asyncio.sleep(1)
        response = f"Grok response to: {message}"
        token_usage = TokenUsage(
            provider=self.name,
            model=self.model,
            prompt_tokens=len(message) // 4,
            completion_tokens=len(response) // 4
        )
        return response, token_usage
    
    async def cleanup(self):
        if self.session:
            await self.session.close()

class DeepSeekProvider(AIProvider):
    """DeepSeek AI provider"""
    
    @property
    def name(self) -> str:
        return "DeepSeek"
    
    @property
    def default_model(self) -> str:
        return "deepseek-coder"
    
    async def initialize(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def generate_response(self, message: str, history: List[Dict] = None) -> Tuple[str, TokenUsage]:
        await asyncio.sleep(1)
        response = f"DeepSeek response to: {message}"
        token_usage = TokenUsage(
            provider=self.name,
            model=self.model,
            prompt_tokens=len(message) // 4,
            completion_tokens=len(response) // 4
        )
        return response, token_usage
    
    async def cleanup(self):
        if self.session:
            await self.session.close()

class QwenProvider(AIProvider):
    """Alibaba Qwen provider"""
    
    @property
    def name(self) -> str:
        return "Qwen"
    
    @property
    def default_model(self) -> str:
        return "qwen-turbo"
    
    async def initialize(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def generate_response(self, message: str, history: List[Dict] = None) -> Tuple[str, TokenUsage]:
        await asyncio.sleep(1)
        response = f"Qwen response to: {message}"
        token_usage = TokenUsage(
            provider=self.name,
            model=self.model,
            prompt_tokens=len(message) // 4,
            completion_tokens=len(response) // 4
        )
        return response, token_usage
    
    async def cleanup(self):
        if self.session:
            await self.session.close()

class AsyncMessageBus:
    """Async message bus for handling AI provider requests with hybrid persistence and self-healing"""

    def __init__(self):
        self.providers: Dict[str, AIProvider] = {}
        self.message_queue = asyncio.Queue()
        self.response_handlers: Dict[str, Callable] = {}
        self.conversation_cache: Dict[str, List[Dict]] = {}
        self.running = False
        self.persistence = HybridPersistence()
        self.config = None
        self.magic = FairyMagic(persistence=self.persistence)  # Self-healing magic system
    
    async def load_config(self) -> Dict:
        """Load configuration from persistence layer"""
        return await self.persistence.load_config()
    
    async def save_config(self):
        """Save configuration to persistence layer"""
        await self.persistence.save_config(self.config)
    
    async def register_provider(self, provider_name: str, provider: AIProvider):
        """Register an AI provider"""
        await provider.initialize()
        self.providers[provider_name.lower()] = provider
        logger.info(f"Registered provider: {provider.name}")
    
    async def unregister_provider(self, provider_name: str):
        """Unregister an AI provider"""
        provider_name = provider_name.lower()
        if provider_name in self.providers:
            await self.providers[provider_name].cleanup()
            del self.providers[provider_name]
            logger.info(f"Unregistered provider: {provider_name}")
    
    @log_execution("debug")
    async def send_message(self, content: str, provider_name: str = None,
                          conversation_id: str = "default", stream: bool = False,
                          consensus: bool = False, consensus_providers: List[str] = None) -> str:
        """Send a message to a specific provider and return the response"""
        logger.debug("Starting message send", content_length=len(content),
                    provider=provider_name, consensus=consensus, stream=stream)

        provider_name = provider_name or self.config.get("default_provider", "chatgpt")
        provider_name = provider_name.lower()

        # Handle consensus mode
        if consensus:
            logger.info("Using consensus mode", provider=provider_name, consensus_providers=consensus_providers)
            return await self._send_consensus_message(content, provider_name, conversation_id,
                                                     consensus_providers, stream)

        if provider_name not in self.providers:
            logger.error("Provider not registered", provider=provider_name, available=list(self.providers.keys()))
            raise ValueError(f"Provider {provider_name} not registered")

        # Performance monitoring: request start
        request_start = asyncio.get_event_loop().time()

        logger.debug("Provider validated", provider=provider_name, request_start=request_start)

        # Rate limiting check
        rate_limiter = get_rate_limiter()
        if not await rate_limiter.acquire(provider_name, timeout=30.0):
            record_metric("rate_limit_exceeded", 1, {"provider": provider_name})
            raise RuntimeError(f"Rate limit exceeded for provider {provider_name}")

        # Apply fairy shield protection for critical operations
        if self.magic.is_shielded:
            logger.debug("Fairy shield active - protecting against unauthorized access")

        # Pre-task vitality boost for agent performance
        agent_config = {"max_tokens": 1024}
        boost_result = await self.magic.acorn_vitality_boost(f"provider_{provider_name}", agent_config)
        if boost_result.get("vitality_boost", 1.0) > 1.0:
            record_metric("vitality_boost_applied", boost_result["vitality_boost"], {"provider": provider_name})
            logger.info("Applied vitality boost to %s provider", provider_name)

        provider = self.providers[provider_name]

        # Get conversation history from persistence or cache
        if conversation_id not in self.conversation_cache:
            self.conversation_cache[conversation_id] = await self.persistence.get_conversation_history(
                conversation_id
            )

        history = self.conversation_cache[conversation_id]

        # Create message
        message_id = f"{provider_name}_{datetime.now().timestamp()}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        message = Message(
            id=message_id,
            content=content,
            timestamp=datetime.now(),
            sender="user",
            provider=provider_name,
            conversation_id=conversation_id
        )

        try:
            start_time = asyncio.get_event_loop().time()
            telemetry = get_telemetry()

            # Retry logic for transient failures
            max_retries = 3
            retry_delay = 1.0  # Start with 1 second
            last_error = None

            for attempt in range(max_retries):
                try:
                    if stream:
                        # Streaming response - token counting not yet implemented for streaming
                        response = ""
                        async for chunk in provider.generate_response_stream(content, history):
                            response += chunk
                            # In streaming mode, we could yield chunks here
                            # For now, accumulate and return complete response
                        response_time = asyncio.get_event_loop().time() - start_time
                        # Create basic token usage for streaming (to be improved)
                        token_usage = TokenUsage(provider=provider.name, model=provider.model)
                        CostCalculator.calculate_cost(token_usage)
                    else:
                        # Regular response
                        response, token_usage = await provider.generate_response(content, history)
                        response_time = asyncio.get_event_loop().time() - start_time

                    message.response = response
                    message.response_time = response_time

                    # Update conversation history
                    history.append({"role": "user", "content": content})
                    history.append({"role": "assistant", "content": response})

                    # Keep only last 10 messages in cache
                    if len(history) > 10:
                        self.conversation_cache[conversation_id] = history[-10:]

                    # Save message to persistence
                    await self.persistence.save_message(message)

                    # Record telemetry
                    await telemetry.record_call(
                        component=f"provider_{provider_name}",
                        response_time=response_time,
                        success=True
                    )

                    # Performance monitoring: successful request
                    total_request_time = asyncio.get_event_loop().time() - request_start
                    record_metric("request_duration", total_request_time * 1000, {"provider": provider_name, "status": "success"})
                    record_metric("requests_total", 1, {"provider": provider_name, "status": "success"})

                    logger.info(f"Response from {provider_name} in {response_time:.2f}s")
                    return response

                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()

                    # Check if error is retryable (transient network/API issues)
                    retryable_errors = ["timeout", "503", "502", "500", "connection", "temporary"]
                    is_retryable = any(err in error_str for err in retryable_errors)

                    if is_retryable and attempt < max_retries - 1:
                        logger.warning(
                            f"Retryable error from {provider_name} (attempt {attempt + 1}/{max_retries}): {e}"
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        # Non-retryable error or max retries reached
                        raise

            # If we get here, all retries failed
            raise last_error

        except Exception as e:
            # Attempt auto-healing with magic system
            healed = await self.magic.auto_heal("ai_provider", e)
            if healed:
                logger.info("Magic auto-healing successful, retrying %s request", provider_name)
                # Retry the request after successful healing
                try:
                    response = await provider.generate_response(content, history)
                    response_time = asyncio.get_event_loop().time() - start_time

                    message.response = response
                    message.response_time = response_time
                    message.token_usage = token_usage

                    # Calculate cost for this usage
                    if token_usage:
                        CostCalculator.calculate_cost(token_usage)

                    # Update conversation history
                    history.append({"role": "user", "content": content})
                    history.append({"role": "assistant", "content": response})

                    # Keep only last 10 messages in cache
                    if len(history) > 10:
                        self.conversation_cache[conversation_id] = history[-10:]

                    # Save message to persistence
                    await self.persistence.save_message(message)

                    # Record telemetry
                    await telemetry.record_call(
                        component=f"provider_{provider_name}",
                        response_time=response_time,
                        success=True
                    )

                    # Performance monitoring: successful request
                    total_request_time = asyncio.get_event_loop().time() - request_start
                    record_metric("request_duration", total_request_time * 1000, {"provider": provider_name, "status": "success"})
                    record_metric("requests_total", 1, {"provider": provider_name, "status": "success"})

                    logger.info(f"Response from {provider_name} after healing in {response_time:.2fs}")
                    return response

                except Exception as retry_error:
                    logger.warning("Retry after healing failed: %s", retry_error)
                    # Fall through to original error handling

            # Original error handling if healing failed or wasn't attempted
            message.error = str(e)
            await self.persistence.save_message(message)

            # Record failed telemetry
            response_time = asyncio.get_event_loop().time() - start_time
            await telemetry.record_call(
                component=f"provider_{provider_name}",
                response_time=response_time,
                success=False
            )

            # Performance monitoring: failed request
            total_request_time = asyncio.get_event_loop().time() - request_start
            record_metric("request_duration", total_request_time * 1000, {"provider": provider_name, "status": "error"})
            record_metric("requests_total", 1, {"provider": provider_name, "status": "error", "error_type": type(e).__name__})

            raise

    async def _send_consensus_message(self, content: str, primary_provider: str,
                                    conversation_id: str, consensus_providers: List[str] = None,
                                    stream: bool = False) -> str:
        """Send message to multiple providers and return consensus response"""

        # Determine which providers to use for consensus
        available_providers = list(self.providers.keys())
        if consensus_providers:
            providers_to_use = [p for p in consensus_providers if p in available_providers]
        else:
            # Use primary provider plus 2-3 others for consensus
            providers_to_use = [primary_provider]
            other_providers = [p for p in available_providers if p != primary_provider]
            providers_to_use.extend(other_providers[:2])  # Add up to 2 more providers

        if len(providers_to_use) < 2:
            logger.warning("Not enough providers for consensus, falling back to single provider")
            return await self.send_message(content, primary_provider, conversation_id, stream)

        logger.info(f"Running consensus with providers: {providers_to_use}")

        # Get responses from all providers concurrently
        tasks = []
        for provider_name in providers_to_use:
            task = self.send_message(content, provider_name, conversation_id, stream)
            tasks.append(task)

        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Consensus gathering failed: {e}")
            # Fallback to primary provider
            return await self.send_message(content, primary_provider, conversation_id, stream)

        # Filter out exceptions and collect valid responses
        valid_responses = []
        provider_responses = []

        for i, response in enumerate(responses):
            provider_name = providers_to_use[i]
            if isinstance(response, Exception):
                logger.warning(f"Provider {provider_name} failed in consensus: {response}")
                continue

            valid_responses.append(response)
            provider_responses.append({
                "provider": provider_name,
                "response": response,
                "length": len(response)
            })

        if not valid_responses:
            raise RuntimeError("All providers failed in consensus mode")

        # Simple consensus algorithm: choose the most common response (basic similarity)
        if len(valid_responses) == 1:
            return valid_responses[0]

        # For now, use a simple approach: return the longest response as it's likely most comprehensive
        # In a more sophisticated implementation, we could use semantic similarity, voting, etc.
        best_response = max(valid_responses, key=len)

        # Log consensus results
        logger.info(f"Consensus completed: {len(valid_responses)}/{len(providers_to_use)} providers succeeded")
        for resp in provider_responses:
            logger.debug(f"Provider {resp['provider']}: {resp['length']} chars")

        return best_response

    async def start(self):
        """Start the message bus"""
        logger.info("Starting ZEJZL.NET AsyncMessageBus")
        self.running = True

        # Initialize persistence
        logger.debug("Initializing persistence layer")
        await self.persistence.initialize()
        logger.info("Persistence layer initialized")
        
        # Load configuration
        self.config = await self.load_config()
        
        # Register providers based on config
        provider_classes = {
            "chatgpt": ChatGPTProvider,
            "claude": ClaudeProvider,
            "gemini": GeminiProvider,
            # "zai": ZaiProvider,  # Commented out for now
            "grok": GrokProvider,
            # "deepseek": DeepSeekProvider,  # Commented out for now
            # "qwen": QwenProvider  # Commented out for now
        }
        
        for provider_name, provider_config in self.config["providers"].items():
            if provider_config.get("api_key"):
                try:
                    provider_class = provider_classes.get(provider_name.lower())
                    if provider_class:
                        provider = provider_class(
                            api_key=provider_config["api_key"],
                            model=provider_config.get("model")
                        )
                        await self.register_provider(provider_name, provider)
                except Exception as e:
                    logger.error(f"Failed to register provider {provider_name}: {str(e)}")
        
        logger.info("Message bus started")
    
    async def stop(self):
        """Stop the message bus"""
        self.running = False

        # Save magic state before shutdown
        if hasattr(self, 'magic') and self.magic:
            await self.magic.save_state()

        # Clean up all providers
        for provider_name in list(self.providers.keys()):
            await self.unregister_provider(provider_name)

        # Clean up persistence
        await self.persistence.cleanup()

        logger.info("Message bus stopped")
    
    async def process_messages(self):
        """Process messages from the queue"""
        while self.running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                # Process message here if needed
                self.message_queue.task_done()
            except asyncio.TimeoutError:
                continue

class AIFrameworkCLI:
    """CLI interface for the AI Framework"""

    def __init__(self):
        self.message_bus = AsyncMessageBus()

    async def start(self):
        """Start the CLI"""
        await self.message_bus.start()
        logger.info("AI Framework CLI started")

    async def stop(self):
        """Stop the CLI"""
        await self.message_bus.stop()
        logger.info("AI Framework CLI stopped")

    async def chat(self, provider: str, message: str, conversation_id: str = "default"):
        """Chat with a specific provider"""
        try:
            response = await self.message_bus.send_message(
                content=message,
                provider_name=provider,
                conversation_id=conversation_id
            )
            print(f"\n[{provider.title()}]: {response}\n")
            return response
        except Exception as e:
            print(f"\nError: {str(e)}\n")
            return None

    
    async def interactive_mode(self, provider: str):
        """Start interactive chat mode"""
        print(f"Starting interactive chat with {provider.title()}. Type 'exit' to quit.")
        conversation_id = f"interactive_{provider}"
        
        while True:
            try:
                user_input = input(f"You ({provider}): ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                await self.chat(provider, user_input, conversation_id)
            except KeyboardInterrupt:
                print("\nExiting...")
                break
    
    async def list_providers(self):
        """List all registered providers"""
        print("\nRegistered providers:")
        for provider_name in self.message_bus.providers:
            print(f"- {provider_name}")
        print()
    
    async def set_api_key(self, provider: str, api_key: str):
        """Set API key for a provider"""
        provider = provider.lower()
        if provider not in self.message_bus.config["providers"]:
            print(f"Unknown provider: {provider}")
            return
        
        self.message_bus.config["providers"][provider]["api_key"] = api_key
        await self.message_bus.save_config()
        print(f"API key for {provider} updated. Please restart the framework to apply changes.")
    
    async def set_default_provider(self, provider: str):
        """Set the default provider"""
        provider = provider.lower()
        if provider not in self.message_bus.providers:
            print(f"Provider not registered: {provider}")
            return
        
        self.message_bus.config["default_provider"] = provider
        await self.message_bus.save_config()
        print(f"Default provider set to: {provider}")
    
    async def show_status(self):
        """Show framework status"""
        print("\n=== AI Framework Status ===")
        print(f"Running: {self.message_bus.running}")
        print(f"Primary Persistence: {type(self.message_bus.persistence.primary).__name__}")
        if self.message_bus.persistence.fallback:
            print(f"Fallback Persistence: {type(self.message_bus.persistence.fallback).__name__}")
        print(f"Registered Providers: {len(self.message_bus.providers)}")
        print(f"Cached Conversations: {len(self.message_bus.conversation_cache)}")
        print("===========================\n")

def main():
    parser = argparse.ArgumentParser(description="Async Message Bus AI Framework with Redis & SQL")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    chat_parser = subparsers.add_parser("chat", help="Send a message to a provider")
    chat_parser.add_argument("provider", help="AI provider to use")
    chat_parser.add_argument("message", help="Message to send")
    chat_parser.add_argument("--conversation-id", default="default", help="Conversation ID")

    interactive_parser = subparsers.add_parser("interactive", help="Start interactive chat mode")
    interactive_parser.add_argument("provider", help="AI provider to use")

    subparsers.add_parser("list", help="List all registered providers")
    subparsers.add_parser("status", help="Show framework status")

    apikey_parser = subparsers.add_parser("set-api-key", help="Set API key for a provider")
    apikey_parser.add_argument("provider", help="AI provider")
    apikey_parser.add_argument("api_key", help="API key")

    default_parser = subparsers.add_parser("set-default", help="Set default provider")
    default_parser.add_argument("provider", help="AI provider")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = AIFrameworkCLI()

    async def run_command():
        await cli.start()
        try:
            if args.command == "chat":
                await cli.chat(args.provider, args.message, args.conversation_id)
            elif args.command == "interactive":
                await cli.interactive_mode(args.provider)
            elif args.command == "list":
                await cli.list_providers()
            elif args.command == "status":
                await cli.show_status()
            elif args.command == "set-api-key":
                await cli.set_api_key(args.provider, args.api_key)
            elif args.command == "set-default":
                await cli.set_default_provider(args.provider)
        finally:
            await cli.stop()

    asyncio.run(run_command())

if __name__ == "__main__":
    main()