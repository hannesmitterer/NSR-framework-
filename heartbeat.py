"""
heartbeat.py
─────────────────────────────────────────────────────────────────────────────
LEX AMORIS ECOSYSTEM – Heartbeat Monitoring System
─────────────────────────────────────────────────────────────────────────────
Implements heartbeat emission and monitoring at target frequency (321.5 Hz)
for continuous system health monitoring and anomaly detection.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class HeartbeatStats:
    """Statistics for heartbeat monitoring."""
    total_beats: int
    average_frequency: float
    target_frequency: float
    frequency_variance: float
    missed_beats: int
    anomalies_detected: int
    uptime_seconds: float
    last_beat_timestamp: float


class HeartbeatMonitor:
    """
    Heartbeat monitoring system with frequency analysis.
    
    Monitors system "pulse" at a target frequency (default 321.5 Hz)
    and detects anomalies in rhythm and timing.
    
    Features:
    - Configurable target frequency
    - Real-time frequency calculation
    - Anomaly detection
    - Statistics collection
    - Callback support for anomalies
    """

    def __init__(
        self,
        target_frequency: float = 321.5,
        anomaly_threshold: float = 0.1,  # 10% deviation
        history_size: int = 1000,
    ):
        """
        Initialize heartbeat monitor.
        
        Args:
            target_frequency: Target heartbeat frequency in Hz
            anomaly_threshold: Threshold for anomaly detection (fraction of target)
            history_size: Number of recent heartbeats to keep in memory
        """
        self.target_frequency = target_frequency
        self.target_period = 1.0 / target_frequency  # Time between beats
        self.anomaly_threshold = anomaly_threshold
        self.history_size = history_size
        
        # Heartbeat timing history
        self._timestamps: deque[float] = deque(maxlen=history_size)
        
        # Statistics
        self._total_beats = 0
        self._missed_beats = 0
        self._anomalies_detected = 0
        self._start_time = time.time()
        self._last_beat_time: Optional[float] = None
        
        # Callbacks
        self._anomaly_callbacks: list[Callable] = []
        
        logger.info(f"Heartbeat monitor initialized: target={target_frequency} Hz")

    def register_anomaly_callback(self, callback: Callable):
        """Register a callback to be called when anomalies are detected."""
        self._anomaly_callbacks.append(callback)

    def beat(self, timestamp: Optional[float] = None) -> bool:
        """
        Record a heartbeat.
        
        Args:
            timestamp: Timestamp of the beat (defaults to time.time())
            
        Returns:
            True if beat is normal, False if anomaly detected
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Record beat
        self._timestamps.append(timestamp)
        self._total_beats += 1
        
        # Check for anomalies if we have previous beat
        is_normal = True
        if self._last_beat_time is not None:
            period = timestamp - self._last_beat_time
            expected_period = self.target_period
            
            # Calculate deviation
            deviation = abs(period - expected_period) / expected_period
            
            if deviation > self.anomaly_threshold:
                is_normal = False
                self._anomalies_detected += 1
                
                # Trigger callbacks
                for callback in self._anomaly_callbacks:
                    try:
                        callback({
                            "timestamp": timestamp,
                            "period": period,
                            "expected_period": expected_period,
                            "deviation": deviation,
                        })
                    except Exception as e:
                        logger.error(f"Anomaly callback failed: {e}")
        
        self._last_beat_time = timestamp
        return is_normal

    def get_current_frequency(self, window_size: int = 100) -> Optional[float]:
        """
        Calculate current frequency based on recent heartbeats.
        
        Args:
            window_size: Number of recent beats to use for calculation
            
        Returns:
            Current frequency in Hz, or None if insufficient data
        """
        if len(self._timestamps) < 2:
            return None
        
        # Use last N timestamps
        recent = list(self._timestamps)[-min(window_size, len(self._timestamps)):]
        
        if len(recent) < 2:
            return None
        
        # Calculate average period
        periods = [recent[i+1] - recent[i] for i in range(len(recent) - 1)]
        avg_period = sum(periods) / len(periods)
        
        # Convert to frequency
        return 1.0 / avg_period if avg_period > 0 else None

    def get_frequency_variance(self, window_size: int = 100) -> Optional[float]:
        """
        Calculate variance in frequency over recent heartbeats.
        
        Args:
            window_size: Number of recent beats to use
            
        Returns:
            Variance as fraction of target frequency
        """
        current_freq = self.get_current_frequency(window_size)
        if current_freq is None:
            return None
        
        deviation = abs(current_freq - self.target_frequency) / self.target_frequency
        return deviation

    def get_stats(self) -> HeartbeatStats:
        """Get heartbeat statistics."""
        current_freq = self.get_current_frequency() or 0.0
        variance = self.get_frequency_variance() or 0.0
        uptime = time.time() - self._start_time
        
        return HeartbeatStats(
            total_beats=self._total_beats,
            average_frequency=current_freq,
            target_frequency=self.target_frequency,
            frequency_variance=variance,
            missed_beats=self._missed_beats,
            anomalies_detected=self._anomalies_detected,
            uptime_seconds=uptime,
            last_beat_timestamp=self._last_beat_time or 0.0,
        )

    def reset(self):
        """Reset all statistics."""
        self._timestamps.clear()
        self._total_beats = 0
        self._missed_beats = 0
        self._anomalies_detected = 0
        self._start_time = time.time()
        self._last_beat_time = None
        logger.info("Heartbeat monitor reset")


class HeartbeatEmitter:
    """
    Asynchronous heartbeat emitter.
    
    Emits heartbeats at a target frequency and monitors them.
    """

    def __init__(
        self,
        target_frequency: float = 321.5,
        monitor: Optional[HeartbeatMonitor] = None,
    ):
        """
        Initialize heartbeat emitter.
        
        Args:
            target_frequency: Target emission frequency in Hz
            monitor: Optional HeartbeatMonitor to record beats
        """
        self.target_frequency = target_frequency
        self.target_period = 1.0 / target_frequency
        self.monitor = monitor or HeartbeatMonitor(target_frequency)
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info(f"Heartbeat emitter initialized: target={target_frequency} Hz")

    async def _emit_loop(self):
        """Main emission loop."""
        while self._running:
            try:
                # Record heartbeat
                now = time.time()
                self.monitor.beat(now)
                
                # Wait for next beat
                await asyncio.sleep(self.target_period)
                
            except Exception as e:
                logger.error(f"Heartbeat emission error: {e}")

    def start(self):
        """Start emitting heartbeats."""
        if self._running:
            logger.warning("Heartbeat emitter already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._emit_loop())
        logger.info("Heartbeat emitter started")

    def stop(self):
        """Stop emitting heartbeats."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Heartbeat emitter stopped")

    def get_stats(self) -> HeartbeatStats:
        """Get heartbeat statistics."""
        return self.monitor.get_stats()


# Global heartbeat monitor instance
_heartbeat_monitor: Optional[HeartbeatMonitor] = None


def get_heartbeat_monitor() -> HeartbeatMonitor:
    """Get or create the global heartbeat monitor."""
    global _heartbeat_monitor
    if _heartbeat_monitor is None:
        _heartbeat_monitor = HeartbeatMonitor()
    return _heartbeat_monitor
