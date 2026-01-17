#!/usr/bin/env python3
"""
ZEJZL.NET Debug CLI Tool
Command-line interface for debugging and monitoring the system
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.logging_debug import debug_monitor, logger, setup_logging
from ai_framework import AsyncMessageBus
from base import get_ai_provider_bus
from telemetry import get_telemetry

class DebugCLI:
    """Command-line interface for debugging ZEJZL.NET"""

    def __init__(self):
        self.bus = None
        self.telemetry = None

    async def initialize(self):
        """Initialize the debug CLI"""
        try:
            self.bus = await get_bus()
            self.telemetry = get_telemetry()
            logger.info("Debug CLI initialized")
        except Exception as e:
            logger.warning(f"Could not initialize full system: {e}")

    async def show_status(self):
        """Show system status"""
        print("🔍 ZEJZL.NET System Status")
        print("=" * 40)

        if self.bus:
            print(f"✅ Message Bus: Connected")
            print(f"📊 Providers: {len(self.bus.providers)} registered")
            for name, provider in self.bus.providers.items():
                status = "✅ Active" if hasattr(provider, 'session') and provider.session else "❌ Inactive"
                print(f"   • {name}: {status}")
        else:
            print("❌ Message Bus: Not connected")

        if hasattr(self.bus, 'magic') and self.bus.magic:
            magic = self.bus.magic
            print(f"🔮 Magic System: Energy {magic.energy_level}/{magic.max_energy}")
            print(f"   • Circuit Breakers: {len(magic.circuit_breakers)}")
            print(f"   • Healing History: {len(magic.healing_history)} records")
        else:
            print("❌ Magic System: Not available")

        print(f"📈 Active Requests: {len(debug_monitor.active_requests)}")
        print(f"⚡ Performance Entries: {len(debug_monitor.performance_history)}")

    async def show_logs(self, lines=20, level=None):
        """Show recent logs"""
        print(f"📝 Recent Debug Logs (last {lines} entries)")
        print("=" * 50)

        log_dir = Path.home() / ".zejzl" / "logs"
        log_files = {
            "debug": log_dir / "debug.log",
            "performance": log_dir / "performance.log",
            "main": log_dir / "zejzl.log"
        }

        target_file = log_files.get(level, log_files["debug"])

        if target_file.exists():
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:]

                    for i, line in enumerate(recent_lines, 1):
                        try:
                            # Try to parse as JSON
                            log_entry = json.loads(line.strip())
                            timestamp = log_entry.get('timestamp', 'Unknown')[:19]
                            level = log_entry.get('level', 'UNKNOWN')
                            message = log_entry.get('message', 'No message')
                            module = log_entry.get('module', 'unknown')

                            print(f"{i:2d}. [{timestamp}] {level:8} {module:12} {message}")
                        except json.JSONDecodeError:
                            # Plain text log
                            print(f"{i:2d}. {line.strip()}")
            except Exception as e:
                print(f"❌ Error reading logs: {e}")
        else:
            print(f"❌ Log file not found: {target_file}")

    async def show_performance(self):
        """Show performance metrics"""
        print("⚡ Performance Metrics")
        print("=" * 30)

        if not debug_monitor.performance_history:
            print("No performance data available")
            return

        # Calculate statistics
        operations = {}
        total_time = 0
        total_calls = len(debug_monitor.performance_history)

        for entry in debug_monitor.performance_history:
            op = entry["operation"]
            duration = entry["duration"]
            total_time += duration

            if op not in operations:
                operations[op] = {"count": 0, "total_time": 0, "min_time": float('inf'), "max_time": 0}

            operations[op]["count"] += 1
            operations[op]["total_time"] += duration
            operations[op]["min_time"] = min(operations[op]["min_time"], duration)
            operations[op]["max_time"] = max(operations[op]["max_time"], duration)

        print(f"Total Calls: {total_calls}")
        print(".3f")
        print(".3f")
        print()

        # Show top operations
        print("Top Operations by Frequency:")
        sorted_ops = sorted(operations.items(), key=lambda x: x[1]["count"], reverse=True)
        for op, stats in sorted_ops[:10]:
            avg_time = stats["total_time"] / stats["count"]
            print(".3f"
                  f"(min: {stats['min_time']:.3f}s, max: {stats['max_time']:.3f}s)")

    async def create_snapshot(self):
        """Create and display system snapshot"""
        print("📊 Creating System Snapshot...")
        print("=" * 35)

        snapshot = await debug_monitor.create_snapshot(self.bus)

        print(f"Timestamp: {snapshot.timestamp}")
        print()

        print("🔧 System Info:")
        sys_info = snapshot.system_info
        print(f"   Platform: {sys_info.get('platform', 'Unknown')}")
        print(f"   Python: {sys_info.get('python_version', 'Unknown')}")
        print(f"   CPU Cores: {sys_info.get('cpu_count', 'Unknown')}")
        memory = sys_info.get('memory', {})
        if memory:
            print(".1f")
        print()

        print("🤖 Agent States:")
        for name, state in snapshot.agent_states.items():
            status = state.get('status', 'unknown')
            model = state.get('model', 'unknown')
            print(f"   • {name}: {status} ({model})")
        print()

        print("🔮 Magic State:")
        magic = snapshot.magic_state
        if magic:
            print(f"   Energy: {magic.get('energy_level', 0)}/{magic.get('max_energy', 100)}")
            print(f"   Circuit Breakers: {magic.get('circuit_breakers', 0)}")
            print(f"   Healing Records: {magic.get('healing_history_count', 0)}")
        else:
            print("   No magic system data available")
        print()

        print("📈 Performance:")
        perf = snapshot.performance_metrics
        print(f"   Total Requests: {perf.get('total_requests', 0)}")
        print(".3f")
        print(".1f")
        print()

        print("✅ Snapshot created and logged")

    async def clear_logs(self):
        """Clear debug logs"""
        print("🧹 Clearing Debug Logs...")
        log_dir = Path.home() / ".zejzl" / "logs"

        cleared = []
        for log_file in ["debug.log", "performance.log", "zejzl.log"]:
            file_path = log_dir / log_file
            if file_path.exists():
                try:
                    file_path.write_text("")
                    cleared.append(log_file)
                except Exception as e:
                    print(f"❌ Failed to clear {log_file}: {e}")

        if cleared:
            print(f"✅ Cleared logs: {', '.join(cleared)}")
        else:
            print("ℹ️  No logs found to clear")

    async def set_log_level(self, level: str):
        """Set logging level"""
        import logging
        try:
            numeric_level = getattr(logging, level.upper(), logging.INFO)
            logging.getLogger().setLevel(numeric_level)
            logger.info(f"Log level set to {level}")
            print(f"✅ Log level set to {level}")
        except Exception as e:
            print(f"❌ Failed to set log level: {e}")

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="ZEJZL.NET Debug CLI")
    parser.add_argument('command', choices=['status', 'logs', 'performance', 'snapshot', 'clear-logs', 'set-level'],
                       help='Command to execute')
    parser.add_argument('--lines', '-n', type=int, default=20, help='Number of lines for logs')
    parser.add_argument('--level', choices=['debug', 'performance', 'main'], default='debug',
                       help='Log level to show')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level')

    args = parser.parse_args()

    # Setup logging
    setup_logging("INFO", pretty=True)

    # Initialize debug CLI
    cli = DebugCLI()
    await cli.initialize()

    # Execute command
    if args.command == 'status':
        await cli.show_status()
    elif args.command == 'logs':
        await cli.show_logs(args.lines, args.level)
    elif args.command == 'performance':
        await cli.show_performance()
    elif args.command == 'snapshot':
        await cli.create_snapshot()
    elif args.command == 'clear-logs':
        await cli.clear_logs()
    elif args.command == 'set-level':
        if args.log_level:
            await cli.set_log_level(args.log_level)
        else:
            print("❌ Please specify --log-level")

if __name__ == "__main__":
    asyncio.run(main())