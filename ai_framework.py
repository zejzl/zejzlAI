#!/usr/bin/env python3
"""
Async Message Bus AI Framework with Redis & SQL Fallback
Supports: Zai, ChatGPT, Claude, Grok, Gemini, DeepSeek, and Qwen
Configuration: TOML format (Toon-like)
Persistence: Redis (primary) + SQLite (fallback)
"""

# --- 1. Future Imports (Must be first) ---
from __future__ import annotations

# --- 2. Standard Library Imports ---
import asyncio
import logging
import os
import sys
import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
from pathlib import Path
import pickle
import hashlib

# --- 3. Third-Party Library Imports ---
import aiohttp
import toml
import redis.asyncio as aioredis
import aiosqlite

# --- 4. Local Application Imports ---
from dotenv import load_dotenv

# (The sys.path fix you added)
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

# --- USE ABSOLUTE IMPORTS HERE ---
# These point to the full path from the project root.
from src.agents.observer import ObserverAgent
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
        return "Zai"
    
    @property
    def default_model(self) -> str:
        return "zai-1"
    
    async def initialize(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def generate_response(self, message: str, history: List[Dict] = None) -> str:
        await asyncio.sleep(1)
        return f"Zai response to: {message}"
    
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
    
    async def generate_response(self, message: str, history: List[Dict] = None) -> str:
        await asyncio.sleep(1)
        return f"Grok response to: {message}"
    
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
    
    async def generate_response(self, message: str, history: List[Dict] = None) -> str:
        await asyncio.sleep(1)
        return f"DeepSeek response to: {message}"
    
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
    
    async def generate_response(self, message: str, history: List[Dict] = None) -> str:
        await asyncio.sleep(1)
        return f"Qwen response to: {message}"
    
    async def cleanup(self):
        if self.session:
            await self.session.close()

class AsyncMessageBus:
    """Async message bus for handling AI provider requests with hybrid persistence"""
    
    def __init__(self):
        self.providers: Dict[str, AIProvider] = {}
        self.message_queue = asyncio.Queue()
        self.response_handlers: Dict[str, Callable] = {}
        self.conversation_cache: Dict[str, List[Dict]] = {}
        self.running = False
        self.persistence = HybridPersistence()
        self.config = None
    
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
    
    async def send_message(self, content: str, provider_name: str = None, 
                          conversation_id: str = "default") -> str:
        """Send a message to a specific provider and return the response"""
        provider_name = provider_name or self.config.get("default_provider", "chatgpt")
        provider_name = provider_name.lower()
        
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not registered")
        
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
            response = await provider.generate_response(content, history)
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
            
            logger.info(f"Response from {provider_name} in {response_time:.2f}s")
            return response
            
        except Exception as e:
            message.error = str(e)
            await self.persistence.save_message(message)
            logger.error(f"Error getting response from {provider_name}: {str(e)}")
            raise
    
    async def start(self):
        """Start the message bus"""
        self.running = True
        
        # Initialize persistence
        await self.persistence.initialize()
        
        # Load configuration
        self.config = await self.load_config()
        
        # Register providers based on config
        provider_classes = {
            "chatgpt": ChatGPTProvider,
            "claude": ClaudeProvider,
            "gemini": GeminiProvider,
            "zai": ZaiProvider,
            "grok": GrokProvider,
            "deepseek": DeepSeekProvider,
            "qwen": QwenProvider
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