#!/usr/bin/env python3
"""
Test script for Performance Monitoring in ZEJZL.NET
"""

import asyncio
import sys
import os
import time

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.performance import metrics_collector, cache, record_metric, get_performance_summary

async def demo():
    """Demonstrate performance monitoring"""
    print("Performance Monitoring Demo")

    # Start metrics collection
    await metrics_collector.start_collection()
    print("+ Metrics collection started")

    # Record test metrics
    print("\nRecording test metrics...")
    for i in range(5):
        record_metric("demo_counter", i * 20)
        record_metric("demo_response_time", 100 + i * 50)
        await asyncio.sleep(0.1)

    print("+ Recorded test metrics")

    # Test caching
    print("\nTesting caching...")
    test_data = {"message": "cached data", "value": 42}
    await cache.set("test_key", test_data, ttl_seconds=300)
    cached = await cache.get("test_key")
    print(f"+ Cache test: {cached is not None}")

    # Get summary
    summary = get_performance_summary()
    print(f"+ Metrics: {len(summary['metrics']['metrics'])}")
    print(f"+ Cache items: {summary['cache_stats']['memory_items']}")

    # Stop collection
    metrics_collector.stop_collection()
    print("\n+ Demo complete!")

if __name__ == "__main__":
    asyncio.run(demo())