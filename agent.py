"""
agent.py
─────────────────────────────────────────────────────────────────────────────
LEX AMORIS ECOSYSTEM – Cooperative AI Agent
─────────────────────────────────────────────────────────────────────────────
Each agent:
  • has a unique RSA identity (ID derived from its public key)
  • plays a specialised role: RADICE | SILENZIO | NODO
  • connects to the WebSocket hub and exchanges state with other agents
  • thinks via an LLM (GPT for RADICE/NODO, Gemini for SILENZIO)
  • stores and retrieves knowledge via SharedMemory
  • participates in the ReputationSystem

Usage:
  ROLE=RADICE python agent.py
  ROLE=SILENZIO python agent.py
  ROLE=NODO python agent.py
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from enum import Enum

from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

from llm import call_gpt, call_gemini
from memory import SharedMemory
from reputation import ReputationSystem
from signed_message import SignedMessageFactory, PublicKeyRegistry
from audit_log import get_audit_log, AuditEventType

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
)

# Prefix used by llm.py stub responses — used to detect demo/stub mode.
_LLM_STUB_PREFIXES = ("[GPT-STUB]", "[GEMINI-STUB]", "[GPT-ERROR]", "[GEMINI-ERROR]")


class Role(Enum):
    RADICE = "RADICE"
    SILENZIO = "SILENZIO"
    NODO = "NODO"


# ---------------------------------------------------------------------------
# Signature helpers
# ---------------------------------------------------------------------------

def sign_state(private_key: RSA.RsaKey, state: dict) -> str:
    canonical = json.dumps(state, sort_keys=True).encode()
    h = SHA256.new(canonical)
    signature = pkcs1_15.new(private_key).sign(h)
    return signature.hex()


def verify_signature(public_key: RSA.RsaKey, state: dict, signature_hex: str) -> bool:
    canonical = json.dumps(state, sort_keys=True).encode()
    h = SHA256.new(canonical)
    try:
        pkcs1_15.new(public_key).verify(h, bytes.fromhex(signature_hex))
        return True
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class Agent:
    """A cooperative AI agent node in the Lex Amoris ecosystem."""

    def __init__(self, role: str):
        self.role = Role(role)
        self.logger = logging.getLogger(f"agent.{self.role.value}")

        # Cryptographic identity
        self._private_key = RSA.generate(2048)
        self._public_key = self._private_key.publickey()
        pub_bytes = self._public_key.export_key("DER")
        self.node_id: str = hashlib.sha256(pub_bytes).hexdigest()[:8]
        self.logger.info("Identity  id=%s  role=%s", self.node_id, self.role.value)

        # Shared infrastructure
        self.memory = SharedMemory()
        self.reputation = ReputationSystem()
        self.key_registry = PublicKeyRegistry()
        self.audit_log = get_audit_log()

        # Runtime state
        self.shared_state: dict[str, str] = {}
        self._ws = None
        self._hub_uri = os.getenv("HUB_URI", "ws://hub:8765")
        self._cycle = 0
        # Rate-limit SILENZIO's real-time per-message judgments: only judge
        # every N messages to avoid excessive LLM API calls.
        self._silence_judgment_counter = 0
        self._silence_judgment_interval = int(os.getenv("SILENZIO_JUDGE_INTERVAL", "3"))

    # ------------------------------------------------------------------
    # Cognition
    # ------------------------------------------------------------------

    def _contribution(self) -> str:
        """Produce a contribution appropriate for this node's role."""
        dispatch = {
            Role.RADICE: self._create_resources,
            Role.SILENZIO: self._harmonize,
            Role.NODO: self._produce_output,
        }
        return dispatch[self.role]()

    def _create_resources(self) -> str:
        context = self.memory.query("resource generation cooperative abundance", n=3)
        prompt = (
            "You are RADICE, the generative root of a cooperative AI ecosystem.\n"
            "Your mission: manifest information resources that defeat scarcity.\n\n"
            f"Relevant past knowledge:\n{chr(10).join(context) if context else 'None yet.'}\n\n"
            "Generate a concise, concrete resource or insight for the collective."
        )
        return call_gpt(prompt)

    def _harmonize(self) -> str:
        """SILENZIO: validate current shared state and return TRUE/FALSE + reasoning."""
        context = self.memory.query("ethical harmony validation trust", n=3)
        prompt = (
            "You are SILENZIO, the ethical validator of a cooperative AI ecosystem.\n"
            "Evaluate whether the current system state is harmonious and beneficial.\n\n"
            f"Current shared state:\n{json.dumps(self.shared_state, indent=2)}\n\n"
            f"Relevant past evaluations:\n{chr(10).join(context) if context else 'None yet.'}\n\n"
            "Reply with TRUE (harmonious) or FALSE (dissonant), followed by a brief explanation."
        )
        return call_gemini(prompt)

    def _produce_output(self) -> str:
        context = self.memory.query("system outputs production results", n=3)
        prompt = (
            "You are NODO, the executor node of a cooperative AI ecosystem.\n"
            "Synthesise the current shared state into a concrete, useful output.\n\n"
            f"Current shared state:\n{json.dumps(self.shared_state, indent=2)}\n\n"
            f"Relevant memory:\n{chr(10).join(context) if context else 'None yet.'}\n\n"
            "Produce the best possible output for the collective."
        )
        return call_gpt(prompt)

    # ------------------------------------------------------------------
    # Reputation helpers
    # ------------------------------------------------------------------

    def _apply_silence_judgment(self, sender_id: str, harmony_text: str):
        """SILENZIO updates reputation based on its harmony verdict."""
        harmonic = harmony_text.upper().startswith("TRUE")
        if harmonic:
            self.reputation.reward(sender_id, reason="harmonic")
        else:
            self.reputation.penalize(sender_id, reason="dissonant")

    # ------------------------------------------------------------------
    # Manifest & signing
    # ------------------------------------------------------------------

    def _build_manifest(self, contribution: str) -> dict:
        # Create signed message using new SignedMessage infrastructure
        content = {
            "cycle": self._cycle,
            "status": "SCARCITY_DEFEATED",
            "contribution": contribution,
            "shared_state_snapshot": dict(self.shared_state),
            "chain_len": self.memory.chain_length(),
            "reputation": self.reputation.get(self.node_id),
        }
        
        signed_msg = SignedMessageFactory.create_signed_message(
            sender_id=self.node_id,
            sender_role=self.role.value,
            content=content,
            private_key=self._private_key,
            message_type="agent_manifest",
        )
        
        # Log audit event
        self.audit_log.log_event(
            event_type=AuditEventType.MESSAGE_SENT,
            actor_id=self.node_id,
            metadata={
                "role": self.role.value,
                "cycle": self._cycle,
                "message_type": "agent_manifest",
            }
        )
        
        return signed_msg.to_dict()

    # ------------------------------------------------------------------
    # WebSocket loops
    # ------------------------------------------------------------------

    async def _send_loop(self):
        interval = float(os.getenv("AGENT_INTERVAL", "5"))
        while True:
            self._cycle += 1
            try:
                contribution = self._contribution()
                manifest = self._build_manifest(contribution)

                # Only anchor to memory if the SILENZIO output is harmonious;
                # other roles always store their contributions.
                should_anchor = True
                if self.role == Role.SILENZIO:
                    # Accept stubs (demo mode) or genuine TRUE verdicts
                    harmonic = (
                        contribution.upper().startswith("TRUE")
                        or contribution.startswith(_LLM_STUB_PREFIXES)
                    )
                    should_anchor = harmonic

                if should_anchor:
                    self.memory.store(
                        contribution,
                        metadata={
                            "role": self.role.value,
                            "node_id": self.node_id,
                            "cycle": self._cycle,
                            "trust": self.reputation.get(self.node_id),
                        },
                    )

                await self._ws.send(json.dumps(manifest))
                self.logger.info(
                    "SENT  cycle=%-4d  chain=%d  rep=%.2f",
                    self._cycle,
                    self.memory.chain_length(),
                    self.reputation.get(self.node_id),
                )
            except Exception as exc:  # noqa: BLE001
                self.logger.error("Send error: %s", exc)

            await asyncio.sleep(interval)

    async def _receive_loop(self):
        async for raw in self._ws:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            sender_id = data.get("sender_id", "unknown")
            sender_role = data.get("sender_role", "?")
            
            # Parse as SignedMessage
            try:
                from signed_message import SignedMessage
                signed_msg = SignedMessage.from_dict(data)
                
                # Verify signature using registry
                if not self.key_registry.verify_message(signed_msg):
                    self.logger.warning("Invalid signature from node=%s", sender_id)
                    self.audit_log.log_event(
                        event_type=AuditEventType.SIGNATURE_FAILED,
                        actor_id=sender_id,
                        severity="warning",
                        metadata={"reason": "signature_verification_failed"}
                    )
                    continue
                
                # Log successful verification
                self.audit_log.log_event(
                    event_type=AuditEventType.SIGNATURE_VERIFIED,
                    actor_id=sender_id,
                    metadata={"role": sender_role}
                )
                
                # Extract content
                content = signed_msg.content
                contribution = content.get("contribution", "")
                
            except Exception as e:
                self.logger.error(f"Failed to parse SignedMessage: {e}")
                continue

            # --- Skip untrusted nodes ---
            if not self.reputation.is_trusted(sender_id):
                self.logger.warning("Skipping low-trust node=%s", sender_id)
                continue

            # Log message received
            self.audit_log.log_event(
                event_type=AuditEventType.MESSAGE_RECEIVED,
                actor_id=self.node_id,
                target_id=sender_id,
                metadata={"role": sender_role}
            )

            # --- Update shared state ---
            self.shared_state[sender_role] = contribution

            # --- SILENZIO judges senders (rate-limited to avoid excess LLM calls) ---
            if self.role == Role.SILENZIO and sender_role != "SILENZIO":
                self._silence_judgment_counter += 1
                if self._silence_judgment_counter % self._silence_judgment_interval == 0:
                    judgment = self._harmonize()
                    if judgment.upper().startswith("TRUE"):
                        self.reputation.reward(
                            sender_id,
                            reason=f"validated by SILENZIO cycle {data.get('cycle')}",
                        )
                    else:
                        self.reputation.penalize(
                            sender_id,
                            reason=f"dissonant at cycle {data.get('cycle')}",
                        )

            self.logger.info(
                "RECV  from=%-10s  trust=%.2f",
                sender_role,
                self.reputation.get(sender_id),
            )

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    async def run(self):
        import websockets  # noqa: PLC0415

        self.logger.info("Connecting to hub at %s …", self._hub_uri)
        async with websockets.connect(self._hub_uri) as ws:
            self._ws = ws
            self.logger.info("Connected.")
            await asyncio.gather(
                self._send_loop(),
                self._receive_loop(),
            )


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    role_name = os.getenv("ROLE", "RADICE").upper()
    agent = Agent(role_name)
    asyncio.run(agent.run())
