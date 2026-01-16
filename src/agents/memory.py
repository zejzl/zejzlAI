# src/agents/memory.py
import asyncio
import logging
from typing import Any, Dict, List

logger = logging.getLogger("MemoryAgent")


class MemoryAgent:
    """
    Memory Agent for Pantheon 9-Agent System.
    Responsible for storing and recalling state, observations, and execution history.
    """

    def __init__(self):
        self.name = "Memory"
        self.memory_store: List[Dict[str, Any]] = []

    async def store(self, event: Dict[str, Any]):
        """
        Store an event in memory (stub).
        """
        self.memory_store.append(event)
        logger.info(f"[{self.name}] Stored event: {event}")

    async def recall(self, filter_fn=None) -> List[Dict[str, Any]]:
        """
        Recall events from memory. Optionally apply a filter function.
        """
        recalled = [e for e in self.memory_store if filter_fn(e)] if filter_fn else self.memory_store
        logger.info(f"[{self.name}] Recalled {len(recalled)} events")
        return recalled
