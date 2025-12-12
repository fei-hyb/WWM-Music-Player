"""
Game Music Player - Automates musical instrument playing in PC games
Uses pydirectinput for reliable key input in DirectX games
"""

import pydirectinput
import time
import re
import random
from typing import Dict, List, Optional


class GameMusicPlayer:
    # Playing mode constants
    MODE_GUQIN = "guqin"      # Default: slow, expressive, with wait commands
    MODE_FAST = "fast"        # Fast mode: minimal delays, no waits
    MODE_CUSTOM = "custom"    # Custom: user-defined tempo multiplier

    def __init__(self, note_delay: float = 0.1, mode: str = "guqin", tempo_multiplier: float = 1.0):
        """
        Initialize the music player with note mappings and timing.
        Enhanced for Jianpu (numbered musical notation) with Guqin support.

        Args:
            note_delay: Base delay between notes in seconds (default 0.1)
            mode: Playing mode - "guqin" (default/slow), "fast", or "custom"
            tempo_multiplier: Speed multiplier (1.0 = normal, 2.0 = 2x faster, 0.5 = half speed)
        """
        self.base_note_delay = note_delay  # Store original delay
        self.note_delay = note_delay
        self.last_played_note: Optional[str] = None  # Track last note for wait commands

        # Playing mode settings
        self.mode = mode
        self.tempo_multiplier = tempo_multiplier
        self._apply_mode_settings()

        # Wait command settings for Jianpu/Guqin prolonged notes
        self.wait_duration_range = (0.5, 2.0)  # Random range for wait duration (seconds)
        self.wait_keywords = ['wait', 'hold', 'sustain', '延音', '延', '-']  # Various wait indicators

        # Musical note mappings to keyboard keys
        self.note_map: Dict[str, str] = {
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

        # Set up pydirectinput for reliable game input
        pydirectinput.FAILSAFE = True  # Move mouse to top-left to abort
        pydirectinput.PAUSE = 0.01  # Minimal pause between actions

    def _apply_mode_settings(self) -> None:
        """Apply the settings for the selected playing mode."""
        if self.mode == self.MODE_FAST:
            # Fast mode: minimal delays, skip wait commands
            self.note_delay = max(0.01, self.base_note_delay * 0.25)  # 4x faster
            self._skip_waits = True
            print(f"Fast mode: note delay {self.note_delay:.3f}s, wait commands skipped")
        elif self.mode == self.MODE_CUSTOM:
            # Custom mode: user-defined tempo multiplier
            # Higher multiplier = faster (e.g., 2.0 = 2x faster = half the delay)
            self.note_delay = max(0.01, self.base_note_delay / self.tempo_multiplier)
            self._skip_waits = self.tempo_multiplier > 1.5  # Skip waits if playing fast
            print(f"Custom mode: tempo {self.tempo_multiplier}x, note delay {self.note_delay:.3f}s")
        else:
            # Default Guqin mode: slow, expressive, with wait commands
            self.mode = self.MODE_GUQIN
            self.note_delay = self.base_note_delay
            self._skip_waits = False
            print(f"Guqin mode: expressive playing, note delay {self.note_delay:.3f}s, waits enabled")

    def set_mode(self, mode: str) -> None:
        """Set the playing mode.

        Args:
            mode: "guqin" (default/slow), "fast", or "custom"
        """
        if mode not in (self.MODE_GUQIN, self.MODE_FAST, self.MODE_CUSTOM):
            print(f"Unknown mode '{mode}'. Using 'guqin' mode.")
            mode = self.MODE_GUQIN
        self.mode = mode
        self._apply_mode_settings()

    def set_tempo(self, multiplier: float) -> None:
        """Set the tempo multiplier and switch to custom mode.

        Args:
            multiplier: Speed multiplier (1.0 = normal, 2.0 = 2x faster, 0.5 = half speed)
        """
        if multiplier <= 0:
            print("Tempo multiplier must be positive. Using 1.0.")
            multiplier = 1.0
        self.tempo_multiplier = multiplier
        self.mode = self.MODE_CUSTOM
        self._apply_mode_settings()

    def get_mode_info(self) -> str:
        """Return a string describing the current playing mode settings."""
        info = f"Mode: {self.mode}\n"
        info += f"Tempo multiplier: {self.tempo_multiplier}x\n"
        info += f"Note delay: {self.note_delay:.3f}s\n"
        info += f"Base delay: {self.base_note_delay:.3f}s\n"
        info += f"Skip waits: {getattr(self, '_skip_waits', False)}\n"
        info += f"Wait range: {self.wait_duration_range[0]:.2f}s - {self.wait_duration_range[1]:.2f}s"
        return info

    def set_note_delay(self, delay: float) -> None:
        """Set the delay between notes."""
        self.base_note_delay = delay
        self.note_delay = delay  # Update current delay
        # Reapply mode settings to adjust note delay if in custom mode
        if self.mode == self.MODE_CUSTOM:
            self.note_delay *= self.tempo_multiplier

    def set_wait_duration_range(self, min_duration: float, max_duration: float) -> None:
        """
        Set the random range for wait command durations.

        Args:
            min_duration: Minimum wait duration in seconds
            max_duration: Maximum wait duration in seconds
        """
        if min_duration <= 0 or max_duration <= min_duration:
            raise ValueError("Invalid duration range: min_duration must be > 0 and max_duration > min_duration")

        self.wait_duration_range = (min_duration, max_duration)
        print(f"Wait duration range set to {min_duration:.2f}s - {max_duration:.2f}s")

    def add_wait_keyword(self, keyword: str) -> None:
        """
        Add a custom wait keyword.

        Args:
            keyword: New wait keyword to recognize
        """
        if keyword.lower() not in self.wait_keywords:
            self.wait_keywords.append(keyword.lower())
            print(f"Added wait keyword: '{keyword}'")

    def parse_notes(self, note_string: str) -> List[str]:
        """
        Parse a string of notes into a list of individual notes or chords.

        Args:
            note_string: String containing notes like "High1 Med3 Low5" or chords "[Med1 Med3 Med5]"

        Returns:
            List of individual note strings or chord strings (with brackets)
        """
        result = []
        i = 0
        chars = note_string

        while i < len(chars):
            # Skip whitespace
            while i < len(chars) and chars[i].isspace():
                i += 1

            if i >= len(chars):
                break

            # Check for chord notation [note1 note2 ...]
            if chars[i] == '[':
                # Find matching closing bracket
                bracket_start = i
                bracket_depth = 1
                i += 1
                while i < len(chars) and bracket_depth > 0:
                    if chars[i] == '[':
                        bracket_depth += 1
                    elif chars[i] == ']':
                        bracket_depth -= 1
                    i += 1
                # Extract the chord including brackets
                chord = chars[bracket_start:i].strip()
                if chord:
                    result.append(chord)
            else:
                # Regular note - read until whitespace or bracket
                note_start = i
                while i < len(chars) and not chars[i].isspace() and chars[i] != '[':
                    i += 1
                note = chars[note_start:i].strip()
                if note:
                    result.append(note)

        return result

    # New parsing helpers for semitone support
    def _split_note_and_duration(self, token: str) -> tuple[str, Optional[str]]:
        """Split a token into base note and optional duration code.

        Examples:
            "Med#3:q" -> ("Med#3", "q")
            "High1" -> ("High1", None)
            "0:h" -> ("0", "h")
        """
        if ':' in token:
            base, duration = token.split(':', 1)
            return base, duration or None
        return token, None

    def _split_note_components(self, base: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Return (octave, accidental, degree) for a musical note without duration.

        Accepts patterns like High1, High#1, Medb3, Low7.
        Returns (None, None, None) if the string does not represent a valid musical note.
        """
        if base == '0':  # rest is handled separately by callers
            return None, None, None

        match = re.match(r'^(High|Med|Low)([#b]?)([1-7])$', base)
        if not match:
            return None, None, None

        octave, accidental, degree = match.groups()
        accidental = accidental or None
        return octave, accidental, degree

    def _get_modifier_for_accidental(self, accidental: Optional[str]) -> Optional[str]:
        """Map accidental symbol to keyboard modifier name used by pydirectinput.

        '#' -> 'shift' (higher semitone)
        'b' -> 'ctrl' (lower semitone)
        None/'' -> None
        """
        if accidental == '#':
            return 'shift'
        if accidental == 'b':
            return 'ctrl'
        return None

    def _build_base_note_key(self, octave: str, degree: str) -> str:
        """Construct the natural-note key used in self.note_map (e.g., 'High3')."""
        return f"{octave}{degree}"

    def _press_key_with_modifier(self, key: str, modifier: Optional[str]) -> None:
        """Press `key` alone, or with 'shift' / 'ctrl' held for semitones.

        Natural notes press the key directly. Sharp notes use Shift+key,
        flat notes use Ctrl+key. The modifier is held down only for the
        duration of the key press.
        """
        if modifier is None:
            pydirectinput.press(key)
            return

        # Only support shift/ctrl as modifiers
        if modifier not in ('shift', 'ctrl'):
            # Fallback to plain press if an unknown modifier is passed
            pydirectinput.press(key)
            return

        pydirectinput.keyDown(modifier)
        try:
            pydirectinput.press(key)
        finally:
            pydirectinput.keyUp(modifier)

    def is_chord(self, token: str) -> bool:
        """Check if a token is a chord notation (e.g., '[Med1 Med3 Med5]')."""
        return token.startswith('[') and token.endswith(']')

    def parse_chord(self, chord_token: str) -> List[str]:
        """Parse a chord token into individual notes.

        Args:
            chord_token: Chord string like "[Med1:q Med3:q Med5:q]"

        Returns:
            List of individual note strings
        """
        # Remove brackets and split by whitespace
        inner = chord_token[1:-1].strip()
        return [n.strip() for n in inner.split() if n.strip()]

    def validate_note(self, note: str) -> bool:
        """Validate if a note, rest, chord, or wait command is syntactically valid.

        Supports duration markers (e.g., "Med1:q", "High#3:e"), rests ("0" or "0:q"),
        chords (e.g., "[Med1 Med3 Med5]"), and wait keywords.
        """
        # Check if it's a chord
        if self.is_chord(note):
            chord_notes = self.parse_chord(note)
            # All notes in the chord must be valid
            return all(self._validate_single_note(n) for n in chord_notes)

        return self._validate_single_note(note)

    def _validate_single_note(self, note: str) -> bool:
        """Validate a single note (not a chord)."""
        # Check if it's a wait command
        if self.is_wait_command(note):
            return True

        # Split base token and optional duration
        base, duration_code = self._split_note_and_duration(note)

        # Handle rest symbols
        if base == '0':
            # Accept "0" and "0:<duration>"
            if duration_code is None:
                return True
            return duration_code in {'w', 'h', 'q', 'e', 's', 't'}

        # Validate duration code for musical notes, if present
        if duration_code is not None and duration_code not in {'w', 'h', 'q', 'e', 's', 't'}:
            return False

        # Parse musical note components
        octave, accidental, degree = self._split_note_components(base)
        if octave is None or degree is None:
            return False

        base_key = self._build_base_note_key(octave, degree)
        if base_key not in self.note_map:
            # If the natural base note isn't mapped, any accidental variation is invalid
            return False

        # Accidentals "#" and "b" are accepted implicitly via parsing above
        return True

    def is_wait_command(self, command: str) -> bool:
        """
        Check if a command is a wait/sustain instruction.

        Args:
            command: Command string to check

        Returns:
            True if it's a wait command, False otherwise
        """
        command_lower = command.lower().strip()
        return command_lower in self.wait_keywords

    def _get_duration_from_code(self, duration_code: Optional[str]) -> float:
        """Map a duration code to seconds, scaled by tempo. Defaults to quarter-note (0.5s)."""
        duration_map = {
            'w': 2.0,   # Whole note
            'h': 1.0,   # Half note
            'q': 0.5,   # Quarter note
            'e': 0.25,  # Eighth note
            's': 0.125, # Sixteenth note
            't': 0.06   # Thirty-second note
        }
        base_duration = duration_map.get(duration_code, 0.5) if duration_code else 0.5

        # Scale duration by tempo (faster tempo = shorter durations)
        if self.mode == self.MODE_FAST:
            return base_duration * 0.25  # 4x faster in fast mode
        elif self.mode == self.MODE_CUSTOM and self.tempo_multiplier != 1.0:
            return base_duration / self.tempo_multiplier
        return base_duration

    def play_single_note(self, note: str) -> bool:
        """Play a single note, rest, or execute a wait command.

        Supports duration markers (e.g., "Med1:q", "High#3:e"), rests ("0" or "0:q"),
        and semitone notes using Shift (sharp) and Ctrl (flat).
        """
        # Handle chords (simultaneous notes)
        if self.is_chord(note):
            return self.play_chord(note)

        # Handle wait commands
        if self.is_wait_command(note):
            return self.execute_wait_command(note)

        # Split base token and optional duration
        base, duration_code = self._split_note_and_duration(note)

        # Handle rest symbols (silence): "0" or "0:<duration>"
        if base == '0':
            rest_duration = self._get_duration_from_code(duration_code)
            print(f"Rest (silence) for {rest_duration:.3f}s")
            time.sleep(rest_duration)
            return True

        # Parse musical note components
        octave, accidental, degree = self._split_note_components(base)
        if octave is None or degree is None:
            print(f"Warning: Unknown note '{base}' - skipping")
            return False

        # Validate base natural note exists in mapping
        base_key = self._build_base_note_key(octave, degree)
        if base_key not in self.note_map:
            print(f"Warning: Unknown note '{base}' (base key '{base_key}' not mapped) - skipping")
            return False

        key = self.note_map[base_key]
        modifier = self._get_modifier_for_accidental(accidental)

        try:
            # Perform the key press with appropriate modifier
            self._press_key_with_modifier(key, modifier)

            # Determine how long this note should last
            sleep_duration = self._get_duration_from_code(duration_code)

            # Map duration markers to human-readable names for logging
            if duration_code:
                duration_names = {
                    'w': 'whole', 'h': 'half', 'q': 'quarter',
                    'e': 'eighth', 's': 'sixteenth', 't': '32nd'
                }
                duration_name = duration_names.get(duration_code, duration_code)
            else:
                duration_name = None

            # Build a description of what was played
            if modifier == 'shift':
                modifier_desc = 'Shift+'
            elif modifier == 'ctrl':
                modifier_desc = 'Ctrl+'
            else:
                modifier_desc = ''

            if duration_name:
                print(f"Played note: {base} ({duration_name}) -> {modifier_desc}{key.upper()}")
            else:
                print(f"Played note: {base} -> {modifier_desc}{key.upper()}")

            # Sleep for the musical duration (note length)
            time.sleep(sleep_duration)

            # Track last played note (including accidental if present) for wait commands
            self.last_played_note = base
            return True
        except Exception as e:
            print(f"Error playing note {base}: {e}")
            return False

    def play_chord(self, chord_token: str) -> bool:
        """Play a chord by pressing multiple keys simultaneously.

        Args:
            chord_token: Chord string like "[Med1:q Med3:q Med5:q]"

        Returns:
            True if chord was played successfully, False otherwise
        """
        chord_notes = self.parse_chord(chord_token)
        if not chord_notes:
            print(f"Warning: Empty chord '{chord_token}' - skipping")
            return False

        # Prepare all keys and modifiers to press
        keys_to_press = []
        max_duration = 0.0

        for note in chord_notes:
            base, duration_code = self._split_note_and_duration(note)

            # Skip rests in chords
            if base == '0':
                continue

            octave, accidental, degree = self._split_note_components(base)
            if octave is None or degree is None:
                print(f"Warning: Unknown note '{base}' in chord - skipping")
                continue

            base_key = self._build_base_note_key(octave, degree)
            if base_key not in self.note_map:
                print(f"Warning: Unknown note '{base}' in chord - skipping")
                continue

            key = self.note_map[base_key]
            modifier = self._get_modifier_for_accidental(accidental)
            keys_to_press.append((key, modifier, note))

            # Track the longest duration in the chord
            note_duration = self._get_duration_from_code(duration_code)
            max_duration = max(max_duration, note_duration)

        if not keys_to_press:
            return False

        try:
            # Press all modifier keys first
            modifiers_held = set()
            for key, modifier, note in keys_to_press:
                if modifier and modifier not in modifiers_held:
                    pydirectinput.keyDown(modifier)
                    modifiers_held.add(modifier)

            # Press all note keys simultaneously
            for key, modifier, note in keys_to_press:
                pydirectinput.keyDown(key)

            # Brief hold for the chord to register
            time.sleep(0.02)

            # Release all note keys
            for key, modifier, note in keys_to_press:
                pydirectinput.keyUp(key)

            # Release all modifier keys
            for modifier in modifiers_held:
                pydirectinput.keyUp(modifier)

            # Log what was played
            note_names = [n for _, _, n in keys_to_press]
            print(f"Played chord: [{' '.join(note_names)}]")

            # Track the last played note (use the first note of the chord)
            self.last_played_note = chord_notes[0]

            # Sleep for the chord duration
            time.sleep(max_duration)

            return True

        except Exception as e:
            # Make sure to release any held keys on error
            for key, modifier, note in keys_to_press:
                try:
                    pydirectinput.keyUp(key)
                except:
                    pass
            for modifier in modifiers_held:
                try:
                    pydirectinput.keyUp(modifier)
                except:
                    pass
            print(f"Error playing chord: {e}")
            return False

    def execute_wait_command(self, wait_command: str) -> bool:
        """
        Execute a wait command to prolong the previous note's echo.

        Args:
            wait_command: The wait command string

        Returns:
            True if wait was executed successfully, False otherwise
        """
        # Skip waits in fast mode
        if getattr(self, '_skip_waits', False):
            print(f"Skipping wait command '{wait_command}' (fast mode)")
            return True

        if not self.last_played_note:
            print(f"Warning: '{wait_command}' command ignored - no previous note to sustain")
            return False

        # Generate random wait duration for natural feel
        wait_duration = random.uniform(*self.wait_duration_range)

        # Scale wait duration by tempo (faster tempo = shorter waits)
        if self.mode == self.MODE_CUSTOM and self.tempo_multiplier > 1.0:
            wait_duration = wait_duration / self.tempo_multiplier

        print(f"Sustaining {self.last_played_note} for {wait_duration:.2f}s ({wait_command})")
        time.sleep(wait_duration)
        return True

    def play_song(self, song_string: str, countdown: int = 3) -> None:
        """Play a complete song from a string of notes with Jianpu wait support."""
        notes = self.parse_notes(song_string)

        if not notes:
            print("No valid notes found in the song string.")
            return

        # Reset last played note at start of song
        self.last_played_note = None

        # Validate all notes and commands first
        invalid_items = []
        wait_count = 0
        note_count = 0

        for item in notes:
            if self.is_wait_command(item):
                wait_count += 1
            elif self.validate_note(item):
                # Count musical notes (not rests) as notes
                base, _ = self._split_note_and_duration(item)
                if base != '0':
                    note_count += 1
            else:
                invalid_items.append(item)

        if invalid_items:
            print(f"Warning: Invalid items found: {invalid_items}")
            response = input("Continue anyway? (y/n): ").lower().strip()
            if response != 'y':
                return

        print(f"\nPreparing to play {note_count} notes with {wait_count} wait commands...")
        print(f"Note delay: {self.note_delay}s")
        print(f"Wait range: {self.wait_duration_range[0]:.2f}s - {self.wait_duration_range[1]:.2f}s")

        # Countdown to give time to focus the game window
        for i in range(countdown, 0, -1):
            print(f"Starting in {i}...")
            time.sleep(1)

        print("Playing song with Jianpu wait support!")

        # Play each note/command
        for i, item in enumerate(notes, 1):
            if self.validate_note(item):
                success = self.play_single_note(item)

                # Add delay between items (except after the last item)
                # Skip delay after wait commands since they include their own timing
                if i < len(notes) and success and not self.is_wait_command(item):
                    time.sleep(self.note_delay)

        print("Song completed!")

    def display_note_map(self) -> None:
        """Display the current note mapping, semitone info, and wait commands for reference."""
        print("\n=== Jianpu Music Player - Note Mapping ===")
        print("High Pitch: Q W E R T Y U")
        print("           1 2 3 4 5 6 7")
        print()
        print("Medium Pitch: A S D F G H J")
        print("             1 2 3 4 5 6 7")
        print()
        print("Low Pitch: Z X C V B N M")
        print("          1 2 3 4 5 6 7")
        print()
        # Semitone usage information, matching in-game Guqin layout
        print("Semitones: #1, b3, #4, #5, b7 between natural degrees.")
        print("Hold Shift for higher semitone (#), Ctrl for lower semitone (b)")
        print("Example semitone input: High1 High#1 High2 Medb3 Med3 Med#4 Low5 Low#5 Low6 Lowb7 Low7")
        print()
        print("=== Wait Commands for Guqin Sustain ===")
        print(f"Keywords: {', '.join(self.wait_keywords)}")
        print(f"Duration: {self.wait_duration_range[0]:.2f}s - {self.wait_duration_range[1]:.2f}s (random)")
        print()
        print("Example usage: High1 wait Med3 hold Low5 延音")
        print("Wait commands prolong the echo of the previous note")
        print("Perfect for Guqin and other sustained instruments")
        print("=============================================\n")


def main():
    """Main function with command-line interface."""
    player = GameMusicPlayer()

    print("=== Game Music Player ===")
    print("Automates musical instrument playing in PC games")
    print("Make sure the game window is active when playing!")
    print()

    while True:
        print("\nOptions:")
        print("1. Play a song")
        print("2. Show note mapping")
        print("3. Change note delay")
        print("4. Quit")

        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == '1':
            print("\nPaste your song string (notes separated by spaces):")
            print("Example: High1 High2 Med3 Low5 High7")
            song = input("Song: ").strip()

            if song:
                print(f"\nCurrent delay between notes: {player.note_delay}s")
                change_delay = input("Change delay? (y/n): ").lower().strip()

                if change_delay == 'y':
                    try:
                        new_delay = float(input("Enter new delay in seconds: "))
                        player.set_note_delay(new_delay)
                        print(f"Delay set to {new_delay}s")
                    except ValueError:
                        print("Invalid delay value, keeping current setting")

                player.play_song(song)
            else:
                print("No song entered.")

        elif choice == '2':
            player.display_note_map()

        elif choice == '3':
            try:
                new_delay = float(input("Enter new delay in seconds: "))
                player.set_note_delay(new_delay)
                print(f"Delay set to {new_delay}s")
            except ValueError:
                print("Invalid delay value.")


        elif choice == '4':
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1-4.")


if __name__ == "__main__":
    main()
