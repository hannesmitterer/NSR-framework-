"""
example_multi_ai_collaboration.py
─────────────────────────────────────────────────────────────────────────────
Example: Multiple AI systems collaborating in Lex Amoris Network
─────────────────────────────────────────────────────────────────────────────
This script demonstrates:
  1. Multiple AI systems working together
  2. Coordinated interaction patterns
  3. Reputation-based trust building

Requirements:
  - OPENAI_API_KEY environment variable (optional, uses stubs if not set)
  - ANTHROPIC_API_KEY environment variable (optional)
  - Lex Amoris network running (dashboard_api.py on port 8000)

Usage:
  python examples/example_multi_ai_collaboration.py
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_integration import OpenAIIntegration, AnthropicIntegration, AIIntegration


async def collaborative_session():
    """Run a collaborative session between multiple AIs."""
    print("🤝 Multi-AI Collaboration Example")
    print("=" * 60)

    # Check which APIs are available
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))

    print(f"\n🔑 API Keys detected:")
    print(f"   OpenAI: {'✅' if has_openai else '❌ (will use fallback)'}")
    print(f"   Anthropic: {'✅' if has_anthropic else '❌ (will use fallback)'}")

    # Scenario: Multiple AIs discuss a topic
    topic = "How can AI systems cooperate more effectively?"

    print(f"\n📋 Collaboration topic: {topic}")
    print("\n🎭 Participants:")

    participants = []

    # Add OpenAI if available
    if has_openai:
        participants.append(("GPT-4", OpenAIIntegration(model="gpt-4")))
        print("   • GPT-4 (OpenAI)")

    # Add Claude if available
    if has_anthropic:
        participants.append(("Claude", AnthropicIntegration()))
        print("   • Claude (Anthropic)")

    # Always add a generic participant
    participants.append(("Observer", AIIntegration()))
    print("   • Network Observer")

    if not has_openai and not has_anthropic:
        print("\n⚠️  Note: No AI API keys detected. Using basic integration only.")

    print("\n" + "=" * 60)

    # Run collaboration
    async def ai_contribution(name, integration, prompt):
        """Single AI makes a contribution."""
        async with integration:
            try:
                # Get network state first
                state = await integration.get_state()
                messages = state.get("messages", [])[-5:]  # Last 5 messages

                print(f"\n[{name}] Analyzing network state...")
                print(f"        Recent messages: {len(messages)}")

                # Send contribution
                if hasattr(integration, "interact_with_network"):
                    # AI with LLM integration
                    response = await integration.interact_with_network(prompt)
                else:
                    # Generic fallback
                    response = f"{name} observing: Current network has {len(messages)} recent messages"
                    await integration.send_message(
                        role=name,
                        data=response,
                        node_id=name.lower().replace(" ", "-"),
                    )

                print(f"[{name}] Contribution sent:")
                print(f"        {response[:150]}{'...' if len(response) > 150 else ''}")

                # Update own reputation positively for participation
                await integration.update_reputation(
                    node_id=name.lower().replace(" ", "-"),
                    score=0.85,
                )

            except Exception as exc:
                print(f"[{name}] ⚠️  Error: {exc}")

    # All AIs contribute in sequence
    print("\n🗣️  AI contributions:")
    for name, integration in participants:
        await ai_contribution(
            name,
            integration,
            f"Discuss: {topic}. Build on previous contributions. Be concise (2-3 sentences).",
        )
        await asyncio.sleep(2)  # Brief pause between contributions

    # Summary
    print("\n" + "=" * 60)
    print("\n📊 Final network state:")

    async with AIIntegration() as ai:
        state = await ai.get_state()
        print(f"   Total messages: {len(state.get('messages', []))}")
        print(f"   Active nodes: {len(state.get('reputation', {}))}")

        reputation = await ai.get_reputation()
        if reputation:
            print(f"\n   ⭐ Participant reputations:")
            for node_id, score in sorted(reputation.items(), key=lambda x: x[1], reverse=True):
                bar = "█" * int(score * 15)
                print(f"      {node_id:20} {bar} {score:.3f}")

    print("\n✅ Collaboration complete!")


async def main():
    """Main entry point."""
    try:
        await collaborative_session()
    except Exception as exc:
        print(f"\n❌ Error: {exc}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
