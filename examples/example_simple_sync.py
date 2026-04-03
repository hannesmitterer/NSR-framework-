"""
example_simple_sync.py
─────────────────────────────────────────────────────────────────────────────
Example: Simple synchronous integration with Lex Amoris Network
─────────────────────────────────────────────────────────────────────────────
This script demonstrates the simplest way to interact with the network
using synchronous (blocking) calls - perfect for scripts and simple bots.

Requirements:
  - Lex Amoris network running (dashboard_api.py on port 8000)

Usage:
  python examples/example_simple_sync.py
"""

import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_integration import SyncAIIntegration


def main():
    """Simple synchronous integration example."""
    print("🔌 Simple Synchronous Integration Example")
    print("=" * 60)

    # Initialize integration (defaults to localhost:8000)
    ai = SyncAIIntegration(api_base_url="http://localhost:8000")

    try:
        # 1. Get current network state
        print("\n📊 Fetching network state...")
        state = ai.get_state()
        print(f"   Messages: {len(state.get('messages', []))}")
        print(f"   Nodes: {len(state.get('reputation', {}))}")

        # 2. Send a simple message
        print("\n📤 Sending message to network...")
        result = ai.send_message(
            role="SimpleBot",
            data="Hello from a simple synchronous client!",
            node_id="simple-bot-001",
        )
        print(f"   Response: {result}")

        # 3. Add a memory
        print("\n💾 Adding memory entry...")
        result = ai.add_memory(
            text="Simple bot connected and sent greeting",
            role="SimpleBot",
            trust=0.7,
        )
        print(f"   Response: {result}")

        # 4. Update reputation (example)
        print("\n⭐ Updating own reputation...")
        result = ai.update_reputation(
            node_id="simple-bot-001",
            score=0.75,
        )
        print(f"   Response: {result}")

        # 5. Monitor network for a few seconds
        print("\n👀 Monitoring network for 10 seconds...")
        for i in range(5):
            time.sleep(2)
            state = ai.get_state()
            msg_count = len(state.get("messages", []))
            print(f"   [{i+1}/5] Total messages: {msg_count}")

        print("\n✅ Integration complete!")

    except Exception as exc:
        print(f"\n❌ Error: {exc}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
