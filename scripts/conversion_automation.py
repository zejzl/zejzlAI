#!/usr/bin/env python3
"""
ZEJZL.NET Conversion Automation Cron Job
Processes trial expirations, sends conversion emails, and optimizes onboarding
"""

import asyncio
import logging
import os
from datetime import datetime

# Add project root to path
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.user_management import user_db, conversion_automation

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main conversion automation task"""
    try:
        logger.info("Starting conversion automation task")

        # Initialize database
        await user_db.initialize()

        # Process trial expirations (send conversion emails)
        await conversion_automation.process_trial_expiration()

        # Get conversion analytics
        analytics = await user_db.get_conversion_analytics()
        logger.info(f"Conversion Analytics: {analytics}")

        # Log key metrics
        logger.info(f"Total Users: {analytics['total_users']}")
        logger.info(f"Converted Users: {analytics['converted_users']}")
        logger.info(f"Conversion Rate: {analytics['conversion_rate']}%")
        logger.info(f"Avg Trial Usage: {analytics['avg_trial_usage']} API calls")

        logger.info("Conversion automation task completed successfully")

    except Exception as e:
        logger.error(f"Conversion automation error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
