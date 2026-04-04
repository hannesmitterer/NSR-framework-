"""
rate_limiter.py
─────────────────────────────────────────────────────────────────────────────
LEX AMORIS ECOSYSTEM – Rate Limiting System
─────────────────────────────────────────────────────────────────────────────
Implements comprehensive rate limiting with exemptions to protect against
spam and abuse while allowing emergency/critical messages.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class RateLimitRule:
    """
    Configuration for a rate limit rule.
    
    Attributes:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
        endpoint: Specific endpoint (None = global)
    """
    max_requests: int
    window_seconds: float
    endpoint: Optional[str] = None


class RateLimiter:
    """
    Token bucket rate limiter with exemption support.
    
    Features:
    - Per-client rate limiting
    - Per-endpoint rate limiting
    - Global rate limiting
    - Exemption/whitelist support
    - Sliding window algorithm
    """

    def __init__(self):
        # Track request timestamps per client per endpoint
        # Structure: {client_id: {endpoint: deque([timestamp1, timestamp2, ...])}}
        self._requests: dict[str, dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        
        # Exempted clients (whitelist)
        self._exemptions: Set[str] = set()
        
        # Rate limit rules per endpoint
        self._rules: dict[str, RateLimitRule] = {}
        
        # Global rate limit rule
        self._global_rule: Optional[RateLimitRule] = None
        
        # Default rules
        self.set_default_rules()

    def set_default_rules(self):
        """Set default rate limit rules."""
        # Default global limit: 100 requests per minute
        self._global_rule = RateLimitRule(
            max_requests=100,
            window_seconds=60.0
        )
        
        # Per-endpoint limits
        self.add_rule("/message", RateLimitRule(max_requests=30, window_seconds=60.0))
        self.add_rule("/reputation", RateLimitRule(max_requests=20, window_seconds=60.0))
        self.add_rule("/memory", RateLimitRule(max_requests=50, window_seconds=60.0))
        self.add_rule("/state", RateLimitRule(max_requests=60, window_seconds=60.0))

    def add_rule(self, endpoint: str, rule: RateLimitRule):
        """Add or update a rate limit rule for an endpoint."""
        self._rules[endpoint] = rule
        logger.info(f"Rate limit rule set for {endpoint}: {rule.max_requests} req/{rule.window_seconds}s")

    def remove_rule(self, endpoint: str):
        """Remove rate limit rule for an endpoint."""
        if endpoint in self._rules:
            del self._rules[endpoint]
            logger.info(f"Rate limit rule removed for {endpoint}")

    def add_exemption(self, client_id: str):
        """Add a client to the exemption list (whitelist)."""
        self._exemptions.add(client_id)
        logger.info(f"Client {client_id} added to rate limit exemptions")

    def remove_exemption(self, client_id: str):
        """Remove a client from the exemption list."""
        self._exemptions.discard(client_id)
        logger.info(f"Client {client_id} removed from rate limit exemptions")

    def is_exempted(self, client_id: str) -> bool:
        """Check if a client is exempted from rate limiting."""
        return client_id in self._exemptions

    def get_exemptions(self) -> Set[str]:
        """Get all exempted clients."""
        return self._exemptions.copy()

    def _clean_old_requests(self, requests: deque, window_seconds: float, now: float):
        """Remove requests outside the time window."""
        while requests and requests[0] < now - window_seconds:
            requests.popleft()

    def check_limit(
        self,
        client_id: str,
        endpoint: str = "global",
        now: Optional[float] = None
    ) -> tuple[bool, Optional[float]]:
        """
        Check if a request is allowed under rate limits.
        
        Args:
            client_id: Unique identifier for the client
            endpoint: Endpoint being accessed
            now: Current timestamp (defaults to time.time())
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
            - is_allowed: True if request is allowed
            - retry_after_seconds: If not allowed, seconds to wait before retry
        """
        if now is None:
            now = time.time()

        # Check exemption first
        if self.is_exempted(client_id):
            return True, None

        # Get the appropriate rule
        rule = self._rules.get(endpoint, self._global_rule)
        if rule is None:
            # No rule defined, allow request
            return True, None

        # Get request history for this client/endpoint
        client_requests = self._requests[client_id]
        endpoint_requests = client_requests[endpoint]

        # Clean old requests outside the window
        self._clean_old_requests(endpoint_requests, rule.window_seconds, now)

        # Check if limit exceeded
        if len(endpoint_requests) >= rule.max_requests:
            # Calculate retry_after
            oldest_request = endpoint_requests[0]
            retry_after = oldest_request + rule.window_seconds - now
            logger.warning(
                f"Rate limit exceeded for client={client_id} endpoint={endpoint}: "
                f"{len(endpoint_requests)}/{rule.max_requests} in {rule.window_seconds}s window"
            )
            return False, retry_after

        return True, None

    def record_request(self, client_id: str, endpoint: str = "global", now: Optional[float] = None):
        """
        Record a request for rate limiting purposes.
        
        Args:
            client_id: Unique identifier for the client
            endpoint: Endpoint being accessed
            now: Current timestamp (defaults to time.time())
        """
        if now is None:
            now = time.time()

        # Don't record for exempted clients
        if self.is_exempted(client_id):
            return

        # Record the request
        client_requests = self._requests[client_id]
        endpoint_requests = client_requests[endpoint]
        endpoint_requests.append(now)

    def get_stats(self, client_id: str, endpoint: str = "global") -> dict:
        """
        Get rate limit statistics for a client/endpoint.
        
        Returns:
            Dictionary with current request count and limit info
        """
        rule = self._rules.get(endpoint, self._global_rule)
        if rule is None:
            return {"error": "No rule defined"}

        client_requests = self._requests.get(client_id, {})
        endpoint_requests = client_requests.get(endpoint, deque())
        
        now = time.time()
        self._clean_old_requests(endpoint_requests, rule.window_seconds, now)

        return {
            "client_id": client_id,
            "endpoint": endpoint,
            "current_requests": len(endpoint_requests),
            "max_requests": rule.max_requests,
            "window_seconds": rule.window_seconds,
            "is_exempted": self.is_exempted(client_id),
            "remaining": max(0, rule.max_requests - len(endpoint_requests)),
        }

    def clear_client_history(self, client_id: str):
        """Clear rate limit history for a client."""
        if client_id in self._requests:
            del self._requests[client_id]
            logger.info(f"Cleared rate limit history for client {client_id}")

    def to_dict(self) -> dict:
        """Export rate limiter state to dictionary."""
        return {
            "exemptions": list(self._exemptions),
            "rules": {
                endpoint: {
                    "max_requests": rule.max_requests,
                    "window_seconds": rule.window_seconds,
                }
                for endpoint, rule in self._rules.items()
            },
            "global_rule": {
                "max_requests": self._global_rule.max_requests,
                "window_seconds": self._global_rule.window_seconds,
            } if self._global_rule else None,
        }
