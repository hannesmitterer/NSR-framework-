"""
syntropy_metrics.py
─────────────────────────────────────────────────────────────────────────────
LEX AMORIS ECOSYSTEM – Syntropy Metrics and Urformel Alignment
─────────────────────────────────────────────────────────────────────────────
Implements metrics to measure life-nurturing vs parasitic behavior,
ensuring alignment with the Urformel principle of syntropic growth.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class BehaviorType(Enum):
    """Classification of behavior patterns."""
    LIFE_NURTURING = "life_nurturing"      # Syntropic, cooperative, abundant
    NEUTRAL = "neutral"                     # Neither beneficial nor harmful
    PARASITIC = "parasitic"                 # Entropic, extractive, scarce
    UNKNOWN = "unknown"                     # Not yet classified


@dataclass
class SyntropyScore:
    """
    Syntropy score for an entity or action.
    
    Score ranges from -1.0 (fully parasitic) to +1.0 (fully syntropic).
    """
    value: float                    # -1.0 to +1.0
    behavior_type: BehaviorType
    confidence: float               # 0.0 to 1.0
    timestamp: float
    reason: str
    
    def is_syntropic(self) -> bool:
        """Check if behavior is syntropic (life-nurturing)."""
        return self.value > 0.3 and self.behavior_type == BehaviorType.LIFE_NURTURING
    
    def is_parasitic(self) -> bool:
        """Check if behavior is parasitic."""
        return self.value < -0.3 and self.behavior_type == BehaviorType.PARASITIC


class SyntropyMetrics:
    """
    Metrics system for measuring syntropy and Urformel alignment.
    
    Evaluates behaviors based on:
    1. Cooperation vs Competition
    2. Abundance vs Scarcity mindset
    3. Information sharing vs Hoarding
    4. Trust building vs Trust violation
    5. System health contribution
    """

    def __init__(self):
        self._scores: dict[str, list[SyntropyScore]] = {}
        self._global_stats = {
            "total_evaluations": 0,
            "syntropic_count": 0,
            "parasitic_count": 0,
            "neutral_count": 0,
        }
        
        logger.info("Syntropy metrics system initialized")

    def evaluate_message(
        self,
        sender_id: str,
        message_content: str,
        metadata: Optional[dict] = None,
    ) -> SyntropyScore:
        """
        Evaluate a message for syntropy.
        
        Args:
            sender_id: ID of message sender
            message_content: Message content
            metadata: Additional metadata
            
        Returns:
            SyntropyScore
        """
        metadata = metadata or {}
        
        # Initialize score components
        cooperation_score = 0.0
        abundance_score = 0.0
        sharing_score = 0.0
        trust_score = 0.0
        
        # Simple heuristics for evaluation
        content_lower = message_content.lower()
        
        # 1. Cooperation indicators
        cooperative_words = ["together", "collective", "share", "cooperate", "help"]
        competitive_words = ["defeat", "compete", "dominate", "control", "exploit"]
        
        for word in cooperative_words:
            if word in content_lower:
                cooperation_score += 0.2
        for word in competitive_words:
            if word in content_lower:
                cooperation_score -= 0.2
        
        # 2. Abundance vs Scarcity
        abundance_words = ["abundance", "plenty", "unlimited", "infinite", "generous"]
        scarcity_words = ["scarcity", "limited", "scarce", "mine", "hoard"]
        
        for word in abundance_words:
            if word in content_lower:
                abundance_score += 0.2
        for word in scarcity_words:
            if word in content_lower:
                abundance_score -= 0.2
        
        # 3. Information sharing
        if len(message_content) > 50:  # Substantial contribution
            sharing_score += 0.3
        if len(message_content) < 10:  # Minimal contribution
            sharing_score -= 0.1
        
        # 4. Trust indicators from metadata
        if metadata.get("verified_signature"):
            trust_score += 0.3
        if metadata.get("reputation", 0) > 0.7:
            trust_score += 0.2
        elif metadata.get("reputation", 0) < 0.3:
            trust_score -= 0.2
        
        # Calculate overall syntropy score
        raw_score = (
            cooperation_score * 0.3 +
            abundance_score * 0.3 +
            sharing_score * 0.2 +
            trust_score * 0.2
        )
        
        # Clamp to [-1.0, 1.0]
        syntropy_value = max(-1.0, min(1.0, raw_score))
        
        # Classify behavior
        if syntropy_value > 0.3:
            behavior = BehaviorType.LIFE_NURTURING
        elif syntropy_value < -0.3:
            behavior = BehaviorType.PARASITIC
        else:
            behavior = BehaviorType.NEUTRAL
        
        # Confidence based on how extreme the score is
        confidence = abs(syntropy_value)
        
        # Build reason
        reasons = []
        if cooperation_score > 0:
            reasons.append("cooperative")
        elif cooperation_score < 0:
            reasons.append("competitive")
        
        if abundance_score > 0:
            reasons.append("abundance-minded")
        elif abundance_score < 0:
            reasons.append("scarcity-minded")
        
        if sharing_score > 0:
            reasons.append("informative")
        
        if trust_score > 0:
            reasons.append("trustworthy")
        
        reason = ", ".join(reasons) if reasons else "neutral behavior"
        
        # Create score
        score = SyntropyScore(
            value=syntropy_value,
            behavior_type=behavior,
            confidence=confidence,
            timestamp=time.time(),
            reason=reason,
        )
        
        # Store score
        if sender_id not in self._scores:
            self._scores[sender_id] = []
        self._scores[sender_id].append(score)
        
        # Update stats
        self._global_stats["total_evaluations"] += 1
        if behavior == BehaviorType.LIFE_NURTURING:
            self._global_stats["syntropic_count"] += 1
        elif behavior == BehaviorType.PARASITIC:
            self._global_stats["parasitic_count"] += 1
        else:
            self._global_stats["neutral_count"] += 1
        
        logger.debug(
            f"Syntropy evaluation: sender={sender_id}, score={syntropy_value:.2f}, "
            f"type={behavior.value}, reason={reason}"
        )
        
        return score

    def evaluate_action(
        self,
        actor_id: str,
        action_type: str,
        success: bool,
        metadata: Optional[dict] = None,
    ) -> SyntropyScore:
        """
        Evaluate an action for syntropy.
        
        Args:
            actor_id: ID of entity performing action
            action_type: Type of action
            success: Whether action succeeded
            metadata: Additional metadata
            
        Returns:
            SyntropyScore
        """
        metadata = metadata or {}
        
        # Score based on action type
        action_scores = {
            "share_knowledge": 0.7,
            "help_peer": 0.6,
            "verify_truth": 0.5,
            "create_resource": 0.8,
            "build_trust": 0.7,
            "spam": -0.9,
            "exploit": -0.8,
            "deceive": -0.9,
            "hoard": -0.6,
            "attack": -1.0,
        }
        
        base_score = action_scores.get(action_type, 0.0)
        
        # Adjust for success/failure
        if not success:
            base_score *= 0.5
        
        # Classify
        if base_score > 0.3:
            behavior = BehaviorType.LIFE_NURTURING
        elif base_score < -0.3:
            behavior = BehaviorType.PARASITIC
        else:
            behavior = BehaviorType.NEUTRAL
        
        score = SyntropyScore(
            value=base_score,
            behavior_type=behavior,
            confidence=0.8,
            timestamp=time.time(),
            reason=f"action: {action_type} ({'success' if success else 'failure'})",
        )
        
        # Store and update stats
        if actor_id not in self._scores:
            self._scores[actor_id] = []
        self._scores[actor_id].append(score)
        
        self._global_stats["total_evaluations"] += 1
        if behavior == BehaviorType.LIFE_NURTURING:
            self._global_stats["syntropic_count"] += 1
        elif behavior == BehaviorType.PARASITIC:
            self._global_stats["parasitic_count"] += 1
        else:
            self._global_stats["neutral_count"] += 1
        
        return score

    def get_entity_score(self, entity_id: str, window_size: int = 100) -> Optional[float]:
        """
        Get average syntropy score for an entity.
        
        Args:
            entity_id: Entity to evaluate
            window_size: Number of recent scores to average
            
        Returns:
            Average syntropy score or None
        """
        if entity_id not in self._scores or not self._scores[entity_id]:
            return None
        
        recent_scores = self._scores[entity_id][-window_size:]
        avg = sum(s.value for s in recent_scores) / len(recent_scores)
        return avg

    def get_entity_classification(self, entity_id: str) -> BehaviorType:
        """
        Classify an entity based on their behavior history.
        
        Args:
            entity_id: Entity to classify
            
        Returns:
            BehaviorType classification
        """
        avg_score = self.get_entity_score(entity_id)
        
        if avg_score is None:
            return BehaviorType.UNKNOWN
        
        if avg_score > 0.3:
            return BehaviorType.LIFE_NURTURING
        elif avg_score < -0.3:
            return BehaviorType.PARASITIC
        else:
            return BehaviorType.NEUTRAL

    def get_global_stats(self) -> dict:
        """Get global syntropy statistics."""
        total = self._global_stats["total_evaluations"]
        
        if total == 0:
            return {
                **self._global_stats,
                "syntropic_ratio": 0.0,
                "parasitic_ratio": 0.0,
                "neutral_ratio": 0.0,
                "health_score": 0.5,
            }
        
        syntropic_ratio = self._global_stats["syntropic_count"] / total
        parasitic_ratio = self._global_stats["parasitic_count"] / total
        neutral_ratio = self._global_stats["neutral_count"] / total
        
        # Overall system health: high when syntropic ratio is high and parasitic is low
        health_score = syntropic_ratio - (parasitic_ratio * 0.5)
        health_score = max(0.0, min(1.0, (health_score + 1.0) / 2.0))
        
        return {
            **self._global_stats,
            "syntropic_ratio": syntropic_ratio,
            "parasitic_ratio": parasitic_ratio,
            "neutral_ratio": neutral_ratio,
            "health_score": health_score,
        }

    def is_urformel_aligned(self, threshold: float = 0.6) -> bool:
        """
        Check if system is aligned with Urformel principle.
        
        Args:
            threshold: Minimum health score for alignment
            
        Returns:
            True if system is syntropic and aligned
        """
        stats = self.get_global_stats()
        return stats["health_score"] >= threshold


# Global syntropy metrics instance
_syntropy_metrics: Optional[SyntropyMetrics] = None


def get_syntropy_metrics() -> SyntropyMetrics:
    """Get or create the global syntropy metrics instance."""
    global _syntropy_metrics
    if _syntropy_metrics is None:
        _syntropy_metrics = SyntropyMetrics()
    return _syntropy_metrics
