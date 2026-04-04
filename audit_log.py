"""
audit_log.py
─────────────────────────────────────────────────────────────────────────────
LEX AMORIS ECOSYSTEM – Persistent Audit Trail
─────────────────────────────────────────────────────────────────────────────
Provides immutable audit logging with structured JSON format for compliance,
anomaly detection, and continuous monitoring (321.5 Hz heartbeat).
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional, List

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    SIGNATURE_VERIFIED = "signature_verified"
    SIGNATURE_FAILED = "signature_failed"
    REPUTATION_CHANGED = "reputation_changed"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    EXEMPTION_GRANTED = "exemption_granted"
    EXEMPTION_REVOKED = "exemption_revoked"
    IPFS_UPLOAD = "ipfs_upload"
    IPFS_DOWNLOAD = "ipfs_download"
    AGENT_CONNECTED = "agent_connected"
    AGENT_DISCONNECTED = "agent_disconnected"
    HEARTBEAT = "heartbeat"
    EMERGENCY_OVERRIDE = "emergency_override"
    GOVERNANCE_UPDATE = "governance_update"
    SYNTROPY_VIOLATION = "syntropy_violation"
    SYSTEM_ERROR = "system_error"


@dataclass
class AuditEvent:
    """
    Structured audit event.
    
    Attributes:
        event_id: Unique identifier for this event
        event_type: Type of event
        timestamp: Unix timestamp
        actor_id: ID of the entity performing the action
        target_id: ID of the entity being acted upon (optional)
        metadata: Additional event-specific data
        severity: Event severity (info, warning, error, critical)
        chain_hash: Hash linking to previous event (for immutability)
    """
    event_id: str
    event_type: str
    timestamp: float
    actor_id: str
    target_id: Optional[str] = None
    metadata: Optional[dict] = None
    severity: str = "info"
    chain_hash: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> AuditEvent:
        """Create from dictionary."""
        return cls(**data)


class AuditLog:
    """
    Persistent audit log with hash chain for immutability.
    
    Features:
    - JSON-formatted structured logging
    - File-based persistence
    - Hash chain for tamper detection
    - Query and search capabilities
    - Automatic rotation
    """

    def __init__(
        self,
        log_dir: str | Path = "memory_db/audit",
        max_memory_events: int = 1000,
        auto_flush: bool = True,
    ):
        """
        Initialize audit log.
        
        Args:
            log_dir: Directory for audit log files
            max_memory_events: Maximum events to keep in memory
            auto_flush: Automatically flush to disk after each event
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_memory_events = max_memory_events
        self.auto_flush = auto_flush
        
        # In-memory event buffer
        self._events: deque[AuditEvent] = deque(maxlen=max_memory_events)
        
        # Hash of the last event (for chain)
        self._last_hash: Optional[str] = None
        
        # Event counter
        self._event_counter = 0
        
        # Current log file
        self._current_log_file = self._get_log_file()
        
        # Load last hash from previous session
        self._load_last_hash()
        
        logger.info(f"Audit log initialized: {self.log_dir}")

    def _get_log_file(self) -> Path:
        """Get current log file path (daily rotation)."""
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"audit_{date_str}.jsonl"

    def _load_last_hash(self):
        """Load the last hash from the most recent log file."""
        try:
            if self._current_log_file.exists():
                # Read last line
                with open(self._current_log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_event = json.loads(lines[-1])
                        self._last_hash = self._compute_hash(last_event)
                        logger.info(f"Loaded last hash from previous session: {self._last_hash[:16]}...")
        except Exception as e:
            logger.warning(f"Could not load last hash: {e}")
            self._last_hash = None

    def _compute_hash(self, event_dict: dict) -> str:
        """Compute SHA256 hash of an event."""
        import hashlib
        canonical = json.dumps(event_dict, sort_keys=True).encode()
        return hashlib.sha256(canonical).hexdigest()

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        self._event_counter += 1
        timestamp_ms = int(time.time() * 1000)
        return f"{timestamp_ms}_{self._event_counter:06d}"

    def log_event(
        self,
        event_type: AuditEventType | str,
        actor_id: str,
        target_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        severity: str = "info",
    ) -> AuditEvent:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            actor_id: ID of entity performing action
            target_id: ID of entity being acted upon
            metadata: Additional event data
            severity: Event severity level
            
        Returns:
            Created AuditEvent
        """
        # Convert enum to string
        if isinstance(event_type, AuditEventType):
            event_type = event_type.value

        # Create event
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            timestamp=time.time(),
            actor_id=actor_id,
            target_id=target_id,
            metadata=metadata,
            severity=severity,
            chain_hash=self._last_hash,
        )

        # Update last hash
        event_dict = event.to_dict()
        self._last_hash = self._compute_hash(event_dict)

        # Add to memory buffer
        self._events.append(event)

        # Write to disk if auto_flush enabled
        if self.auto_flush:
            self._write_event(event_dict)

        logger.debug(f"Audit event logged: {event_type} by {actor_id}")
        return event

    def _write_event(self, event_dict: dict):
        """Write event to log file."""
        try:
            # Check if we need to rotate (new day)
            current_file = self._get_log_file()
            if current_file != self._current_log_file:
                self._current_log_file = current_file
                logger.info(f"Rotated to new log file: {current_file}")

            # Append to log file (JSONL format)
            with open(self._current_log_file, 'a') as f:
                f.write(json.dumps(event_dict) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write audit event to disk: {e}")

    def flush(self):
        """Flush all buffered events to disk."""
        if not self.auto_flush:
            for event in self._events:
                self._write_event(event.to_dict())
            logger.info(f"Flushed {len(self._events)} events to disk")

    def get_recent_events(self, limit: int = 100) -> List[AuditEvent]:
        """Get recent events from memory buffer."""
        return list(self._events)[-limit:]

    def query_events(
        self,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """
        Query events with filters.
        
        Args:
            event_type: Filter by event type
            actor_id: Filter by actor ID
            start_time: Filter by start timestamp
            end_time: Filter by end timestamp
            severity: Filter by severity
            limit: Maximum number of results
            
        Returns:
            List of matching events
        """
        results = []
        
        for event in reversed(self._events):
            # Apply filters
            if event_type and event.event_type != event_type:
                continue
            if actor_id and event.actor_id != actor_id:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            if severity and event.severity != severity:
                continue
            
            results.append(event)
            
            if len(results) >= limit:
                break
        
        return results

    def verify_chain(self) -> tuple[bool, Optional[str]]:
        """
        Verify the integrity of the event hash chain.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        prev_hash = None
        
        for i, event in enumerate(self._events):
            # Check if chain_hash matches previous event's hash
            if event.chain_hash != prev_hash:
                return False, f"Chain broken at event {i}: expected {prev_hash}, got {event.chain_hash}"
            
            # Compute hash for next iteration
            prev_hash = self._compute_hash(event.to_dict())
        
        return True, None

    def get_stats(self) -> dict:
        """Get audit log statistics."""
        return {
            "total_events_in_memory": len(self._events),
            "current_log_file": str(self._current_log_file),
            "last_hash": self._last_hash[:16] + "..." if self._last_hash else None,
            "event_counter": self._event_counter,
            "auto_flush": self.auto_flush,
        }


# Singleton instance
_audit_log: Optional[AuditLog] = None


def get_audit_log() -> AuditLog:
    """Get or create the global audit log instance."""
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log
