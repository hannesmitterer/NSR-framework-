"""
reputation.py
─────────────────────────────────────────────────────────────────────────────
LEX AMORIS ECOSYSTEM – Distributed Reputation / Trust Engine
─────────────────────────────────────────────────────────────────────────────
Tracks the trustworthiness of each agent node.  Scores are clamped to [0, 1].
SILENZIO is the primary validator that adjusts scores based on harmony checks.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_SCORES_FILE = Path("memory_db/reputation.json")

_DEFAULT_SCORE = 0.5
_MAX_SCORE = 1.0
_MIN_SCORE = 0.0


class ReputationSystem:
    """
    Simple in-memory reputation store with file persistence.

    Scores are keyed by node ID (8-char hex from the RSA public key hash).
    They are also exposed by role name for convenience.
    """

    def __init__(self):
        self._scores: dict[str, float] = {}
        self._history: list[dict] = []
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _load(self):
        if _SCORES_FILE.exists():
            try:
                data = json.loads(_SCORES_FILE.read_text())
                self._scores = data.get("scores", {})
                self._history = data.get("history", [])
                logger.info("Loaded reputation data (%d nodes)", len(self._scores))
            except Exception:  # noqa: BLE001
                logger.warning("Could not load reputation file – starting fresh")

    def _save(self):
        _SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SCORES_FILE.write_text(
            json.dumps({"scores": self._scores, "history": self._history[-200:]})
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get(self, node_id: str) -> float:
        """Return current score for *node_id* (default 0.5)."""
        return self._scores.get(node_id, _DEFAULT_SCORE)

    def update(self, node_id: str, delta: float, reason: str = "") -> float:
        """
        Adjust score for *node_id* by *delta* and clamp to [0, 1].
        Returns the new score.
        """
        current = self._scores.get(node_id, _DEFAULT_SCORE)
        new_score = max(_MIN_SCORE, min(_MAX_SCORE, current + delta))
        self._scores[node_id] = new_score

        entry = {
            "node_id": node_id,
            "delta": delta,
            "score": new_score,
            "reason": reason,
            "timestamp": time.time(),
        }
        self._history.append(entry)
        logger.debug(
            "Reputation  node=%-12s  delta=%-+.2f  new=%.3f  reason=%s",
            node_id,
            delta,
            new_score,
            reason,
        )
        self._save()
        return new_score

    def reward(self, node_id: str, reason: str = "harmonic") -> float:
        return self.update(node_id, +0.05, reason)

    def penalize(self, node_id: str, reason: str = "dissonant") -> float:
        return self.update(node_id, -0.10, reason)

    def is_trusted(self, node_id: str, threshold: float = 0.30) -> bool:
        """Return True if the node score is above *threshold*."""
        return self.get(node_id) >= threshold

    def all_scores(self) -> dict[str, float]:
        return dict(self._scores)

    def history(self, last: int = 50) -> list[dict]:
        return self._history[-last:]
