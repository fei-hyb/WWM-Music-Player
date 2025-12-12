"""
Advanced Playback Engine for Game Music Player
Provides high-precision timing, BPM support, and anti-cheat safety features.

Author: Python Music Architect
"""

import time
import random
import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NoteDuration(Enum):
    """Standard musical note durations."""
    WHOLE = 4.0
    HALF = 2.0
    QUARTER = 1.0
    EIGHTH = 0.5
    SIXTEENTH = 0.25
    THIRTY_SECOND = 0.125


@dataclass
class MusicalEvent:
    """
    Represents a single musical event with precise timing.

    Attributes:
        key: The keyboard key to press
        start_time: When to trigger (seconds from start)
        duration: How long to hold (seconds)
        note_name: Human-readable note (e.g., "High1")
        velocity: Note intensity (0.0-1.0, for future use)
    """
    key: str
    start_time: float
    duration: float
    note_name: str
    velocity: float = 1.0


class PlaybackEngine:
    """
    High-precision playback engine with BPM support and anti-cheat features.

    Features:
    - Sub-millisecond timing accuracy using time.perf_counter()
    - BPM-based tempo control with beat/measure calculations
    - Human-like randomness (configurable jitter)
    - Drift compensation for long sequences
    - Dry-run mode for preview without execution
    - Diagnostic timeline printing
    """

    def __init__(
        self,
        bpm: float = 120.0,
        humanize: bool = True,
        jitter_ms: tuple = (5, 15),
        key_press_callback: Optional[Callable] = None
    ):
        """
        Initialize the playback engine.

        Args:
            bpm: Beats per minute (default 120)
            humanize: Add human-like timing variations
            jitter_ms: Random jitter range in milliseconds (min, max)
            key_press_callback: Function to call for key presses (key: str) -> None
        """
        self.bpm = bpm
        self.humanize = humanize
        self.jitter_range = tuple(ms / 1000.0 for ms in jitter_ms)  # Convert to seconds
        self.key_press_callback = key_press_callback

        # Timing calculations
        self._beat_duration = 60.0 / self.bpm  # Seconds per beat

        # Playback state
        self.is_playing = False
        self.events: List[MusicalEvent] = []

        logger.info(f"PlaybackEngine initialized: BPM={bpm}, beat={self._beat_duration:.3f}s")

    def set_bpm(self, bpm: float) -> None:
        """
        Set the tempo in beats per minute.

        Args:
            bpm: Beats per minute (must be > 0)
        """
        if bpm <= 0:
            raise ValueError("BPM must be greater than 0")

        self.bpm = bpm
        self._beat_duration = 60.0 / self.bpm
        logger.info(f"BPM set to {bpm} (beat duration: {self._beat_duration:.3f}s)")

    def beats_to_seconds(self, beats: float) -> float:
        """
        Convert musical beats to seconds based on current BPM.

        Args:
            beats: Number of beats

        Returns:
            Duration in seconds

        Example:
            At 120 BPM, quarter note (1 beat) = 0.5 seconds
            At 120 BPM, eighth note (0.5 beats) = 0.25 seconds
        """
        return beats * self._beat_duration

    def note_duration_to_seconds(self, duration: NoteDuration) -> float:
        """
        Convert a NoteDuration enum to seconds.

        Args:
            duration: NoteDuration enum value

        Returns:
            Duration in seconds
        """
        return self.beats_to_seconds(duration.value)

    def add_event(
        self,
        key: str,
        start_time: float,
        duration: float = 0.1,
        note_name: str = "",
        velocity: float = 1.0
    ) -> None:
        """
        Add a musical event to the playback schedule.

        Args:
            key: Keyboard key to press
            start_time: When to trigger (seconds from playback start)
            duration: How long to hold (seconds)
            note_name: Human-readable note name
            velocity: Note intensity (0.0-1.0)
        """
        event = MusicalEvent(
            key=key,
            start_time=start_time,
            duration=duration,
            note_name=note_name or key,
            velocity=velocity
        )
        self.events.append(event)

    def clear_events(self) -> None:
        """Clear all scheduled events."""
        self.events.clear()
        logger.info("All events cleared")

    def sort_events(self) -> None:
        """Sort events by start time (required before playback)."""
        self.events.sort(key=lambda e: e.start_time)

    def get_total_duration(self) -> float:
        """
        Calculate total playback duration.

        Returns:
            Total duration in seconds
        """
        if not self.events:
            return 0.0

        # Find the last event's end time
        last_event = max(self.events, key=lambda e: e.start_time + e.duration)
        return last_event.start_time + last_event.duration

    def print_timeline(self, max_events: int = 50) -> None:
        """
        Print a diagnostic timeline of scheduled events.

        Args:
            max_events: Maximum number of events to print
        """
        if not self.events:
            print("No events scheduled")
            return

        self.sort_events()
        total_duration = self.get_total_duration()

        print("\n" + "="*70)
        print(f"PLAYBACK TIMELINE (BPM: {self.bpm}, Total: {total_duration:.2f}s)")
        print("="*70)
        print(f"{'Time (s)':<10} {'Note':<15} {'Key':<8} {'Duration (s)':<12}")
        print("-"*70)

        for i, event in enumerate(self.events[:max_events]):
            print(f"{event.start_time:<10.3f} {event.note_name:<15} {event.key.upper():<8} {event.duration:<12.3f}")

        if len(self.events) > max_events:
            print(f"... and {len(self.events) - max_events} more events")

        print("="*70 + "\n")

    def apply_humanization(self, target_time: float) -> float:
        """
        Add human-like timing jitter to a target time.

        Args:
            target_time: Intended trigger time

        Returns:
            Adjusted time with random jitter
        """
        if not self.humanize:
            return target_time

        # Add random jitter in the configured range
        jitter = random.uniform(*self.jitter_range)
        # 50/50 chance of being early or late
        jitter *= random.choice([-1, 1])

        return max(0, target_time + jitter)  # Don't go negative

    def play(
        self,
        countdown: int = 3,
        dry_run: bool = False,
        on_event_callback: Optional[Callable] = None
    ) -> bool:
        """
        Execute the playback sequence with high-precision timing.

        Args:
            countdown: Countdown seconds before starting (gives time to focus game)
            dry_run: If True, simulate without actually pressing keys
            on_event_callback: Optional callback for each event (event: MusicalEvent) -> None

        Returns:
            True if playback completed successfully, False if aborted
        """
        if not self.events:
            logger.warning("No events to play")
            return False

        # Sort events by time
        self.sort_events()

        # Countdown
        if countdown > 0:
            logger.info(f"Starting playback in {countdown} seconds...")
            for i in range(countdown, 0, -1):
                print(f"  {i}...")
                time.sleep(1)
            print("  GO!")

        # Playback mode indicator
        mode_str = "DRY-RUN" if dry_run else "LIVE"
        logger.info(f"Starting {mode_str} playback: {len(self.events)} events over {self.get_total_duration():.2f}s")

        self.is_playing = True
        start_time_ref = time.perf_counter()  # High-precision reference time

        try:
            for event in self.events:
                if not self.is_playing:
                    logger.info("Playback aborted by user")
                    return False

                # Calculate target time with optional humanization
                target_time = event.start_time
                if self.humanize and not dry_run:
                    target_time = self.apply_humanization(target_time)

                # Wait until target time (with drift compensation)
                current_elapsed = time.perf_counter() - start_time_ref
                sleep_duration = target_time - current_elapsed

                if sleep_duration > 0:
                    time.sleep(sleep_duration)
                elif sleep_duration < -0.1:  # More than 100ms behind
                    logger.warning(f"Timing drift detected: {abs(sleep_duration)*1000:.1f}ms behind schedule")

                # Execute the event
                actual_time = time.perf_counter() - start_time_ref

                if dry_run:
                    print(f"[{actual_time:.3f}s] DRY-RUN: {event.note_name} -> {event.key.upper()}")
                else:
                    # Call the key press callback
                    if self.key_press_callback:
                        self.key_press_callback(event.key)
                        logger.debug(f"[{actual_time:.3f}s] Pressed: {event.note_name} -> {event.key.upper()}")
                    else:
                        logger.warning("No key_press_callback configured; events not executed")

                # Call user event callback if provided
                if on_event_callback:
                    on_event_callback(event)

                # Note: We don't sleep for event.duration here because game input
                # is typically instantaneous. Duration is metadata for future features.

            logger.info(f"{mode_str} playback completed successfully")
            return True

        except Exception as e:
            logger.error(f"Playback error: {e}")
            return False
        finally:
            self.is_playing = False

    def stop(self) -> None:
        """Stop playback immediately."""
        self.is_playing = False
        logger.info("Playback stop requested")


# ============================================================================
# Example Usage and Testing
# ============================================================================

def example_key_press(key: str):
    """Example callback that simulates key pressing."""
    print(f"  >> Pressing key: {key.upper()}")


if __name__ == "__main__":
    print("PlaybackEngine Demo\n")

    # Create engine at 120 BPM with humanization
    engine = PlaybackEngine(bpm=120, humanize=True, key_press_callback=example_key_press)

    # Example 1: Simple melody using beat-based timing
    print("Example 1: Simple melody with beat timing")
    print("-" * 50)

    # At 120 BPM: quarter note = 0.5s, eighth note = 0.25s
    current_time = 0.0

    # C D E F G (quarter notes)
    notes = [('q', 'High1'), ('w', 'High2'), ('e', 'High3'), ('r', 'High4'), ('t', 'High5')]

    for key, note_name in notes:
        engine.add_event(
            key=key,
            start_time=current_time,
            duration=engine.note_duration_to_seconds(NoteDuration.QUARTER),
            note_name=note_name
        )
        current_time += engine.beats_to_seconds(1.0)  # Move forward 1 beat

    # Print timeline
    engine.print_timeline()

    # Dry-run first
    print("\nDry-run preview:")
    engine.play(countdown=1, dry_run=True)

    # Ask user if they want to execute
    print("\n" + "="*50)
    response = input("Execute live playback? (y/n): ")

    if response.lower() == 'y':
        engine.play(countdown=3, dry_run=False)

    print("\nDemo complete!")

