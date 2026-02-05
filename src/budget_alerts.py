#!/usr/bin/env python3
"""
Budget Alert System for zejzl.net Pantheon

Monitors token usage and sends alerts to Discord when thresholds are reached:
- 80% usage: WARNING (yellow)
- 90% usage: CRITICAL (red)
- 100% usage: EXHAUSTED (block new requests)

Usage:
    from src.budget_alerts import BudgetAlertManager
    
    alerts = BudgetAlertManager(discord_webhook_url="https://...")
    await alerts.check_and_notify(task_id, tokens_used, budget_limit)
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import aiohttp

logger = logging.getLogger(__name__)

# Alert thresholds
THRESHOLD_WARNING = 0.80   # 80%
THRESHOLD_CRITICAL = 0.90  # 90%
THRESHOLD_EXHAUSTED = 1.00 # 100%


class BudgetAlertManager:
    """
    Manages budget alerts and Discord notifications
    
    Features:
    - Threshold-based alerts (80%, 90%, 100%)
    - Discord webhook integration
    - Alert deduplication (don't spam same alert)
    - Alert history tracking
    """
    
    def __init__(
        self,
        discord_webhook_url: Optional[str] = None,
        data_dir: Path = Path("skills/swarm-orchestrator/data")
    ):
        """
        Initialize Budget Alert Manager
        
        Args:
            discord_webhook_url: Discord webhook URL for notifications
            data_dir: Directory for alert history storage
        """
        self.webhook_url = discord_webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.alert_file = self.data_dir / "budget_alerts.json"
        self.alert_history = self._load_alert_history()
        
        logger.info("BudgetAlertManager initialized")
    
    def _load_alert_history(self) -> Dict[str, Any]:
        """Load alert history from file"""
        if self.alert_file.exists():
            try:
                with open(self.alert_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading alert history: {e}")
        
        return {
            "alerts_sent": {},
            "total_alerts": 0,
            "last_alert": None
        }
    
    def _save_alert_history(self):
        """Save alert history to file"""
        try:
            with open(self.alert_file, 'w', encoding='utf-8') as f:
                json.dump(self.alert_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving alert history: {e}")
    
    def calculate_percentage(self, used: int, limit: int) -> float:
        """Calculate usage percentage"""
        if limit == 0:
            return 0.0
        return (used / limit) * 100
    
    def get_alert_level(self, percentage: float) -> Optional[str]:
        """
        Determine alert level based on percentage
        
        Returns:
            "WARNING", "CRITICAL", "EXHAUSTED", or None
        """
        if percentage >= 100:
            return "EXHAUSTED"
        elif percentage >= 90:
            return "CRITICAL"
        elif percentage >= 80:
            return "WARNING"
        return None
    
    def should_send_alert(self, task_id: str, alert_level: str) -> bool:
        """
        Check if alert should be sent (deduplication)
        
        Only send each alert level once per task to avoid spam
        """
        task_alerts = self.alert_history["alerts_sent"].get(task_id, [])
        return alert_level not in task_alerts
    
    def mark_alert_sent(self, task_id: str, alert_level: str):
        """Mark alert as sent for this task"""
        if task_id not in self.alert_history["alerts_sent"]:
            self.alert_history["alerts_sent"][task_id] = []
        
        if alert_level not in self.alert_history["alerts_sent"][task_id]:
            self.alert_history["alerts_sent"][task_id].append(alert_level)
            self.alert_history["total_alerts"] += 1
            self.alert_history["last_alert"] = datetime.now().isoformat()
            self._save_alert_history()
    
    async def send_discord_notification(
        self,
        task_id: str,
        tokens_used: int,
        budget_limit: int,
        percentage: float,
        alert_level: str
    ):
        """
        Send Discord webhook notification
        
        Args:
            task_id: Task identifier
            tokens_used: Tokens consumed
            budget_limit: Budget limit
            percentage: Usage percentage
            alert_level: WARNING, CRITICAL, or EXHAUSTED
        """
        if not self.webhook_url:
            logger.warning("Discord webhook URL not configured - skipping notification")
            return
        
        # Determine emoji and color based on alert level
        emoji_map = {
            "WARNING": "⚠️",
            "CRITICAL": "🚨",
            "EXHAUSTED": "🛑"
        }
        
        color_map = {
            "WARNING": 16776960,   # Yellow
            "CRITICAL": 16711680,  # Red
            "EXHAUSTED": 0         # Black
        }
        
        emoji = emoji_map.get(alert_level, "⚠️")
        color = color_map.get(alert_level, 16776960)
        
        # Create Discord embed
        embed = {
            "title": f"{emoji} Budget Alert: {alert_level}",
            "description": f"Task **{task_id}** has reached {percentage:.1f}% of budget",
            "color": color,
            "fields": [
                {
                    "name": "Tokens Used",
                    "value": f"{tokens_used:,}",
                    "inline": True
                },
                {
                    "name": "Budget Limit",
                    "value": f"{budget_limit:,}",
                    "inline": True
                },
                {
                    "name": "Remaining",
                    "value": f"{(budget_limit - tokens_used):,}",
                    "inline": True
                },
                {
                    "name": "Percentage",
                    "value": f"{percentage:.1f}%",
                    "inline": True
                },
                {
                    "name": "Status",
                    "value": alert_level,
                    "inline": True
                },
                {
                    "name": "Dashboard",
                    "value": "[View Dashboard](http://localhost:8000/blackboard)",
                    "inline": True
                }
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "ZEJZL.NET Budget Monitoring"
            }
        }
        
        # Add action recommendation
        if alert_level == "EXHAUSTED":
            embed["fields"].append({
                "name": "⚠️ Action Required",
                "value": "Budget exhausted - new requests will be blocked until budget is increased",
                "inline": False
            })
        elif alert_level == "CRITICAL":
            embed["fields"].append({
                "name": "⚠️ Action Recommended",
                "value": "Budget nearly exhausted - consider increasing limit or optimizing task",
                "inline": False
            })
        
        payload = {
            "embeds": [embed]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    if resp.status == 204:
                        logger.info(f"Discord notification sent: {alert_level} for {task_id}")
                    else:
                        logger.error(f"Discord notification failed: {resp.status}")
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
    
    async def check_and_notify(
        self,
        task_id: str,
        tokens_used: int,
        budget_limit: int
    ) -> Dict[str, Any]:
        """
        Check budget usage and send alerts if thresholds crossed
        
        Args:
            task_id: Task identifier
            tokens_used: Current token usage
            budget_limit: Budget limit
        
        Returns:
            Dict with alert status and details
        """
        percentage = self.calculate_percentage(tokens_used, budget_limit)
        alert_level = self.get_alert_level(percentage)
        
        result = {
            "task_id": task_id,
            "tokens_used": tokens_used,
            "budget_limit": budget_limit,
            "percentage": percentage,
            "alert_level": alert_level,
            "alert_sent": False
        }
        
        if alert_level and self.should_send_alert(task_id, alert_level):
            # Send alert
            await self.send_discord_notification(
                task_id,
                tokens_used,
                budget_limit,
                percentage,
                alert_level
            )
            
            self.mark_alert_sent(task_id, alert_level)
            result["alert_sent"] = True
            
            logger.info(
                f"Budget alert sent: {task_id} at {percentage:.1f}% "
                f"({tokens_used:,}/{budget_limit:,}) - {alert_level}"
            )
        
        return result
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of all alerts"""
        return {
            "total_alerts_sent": self.alert_history["total_alerts"],
            "last_alert_time": self.alert_history["last_alert"],
            "tasks_with_alerts": len(self.alert_history["alerts_sent"]),
            "alert_breakdown": {
                task_id: alerts
                for task_id, alerts in self.alert_history["alerts_sent"].items()
            }
        }


# Convenience function for quick alerts
async def send_budget_alert(
    task_id: str,
    tokens_used: int,
    budget_limit: int,
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Quick function to check budget and send alert if needed
    
    Usage:
        result = await send_budget_alert("task_123", 8500, 10000)
        if result["alert_sent"]:
            print(f"Alert sent: {result['alert_level']}")
    """
    manager = BudgetAlertManager(discord_webhook_url=webhook_url)
    return await manager.check_and_notify(task_id, tokens_used, budget_limit)
