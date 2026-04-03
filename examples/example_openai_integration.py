"""
example_openai_integration.py
─────────────────────────────────────────────────────────────────────────────
Example: Integrate OpenAI GPT with Lex Amoris Network
─────────────────────────────────────────────────────────────────────────────
This script demonstrates how to:
  1. Query the current network state
  2. Use GPT to generate contextual responses
  3. Send messages back to the network
  4. Monitor network activity

Requirements:
  - OPENAI_API_KEY environment variable set
  - Lex Amoris network running (dashboard_api.py on port 8000)

Usage:
  python examples/example_openai_integration.py
"""

import asyncio
import os
import sys

# Add parent directory to path to import ai_integration
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_integration import OpenAIIntegration


async def main():
    """Main integration loop."""
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return

    print("🤖 OpenAI GPT Integration with Lex Amoris Network")
    print("=" * 60)

    # Initialize integration
    async with OpenAIIntegration(model="gpt-4") as ai:
        print("✅ Connected to Lex Amoris API")

        # Get initial state
        print("\n📊 Fetching current network state...")
        state = await ai.get_state()
        print(f"   Messages: {len(state.get('messages', []))}")
        print(f"   Nodes: {len(state.get('reputation', {}))}")
        print(f"   Memory entries: {len(state.get('memory', []))}")
        print(f"   Chain length: {state.get('chain', {}).get('length', 0)}")

        # Show recent activity
        recent_messages = state.get("messages", [])[-3:]
        if recent_messages:
            print("\n💬 Recent network activity:")
            for msg in recent_messages:
                role = msg.get("role", "unknown")
                data = msg.get("data", "")[:80]
                print(f"   [{role}] {data}...")

        # Let GPT interact with the network
        print("\n🧠 Querying GPT-4 for network interaction...")
        system_prompt = """
        You are collaborating with a multi-agent AI network called Lex Amoris.
        The network follows cooperative principles and aims to benefit all participants.
        
        Based on recent network activity, provide a constructive, helpful contribution.
        Keep your response concise (2-3 sentences).
        """

        try:
            response = await ai.interact_with_network(system_prompt)
            print(f"\n📤 GPT-4 response sent to network:")
            print(f"   {response}")

        except Exception as exc:
            print(f"❌ Error during GPT interaction: {exc}")
            return

        # Monitor reputation
        print("\n⭐ Current node reputations:")
        reputation = await ai.get_reputation()
        if reputation:
            for node_id, score in sorted(reputation.items(), key=lambda x: x[1], reverse=True):
                bar = "█" * int(score * 20)
                print(f"   {node_id:15} {bar} {score:.3f}")
        else:
            print("   No reputation data available yet")

        # Add a memory
        print("\n💾 Adding interaction memory...")
        await ai.add_memory(
            text="OpenAI GPT-4 integration successfully established",
            role="OpenAI-GPT",
            trust=0.8,
        )
        print("   Memory added successfully")

    print("\n✅ Integration complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as exc:
        print(f"\n❌ Fatal error: {exc}")
        import traceback
        traceback.print_exc()
