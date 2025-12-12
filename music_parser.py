"""
Music Parser for Game Music Player
Converts various music notation formats into timed event sequences.

Author: Python Music Architect
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from playback_engine import PlaybackEngine, NoteDuration, MusicalEvent

logger = logging.getLogger(__name__)


class MusicParser:
    """
    Parses music notation and generates timed events for the PlaybackEngine.

    Supported formats:
    - Jianpu notation: "High1 Med2 Low3"
    - Duration notation: "High1:q Med2:e Low3:h" (q=quarter, e=eighth, h=half, w=whole)
    - Wait commands: "High1 wait Med2 延音 Low3 hold"
    - BPM directives: "BPM:120 High1 High2 Med3"
    """

    def __init__(self, note_map: Dict[str, str]):
        """
        Initialize the parser with note-to-key mappings.

        Args:
            note_map: Dictionary mapping note names to keyboard keys
                     e.g., {'High1': 'q', 'Med1': 'a', 'Low1': 'z'}
        """
        self.note_map = note_map

        # Duration shortcuts
        self.duration_shortcuts = {
            'w': NoteDuration.WHOLE,
            'h': NoteDuration.HALF,
            'q': NoteDuration.QUARTER,
            'e': NoteDuration.EIGHTH,
            's': NoteDuration.SIXTEENTH,
            't': NoteDuration.THIRTY_SECOND,
        }

        # Wait command keywords (supports multiple languages)
        self.wait_keywords = ['wait', 'hold', 'sustain', '延音', '延', '-']

        # Default settings
        self.default_duration = NoteDuration.QUARTER
        self.default_wait_beats = 1.0  # How many beats to wait

        logger.info(f"MusicParser initialized with {len(note_map)} note mappings")

    def parse_to_engine(
        self,
        notation_string: str,
        engine: PlaybackEngine,
        default_bpm: float = 120.0,
        auto_spacing: bool = True
    ) -> bool:
        """
        Parse notation string and populate a PlaybackEngine with events.

        Args:
            notation_string: Music notation string
            engine: PlaybackEngine to populate
            default_bpm: Default BPM if not specified in notation
            auto_spacing: Automatically space notes by their duration

        Returns:
            True if parsing succeeded, False otherwise
        """
        engine.clear_events()

        try:
            tokens = self._tokenize(notation_string)
            current_time = 0.0
            current_bpm = default_bpm
            last_duration = self.default_duration

            engine.set_bpm(current_bpm)

            for token in tokens:
                # Check for BPM directive
                if token.startswith('BPM:'):
                    try:
                        new_bpm = float(token.split(':')[1])
                        engine.set_bpm(new_bpm)
                        current_bpm = new_bpm
                        logger.info(f"BPM changed to {new_bpm}")
                        continue
                    except (ValueError, IndexError):
                        logger.warning(f"Invalid BPM directive: {token}")
                        continue

                # Check for rest notation
                if token == '0' or token.startswith('0:'):
                    # Rest (silence)
                    if ':' in token:
                        _, duration_code = token.split(':')
                        if duration_code in self.duration_shortcuts:
                            rest_duration = self.duration_shortcuts[duration_code]
                        else:
                            rest_duration = self.default_duration
                    else:
                        rest_duration = self.default_duration

                    rest_seconds = engine.note_duration_to_seconds(rest_duration)
                    current_time += rest_seconds
                    logger.debug(f"Rest: +{rest_seconds:.3f}s")
                    continue

                # Check for wait command
                if self._is_wait_command(token):
                    wait_duration = engine.beats_to_seconds(self.default_wait_beats)
                    current_time += wait_duration
                    logger.debug(f"Wait command: +{wait_duration:.3f}s")
                    continue

                # Parse note with optional duration
                note_name, duration = self._parse_note_duration(token)

                if note_name not in self.note_map:
                    logger.warning(f"Unknown note: {note_name}")
                    continue

                # Get the keyboard key
                key = self.note_map[note_name]

                # Calculate duration in seconds
                duration_seconds = engine.note_duration_to_seconds(duration)

                # Add event
                engine.add_event(
                    key=key,
                    start_time=current_time,
                    duration=duration_seconds,
                    note_name=note_name
                )

                # Advance time if auto-spacing
                if auto_spacing:
                    current_time += duration_seconds

                last_duration = duration

            logger.info(f"Parsed {len(engine.events)} events, total duration: {engine.get_total_duration():.2f}s")
            return True

        except Exception as e:
            logger.error(f"Parsing error: {e}")
            return False

    def _tokenize(self, notation_string: str) -> List[str]:
        """
        Split notation string into individual tokens.

        Args:
            notation_string: Raw notation string

        Returns:
            List of tokens
        """
        # Split by whitespace and filter empty strings
        tokens = [t.strip() for t in notation_string.split() if t.strip()]
        return tokens

    def _is_wait_command(self, token: str) -> bool:
        """
        Check if a token is a wait command.

        Args:
            token: Token to check

        Returns:
            True if it's a wait command
        """
        return token.lower() in self.wait_keywords

    def _parse_note_duration(self, token: str) -> Tuple[str, NoteDuration]:
        """
        Parse a note token with optional duration suffix.

        Examples:
            "High1" -> ("High1", NoteDuration.QUARTER)
            "Med3:e" -> ("Med3", NoteDuration.EIGHTH)
            "Low5:h" -> ("Low5", NoteDuration.HALF)

        Args:
            token: Note token

        Returns:
            Tuple of (note_name, duration)
        """
        # Check for duration suffix (e.g., "High1:q")
        if ':' in token:
            parts = token.split(':')
            note_name = parts[0]
            duration_code = parts[1].lower()

            if duration_code in self.duration_shortcuts:
                return note_name, self.duration_shortcuts[duration_code]
            else:
                logger.warning(f"Unknown duration code '{duration_code}', using default")
                return note_name, self.default_duration

        return token, self.default_duration

    def parse_simple_notation(
        self,
        notation_string: str,
        note_delay: float = 0.1,
        wait_duration: float = 0.8
    ) -> List[Dict[str, any]]:
        """
        Parse simple notation (legacy mode) into a list of note dictionaries.
        This is for backward compatibility with the original game_music_player.py

        Args:
            notation_string: Music notation string
            note_delay: Fixed delay between notes (seconds)
            wait_duration: Fixed duration for wait commands (seconds)

        Returns:
            List of note dictionaries with 'type', 'note', 'key', 'delay'
        """
        tokens = self._tokenize(notation_string)
        result = []

        for token in tokens:
            if self._is_wait_command(token):
                result.append({
                    'type': 'wait',
                    'note': token,
                    'key': None,
                    'delay': wait_duration
                })
            else:
                note_name, _ = self._parse_note_duration(token)

                if note_name in self.note_map:
                    result.append({
                        'type': 'note',
                        'note': note_name,
                        'key': self.note_map[note_name],
                        'delay': note_delay
                    })
                else:
                    logger.warning(f"Unknown note in simple notation: {note_name}")

        return result


class KeyMapper:
    """
    Maps musical intervals to keyboard key layouts.
    Useful for generating game-specific key mappings.
    """

    @staticmethod
    def create_standard_mapping() -> Dict[str, str]:
        """
        Create the standard 3-octave mapping used by the game.

        Returns:
            Dictionary mapping note names to keys
        """
        return {
            # High Pitch notes (1-7)
            'High1': 'q', 'High2': 'w', 'High3': 'e', 'High4': 'r',
            'High5': 't', 'High6': 'y', 'High7': 'u',

            # Medium Pitch notes (1-7)
            'Med1': 'a', 'Med2': 's', 'Med3': 'd', 'Med4': 'f',
            'Med5': 'g', 'Med6': 'h', 'Med7': 'j',

            # Low Pitch notes (1-7)
            'Low1': 'z', 'Low2': 'x', 'Low3': 'c', 'Low4': 'v',
            'Low5': 'b', 'Low6': 'n', 'Low7': 'm'
        }

    @staticmethod
    def create_custom_mapping(
        high_keys: str,
        med_keys: str,
        low_keys: str
    ) -> Dict[str, str]:
        """
        Create a custom mapping with specified key layouts.

        Args:
            high_keys: 7 keys for high notes (e.g., "qwertyu")
            med_keys: 7 keys for medium notes (e.g., "asdfghj")
            low_keys: 7 keys for low notes (e.g., "zxcvbnm")

        Returns:
            Dictionary mapping note names to keys
        """
        if len(high_keys) != 7 or len(med_keys) != 7 or len(low_keys) != 7:
            raise ValueError("Each key set must contain exactly 7 keys")

        mapping = {}

        for i in range(7):
            mapping[f'High{i+1}'] = high_keys[i].lower()
            mapping[f'Med{i+1}'] = med_keys[i].lower()
            mapping[f'Low{i+1}'] = low_keys[i].lower()

        return mapping

    @staticmethod
    def print_mapping(note_map: Dict[str, str]) -> None:
        """Print a visual representation of the key mapping."""
        print("\n" + "="*60)
        print("KEY MAPPING REFERENCE")
        print("="*60)

        # Extract and sort by octave
        high_notes = sorted([(k, v) for k, v in note_map.items() if k.startswith('High')],
                           key=lambda x: x[0])
        med_notes = sorted([(k, v) for k, v in note_map.items() if k.startswith('Med')],
                          key=lambda x: x[0])
        low_notes = sorted([(k, v) for k, v in note_map.items() if k.startswith('Low')],
                          key=lambda x: x[0])

        def print_octave(octave_notes, label):
            keys = '  '.join(n[1].upper() for n in octave_notes)
            numbers = '  '.join(n[0][-1] for n in octave_notes)
            print(f"{label:12} {keys}")
            print(f"{'':12} {numbers}")

        print_octave(high_notes, "High Pitch:")
        print()
        print_octave(med_notes, "Med Pitch:")
        print()
        print_octave(low_notes, "Low Pitch:")
        print("="*60 + "\n")


# ============================================================================
# Example Usage and Testing
# ============================================================================

if __name__ == "__main__":
    print("MusicParser Demo\n")

    # Create standard key mapping
    note_map = KeyMapper.create_standard_mapping()
    KeyMapper.print_mapping(note_map)

    # Create parser and engine
    parser = MusicParser(note_map)

    # Example callback
    def example_key_press(key: str):
        print(f"  >> Key: {key.upper()}")

    engine = PlaybackEngine(bpm=120, humanize=False, key_press_callback=example_key_press)

    # Example 1: Simple melody
    print("\nExample 1: Simple melody (auto-spaced quarter notes)")
    print("-" * 60)
    notation1 = "High1 High2 High3 High4 High5"

    parser.parse_to_engine(notation1, engine)
    engine.print_timeline()
    engine.play(countdown=1, dry_run=True)

    # Example 2: Mixed durations
    print("\nExample 2: Mixed durations (q=quarter, e=eighth, h=half)")
    print("-" * 60)
    notation2 = "High1:q High2:e High3:e High4:h High5:q"

    engine.clear_events()
    parser.parse_to_engine(notation2, engine)
    engine.print_timeline()
    engine.play(countdown=1, dry_run=True)

    # Example 3: With wait commands
    print("\nExample 3: Guqin style with wait commands")
    print("-" * 60)
    notation3 = "Med1:q wait Med3:q 延音 Med5:h hold Low7:q"

    engine.clear_events()
    parser.parse_to_engine(notation3, engine)
    engine.print_timeline()
    engine.play(countdown=1, dry_run=True)

    # Example 4: BPM change mid-song
    print("\nExample 4: BPM change (starts at 120, changes to 90)")
    print("-" * 60)
    notation4 = "High1 High2 High3 BPM:90 Med1 Med2 Med3"

    engine.clear_events()
    parser.parse_to_engine(notation4, engine, default_bpm=120)
    engine.print_timeline()
    engine.play(countdown=1, dry_run=True)

    print("\nDemo complete!")

