"""
example_event_subscriber.py
─────────────────────────────────────────────────────────────────────────────
Example: Subscribe to real-time network events via WebSocket
─────────────────────────────────────────────────────────────────────────────
This script demonstrates how to:
  1. Subscribe to network events in real-time
  2. React to different event types (messages, reputation updates, etc.)
  3. Implement custom event handlers

Requirements:
  - Lex Amoris network running (dashboard_api.py on port 8000)

Usage:
  python examples/example_event_subscriber.py
"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_integration import NetworkEventSubscriber, AIIntegration


# Event handlers
async def on_message(payload):
    """Handle incoming messages."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    role = payload.get("role", "unknown")
    data = payload.get("data", "")[:100]
    node_id = payload.get("node_id", "N/A")

    print(f"[{timestamp}] 💬 MESSAGE from {role} (node: {node_id})")
    print(f"           {data}")


async def on_reputation(payload):
    """Handle reputation updates."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] ⭐ REPUTATION UPDATE")
    for node_id, score in payload.items():
        print(f"           {node_id}: {score:.3f}")


async def on_memory(payload):
    """Handle memory additions."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    text = payload.get("text", "")[:80]
    role = payload.get("role", "unknown")
    trust = payload.get("trust", 0.0)

    print(f"[{timestamp}] 💾 MEMORY added by {role} (trust: {trust:.2f})")
    print(f"           {text}")


async def on_snapshot(payload):
    """Handle initial snapshot."""
    print("\n📸 SNAPSHOT received:")
    print(f"   Messages: {len(payload.get('messages', []))}")
    print(f"   Reputation entries: {len(payload.get('reputation', {}))}")
    print(f"   Memory entries: {len(payload.get('memory', []))}")
    print(f"   Chain length: {payload.get('chain', {}).get('length', 0)}")
    print()


async def main():
    """Main event subscriber loop."""
    print("🔔 Network Event Subscriber Example")
    print("=" * 60)
    print("Connecting to Lex Amoris WebSocket...")
    print("(Press Ctrl+C to stop)\n")

    # Create subscriber
    subscriber = NetworkEventSubscriber(ws_url="ws://localhost:8000/ws")

    # Register event handlers
    subscriber.on("message", on_message)
    subscriber.on("reputation", on_reputation)
    subscriber.on("memory", on_memory)
    subscriber.on("snapshot", on_snapshot)

    # Optional: Send periodic messages to generate activity
    async def send_periodic_messages():
        """Send a message every 30 seconds to demonstrate the flow."""
        await asyncio.sleep(5)  # Wait for initial connection

        async with AIIntegration() as ai:
            while True:
                try:
                    await ai.send_message(
                        role="EventMonitor",
                        data=f"Heartbeat at {datetime.now().strftime('%H:%M:%S')}",
                        node_id="event-monitor",
                    )
                    await asyncio.sleep(30)
                except Exception:  # noqa: BLE001
                    break

    # Run subscriber and periodic sender concurrently
    try:
        await asyncio.gather(
            subscriber.subscribe(),
            send_periodic_messages(),
        )
    except asyncio.CancelledError:
        print("\n\n⚠️  Shutting down gracefully...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✅ Subscriber stopped by user")
