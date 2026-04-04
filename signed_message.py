"""
signed_message.py
─────────────────────────────────────────────────────────────────────────────
LEX AMORIS ECOSYSTEM – SignedMessage Data Structure
─────────────────────────────────────────────────────────────────────────────
Implements cryptographically signed messages with public key verification.
Provides transparency and authenticity for all cross-agent communications.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from typing import Any, Optional

from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256


@dataclass
class SignedMessage:
    """
    A message with cryptographic signature for authenticity verification.
    
    Attributes:
        sender_id: Unique identifier of the sender (8-char hex from public key hash)
        sender_role: Role of the sender (RADICE, SILENZIO, NODO)
        content: Message payload (can be any JSON-serializable data)
        timestamp: Unix timestamp when message was created
        signature: Hex-encoded RSA signature
        public_key_pem: PEM-encoded public key of sender (for verification)
        message_type: Type of message (state, memory, reputation, etc.)
        metadata: Additional metadata (optional)
    """
    sender_id: str
    sender_role: str
    content: Any
    timestamp: float
    signature: str
    public_key_pem: str
    message_type: str = "general"
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> SignedMessage:
        """Create SignedMessage from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> SignedMessage:
        """Create SignedMessage from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def verify(self) -> bool:
        """
        Verify the signature of this message.
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Import the public key
            public_key = RSA.import_key(self.public_key_pem)
            
            # Create canonical representation (without signature)
            canonical_data = {
                "sender_id": self.sender_id,
                "sender_role": self.sender_role,
                "content": self.content,
                "timestamp": self.timestamp,
                "message_type": self.message_type,
                "metadata": self.metadata,
            }
            canonical = json.dumps(canonical_data, sort_keys=True).encode()
            
            # Verify signature
            h = SHA256.new(canonical)
            pkcs1_15.new(public_key).verify(h, bytes.fromhex(self.signature))
            return True
        except Exception:
            return False


class SignedMessageFactory:
    """Factory for creating signed messages."""

    @staticmethod
    def create_signed_message(
        sender_id: str,
        sender_role: str,
        content: Any,
        private_key: RSA.RsaKey,
        message_type: str = "general",
        metadata: Optional[dict] = None,
    ) -> SignedMessage:
        """
        Create a new signed message.
        
        Args:
            sender_id: Unique identifier of the sender
            sender_role: Role of the sender
            content: Message payload
            private_key: RSA private key for signing
            message_type: Type of message
            metadata: Additional metadata
            
        Returns:
            SignedMessage with valid signature
        """
        timestamp = time.time()
        
        # Create canonical representation for signing
        canonical_data = {
            "sender_id": sender_id,
            "sender_role": sender_role,
            "content": content,
            "timestamp": timestamp,
            "message_type": message_type,
            "metadata": metadata,
        }
        canonical = json.dumps(canonical_data, sort_keys=True).encode()
        
        # Sign the message
        h = SHA256.new(canonical)
        signature = pkcs1_15.new(private_key).sign(h)
        
        # Export public key
        public_key_pem = private_key.publickey().export_key().decode()
        
        return SignedMessage(
            sender_id=sender_id,
            sender_role=sender_role,
            content=content,
            timestamp=timestamp,
            signature=signature.hex(),
            public_key_pem=public_key_pem,
            message_type=message_type,
            metadata=metadata,
        )


class PublicKeyRegistry:
    """
    Registry for storing and retrieving public keys of agents.
    Enables cross-agent signature verification.
    """

    def __init__(self):
        self._keys: dict[str, str] = {}  # sender_id -> public_key_pem

    def register_key(self, sender_id: str, public_key_pem: str):
        """Register a public key for a sender."""
        self._keys[sender_id] = public_key_pem

    def get_key(self, sender_id: str) -> Optional[str]:
        """Get public key for a sender."""
        return self._keys.get(sender_id)

    def has_key(self, sender_id: str) -> bool:
        """Check if public key is registered for a sender."""
        return sender_id in self._keys

    def verify_message(self, message: SignedMessage) -> bool:
        """
        Verify a signed message using the registry.
        Automatically registers the public key if not present.
        
        Returns:
            True if signature is valid, False otherwise
        """
        # Auto-register public key from message if not present
        if not self.has_key(message.sender_id):
            self.register_key(message.sender_id, message.public_key_pem)
        
        # Verify using the message's built-in verification
        return message.verify()

    def to_dict(self) -> dict:
        """Export registry to dictionary."""
        return {"keys": self._keys}

    def from_dict(self, data: dict):
        """Import registry from dictionary."""
        self._keys = data.get("keys", {})
