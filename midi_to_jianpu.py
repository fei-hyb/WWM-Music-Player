"""
MIDI to Jianpu Transcriber
Converts MIDI files to Jianpu notation for the game music player
"""

import os
import logging
from typing import List, Optional, Tuple, Dict
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MIDIToJianpuTranscriber:
    """
    Transcribes MIDI files to Jianpu notation compatible with the game music player.
    """

    def __init__(self,
                 playable_min: int = 36,
                 playable_max: int = 107,
                 debug: bool = False):
        # Expanded / configurable playable MIDI range
        self.playable_min = playable_min
        self.playable_max = playable_max

        # MIDI note number to Jianpu mapping with chromatic handling.
        # For each pitch class (0-11), store (degree, accidental) where:
        #   degree: 1-7 (Jianpu scale degree)
        #   accidental: None for natural, '#' for sharp, 'b' for flat
        # C4 (middle C) = MIDI note 60 = Jianpu Med1 (do)
        self.midi_to_jianpu_base: Dict[int, Tuple[int, Optional[str]]] = {
            0: (1, None),   # C  -> 1
            1: (1, '#'),    # C# -> #1
            2: (2, None),   # D  -> 2
            3: (3, 'b'),    # D# -> b3
            4: (3, None),   # E  -> 3
            5: (4, None),   # F  -> 4
            6: (4, '#'),    # F# -> #4
            7: (5, None),   # G  -> 5
            8: (5, '#'),    # G# -> #5
            9: (6, None),   # A  -> 6
            10: (7, 'b'),   # A# -> b7
            11: (7, None),  # B  -> 7
        }

        # Octave ranges for pitch designation
        # Must cover the full playable range (36-107) to avoid notes falling into "Unknown"
        # Each range spans 2 octaves (24 semitones) for balanced coverage
        self.octave_ranges = {
            'Low': (36, 59),     # C2-B3 (2 octaves of low range)
            'Med': (60, 83),     # C4-B5 (2 octaves of middle range)
            'High': (84, 107),   # C6-B7 (2 octaves of high range)
        }

        # Default settings - favor accuracy over filtering
        # High max_notes to handle long/complex MIDIs without truncation.
        # For a 50+ minute MIDI with heavy polyphony, we may have 5000+ notes.
        self.max_notes = 100000  # Essentially unlimited - let the full MIDI through
        self.min_duration = 0.001  # Keep almost all notes (only filter out extremely short artifacts)
        self.add_wait_commands = True  # Add wait commands for longer notes
        self.wait_threshold = 0.3  # Lower threshold for more natural expression
        self.remove_duplicates = False  # Keep all notes by default for 1:1 conversion
        self.duplicate_threshold = 0.05  # Time window for duplicate removal (if enabled)

        # Chord detection window (seconds)
        self.chord_time_window = 0.05

        # Polyphonic mode: output chords as [note1 note2 note3] for simultaneous playback
        # When True, chords are grouped with brackets for the player to press keys simultaneously
        # When False, chord notes are output sequentially (legacy behavior)
        self.polyphonic_mode = True

        # Multi-track MIDI handling options
        self.exclude_drums = True  # Exclude MIDI channel 10 (drums/percussion)
        self.max_chord_size = 3    # Maximum notes in a chord (0 = unlimited)
        self.melody_track_only = False  # If True, only use the track with highest average pitch
        self.selected_tracks = None  # List of track indices to include, or None for all

        # Debug flag for extra logging about filtering/mapping
        self.debug = debug

    def set_debug(self, enabled: bool = True) -> None:
        """Enable or disable verbose debug logging for transcription internals."""
        self.debug = enabled
        logger.info(f"MIDIToJianpuTranscriber debug mode set to {self.debug}")

    def transcribe_midi_file(self, midi_path: str) -> Optional[str]:
        """
        Transcribe a MIDI file to Jianpu notation.

        Args:
            midi_path: Path to the MIDI file

        Returns:
            Jianpu notation string or None if failed
        """
        if not os.path.exists(midi_path):
            logger.error(f"MIDI file not found: {midi_path}")
            return None

        try:
            # Try different MIDI libraries
            result = self._try_mido_transcription(midi_path)
            if result:
                return result

            result = self._try_music21_transcription(midi_path)
            if result:
                return result

            result = self._try_pretty_midi_transcription(midi_path)
            if result:
                return result

            logger.warning("Could not transcribe MIDI file with available libraries")
            return None

        except Exception as e:
            logger.error(f"Error transcribing MIDI file: {e}")
            return None

    def _try_mido_transcription(self, midi_path: str) -> Optional[str]:
        """Try transcribing using mido library with improved timing accuracy."""
        try:
            import mido

            logger.info("Attempting transcription with mido...")

            mid = mido.MidiFile(midi_path)
            all_notes = []

            # If melody_track_only is set, find the best melody track
            if self.melody_track_only:
                best_track_idx = self._find_melody_track(mid)
                logger.info(f"Melody track mode: using track {best_track_idx}")
                tracks_to_use = [mid.tracks[best_track_idx]]
            elif self.selected_tracks is not None:
                tracks_to_use = [mid.tracks[i] for i in self.selected_tracks if i < len(mid.tracks)]
                logger.info(f"Using selected tracks: {self.selected_tracks}")
            else:
                tracks_to_use = mid.tracks

            # Merge selected tracks into a single timeline
            merged_track = mido.merge_tracks(tracks_to_use)

            # Track note states for proper duration calculation
            # {(channel, note_number): (start_time_seconds, velocity, tempo_at_note_on)}
            active_notes = {}
            current_time = 0
            tempo = 500000  # Default tempo (120 BPM)
            ticks_per_beat = mid.ticks_per_beat

            # Track current channel for each note
            current_channel = 0

            for msg in merged_track:
                # Convert ticks to seconds
                if msg.time > 0:
                    seconds_per_tick = tempo / (1000000 * ticks_per_beat)
                    current_time += msg.time * seconds_per_tick

                # Handle tempo changes
                if msg.type == 'set_tempo':
                    tempo = msg.tempo
                    logger.debug(f"Tempo change at {current_time:.2f}s: {60000000/tempo:.1f} BPM")

                # Handle note on events
                elif msg.type == 'note_on' and msg.velocity > 0:
                    channel = getattr(msg, 'channel', 0)

                    # Skip drum channel (channel 9 in 0-indexed, channel 10 in 1-indexed)
                    if self.exclude_drums and channel == 9:
                        continue

                    # Store both start time and velocity with channel
                    active_notes[(channel, msg.note)] = (current_time, msg.velocity, tempo)

                # Handle note off events (including note_on with velocity 0)
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    channel = getattr(msg, 'channel', 0)
                    key = (channel, msg.note)

                    if key in active_notes:
                        start_time, velocity, tempo_at_on = active_notes[key]
                        duration = current_time - start_time
                        seconds_per_beat = max(tempo_at_on / 1000000.0, 0.001)
                        duration_beats = duration / seconds_per_beat

                        # Convert MIDI note to Jianpu
                        jianpu_note = self._midi_note_to_jianpu(msg.note)
                        if jianpu_note:
                            # Store velocity normalized to 0-1
                            all_notes.append((start_time, jianpu_note, duration, velocity / 127.0, duration_beats))

                        del active_notes[key]

            # Handle any remaining active notes (songs that don't end cleanly)
            for (channel, note_num), (start_time, velocity, _tempo_at_on) in active_notes.items():
                jianpu_note = self._midi_note_to_jianpu(note_num)
                if jianpu_note:
                    duration = 0.5  # Default duration for unclosed notes
                    all_notes.append((start_time, jianpu_note, duration, velocity / 127.0, 1.0))

            if all_notes:
                # Sort by time and convert to string
                all_notes.sort(key=lambda x: x[0])
                return self._notes_to_jianpu_string_advanced(all_notes)

        except ImportError:
            logger.info("mido library not available")
        except Exception as e:
            logger.warning(f"mido transcription failed: {e}")

        return None

    def _find_melody_track(self, mid) -> int:
        """Find the track most likely to be the melody based on name, pitch range, and note count."""
        best_track = 0
        best_score = -1

        # Keywords that suggest melody tracks (case-insensitive)
        melody_keywords = ['melody', 'lead', 'vocal', 'voice', 'flute', 'violin', 'solo']
        # Keywords that suggest non-melody tracks
        avoid_keywords = ['drum', 'bass', 'chord', 'pad', 'percussion', 'kick', 'snare', 'hat']

        for i, track in enumerate(mid.tracks):
            notes = []
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    channel = getattr(msg, 'channel', 0)
                    # Skip drum channel
                    if channel == 9:
                        continue
                    notes.append(msg.note)

            if not notes:
                continue

            # Base score from pitch and note count
            avg_pitch = sum(notes) / len(notes)
            note_count = len(notes)

            # Prefer tracks with notes in the melody range (60-84) and not too many notes
            melody_range_notes = sum(1 for n in notes if 60 <= n <= 84)
            melody_ratio = melody_range_notes / len(notes) if notes else 0

            # Base score: high average pitch + good melody ratio + reasonable note count
            score = avg_pitch * 0.5 + melody_ratio * 30 + min(note_count, 500) * 0.1

            # Check track name for hints
            track_name = (track.name or "").lower()

            # Big bonus for melody-related names
            for keyword in melody_keywords:
                if keyword in track_name:
                    score += 50  # Strong preference
                    break

            # Penalty for non-melody track names
            for keyword in avoid_keywords:
                if keyword in track_name:
                    score -= 30
                    break

            if score > best_score:
                best_score = score
                best_track = i

        return best_track

    def _try_music21_transcription(self, midi_path: str) -> Optional[str]:
        """Try transcribing using music21 library."""
        try:
            from music21 import converter, note, stream, pitch

            logger.info("Attempting transcription with music21...")

            # Load MIDI file
            score = converter.parse(midi_path)
            notes = []

            # Extract notes from the score
            for element in score.flat.notes:
                if isinstance(element, note.Note):
                    midi_note = element.pitch.midi
                    jianpu_note = self._midi_note_to_jianpu(midi_note)
                    if jianpu_note:
                        duration = float(element.quarterLength)
                        offset = float(element.offset)
                        notes.append((offset, jianpu_note, duration, 0.8, duration))

                elif isinstance(element, note.Chord):
                    # For chords, take the highest note
                    highest = max(element.notes, key=lambda n: n.pitch.midi)
                    midi_note = highest.pitch.midi
                    jianpu_note = self._midi_note_to_jianpu(midi_note)
                    if jianpu_note:
                        duration = float(element.quarterLength)
                        offset = float(element.offset)
                        notes.append((offset, jianpu_note, duration, 0.8, duration))

            if notes:
                # Sort by time and convert to string
                notes.sort(key=lambda x: x[0])
                return self._notes_to_jianpu_string_advanced(notes)

        except ImportError:
            logger.info("music21 library not available")
        except Exception as e:
            logger.warning(f"music21 transcription failed: {e}")

        return None

    def _try_pretty_midi_transcription(self, midi_path: str) -> Optional[str]:
        """Try transcribing using pretty_midi library."""
        try:
            import pretty_midi

            logger.info("Attempting transcription with pretty_midi...")

            # Load MIDI file
            midi_data = pretty_midi.PrettyMIDI(midi_path)
            notes = []

            # Extract notes from all instruments
            for instrument in midi_data.instruments:
                if not instrument.is_drum:  # Skip drum tracks
                    for note in instrument.notes:
                        jianpu_note = self._midi_note_to_jianpu(note.pitch)
                        if jianpu_note:
                            duration = note.end - note.start
                            notes.append((note.start, jianpu_note, duration, 0.8, None))

            if notes:
                # Sort by time and convert to string
                notes.sort(key=lambda x: x[0])
                return self._notes_to_jianpu_string_advanced(notes)

        except ImportError:
            logger.info("pretty_midi library not available")
        except Exception as e:
            logger.warning(f"pretty_midi transcription failed: {e}")

        return None

    def _clamp_midi_to_playable_range(self, midi_note: int) -> int:
        """Transpose a MIDI note into the configured playable range by octaves.

        - If within [playable_min, playable_max], return as-is.
        - If above max, transpose down by 12 until <= max.
        - If below min, transpose up by 12 until >= min.

        This preserves pitch class (for semitone mapping) while ensuring every
        note is representable by High/Med/Low ranges instead of being dropped.
        """
        note = midi_note
        if self.playable_min is None or self.playable_max is None:
            return note

        # Bring high notes down
        while note > self.playable_max:
            note -= 12
        # Bring low notes up
        while note < self.playable_min:
            note += 12
        return note

    def _midi_note_to_jianpu(self, midi_note: int) -> Optional[str]:
        """Convert MIDI note number to Jianpu notation with semitone-aware mapping.

        Returns note names like "High1", "Med#3", "Lowb7" that align with
        GameMusicPlayer's parsing of accidentals.
        """
        # First, clamp into playable range by octaves so notes are not lost
        clamped_note = self._clamp_midi_to_playable_range(midi_note)

        # If clamping still leaves it outside (e.g. extreme config), drop it
        if clamped_note < self.playable_min or clamped_note > self.playable_max:
            if self.debug:
                logger.debug(
                    f"Dropping MIDI note {midi_note} (clamped to {clamped_note}) "
                    f"outside playable range {self.playable_min}-{self.playable_max}"
                )
            return None

        midi_note = clamped_note

        # Determine octave range label: Low / Med / High
        pitch_range = "Med"  # Default
        for range_name, (low, high) in self.octave_ranges.items():
            if low <= midi_note <= high:
                pitch_range = range_name
                break

        # Get note within octave (0-11)
        note_in_octave = midi_note % 12

        # Look up Jianpu degree and accidental
        mapping = self.midi_to_jianpu_base.get(note_in_octave)
        if mapping is None:
            # Fallback to degree 1 natural if something unexpected occurs
            degree, accidental = 1, None
        else:
            degree, accidental = mapping

        # Build Jianpu label with optional accidental
        if accidental:
            jianpu_label = f"{pitch_range}{accidental}{degree}"
        else:
            jianpu_label = f"{pitch_range}{degree}"

        return jianpu_label

    def _get_midi_from_jianpu(self, jianpu: str) -> int:
        """Get approximate MIDI note number from Jianpu label for sorting purposes.

        Returns higher values for higher pitches. Used for chord sorting.
        """
        import re

        # Parse: High#3, Med1, Lowb7, etc.
        match = re.match(r'(High|Med|Low)([#b]?)(\d)', jianpu)
        if not match:
            return 60  # Default to middle C

        range_name, accidental, degree = match.groups()
        degree = int(degree)

        # Base MIDI for each range
        range_base = {'Low': 48, 'Med': 60, 'High': 72}
        base = range_base.get(range_name, 60)

        # Jianpu degree to semitone offset (1=C, 2=D, 3=E, 4=F, 5=G, 6=A, 7=B)
        degree_offsets = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}
        offset = degree_offsets.get(degree, 0)

        # Apply accidental
        if accidental == '#':
            offset += 1
        elif accidental == 'b':
            offset -= 1

        return base + offset

    def _estimate_note_duration(self, track, note_msg, current_time) -> float:
        """Estimate note duration from MIDI track (simplified)."""
        # This is a simplified estimation - in practice you'd track note_off events
        return 0.5  # Default duration

    def _notes_to_jianpu_string(self, notes: List[Tuple[float, str, float]]) -> str:
        """
        Convert list of timed notes to Jianpu string with improved timing and expression.

        Args:
            notes: List of (time, jianpu_note, duration) tuples

        Returns:
            Jianpu notation string
        """
        # Convert to advanced format with default velocity
        notes_with_velocity = [(t, n, d, 0.8, None) for t, n, d in notes]
        return self._notes_to_jianpu_string_advanced(notes_with_velocity)

    def _notes_to_jianpu_string_advanced(self, notes: List[Tuple[float, str, float, float, Optional[float]]]) -> str:
        """
        Advanced conversion with chord detection and accurate rhythm preservation.

        Args:
            notes: List of (time, jianpu_note, duration, velocity) tuples

        Returns:
            Jianpu notation string with duration markers
        """
        if not notes:
            return ""

        total_raw = len(notes)

        # Filter out very short notes (likely grace notes or noise)
        filtered_notes = [(t, n, d, v, b) for t, n, d, v, b in notes if d >= self.min_duration]
        after_duration = len(filtered_notes)

        # Remove rapid duplicates if enabled
        if self.remove_duplicates:
            filtered_notes = self._remove_duplicate_notes_advanced(filtered_notes)
        after_duplicates = len(filtered_notes)

        # Limit number of notes for game performance
        if len(filtered_notes) > self.max_notes:
            if self.debug:
                logger.info(f"Limiting notes from {len(filtered_notes)} to first {self.max_notes}")
            filtered_notes = filtered_notes[:self.max_notes]
        after_trunc = len(filtered_notes)

        if not filtered_notes:
            if self.debug:
                logger.info("All notes filtered out after duration/duplicate/truncation steps.")
            return ""

        if self.debug:
            logger.info(
                f"Note filtering: raw={total_raw}, after_duration>={self.min_duration}s -> {after_duration}, "
                f"after_duplicates -> {after_duplicates}, after_trunc -> {after_trunc}"
            )

        jianpu_sequence: List[str] = []
        i = 0

        # Helper to roughly classify by label prefix for debug
        def _range_from_label(label: str) -> str:
            if label.startswith('Low'):
                return 'Low'
            if label.startswith('Med'):
                return 'Med'
            if label.startswith('High'):
                return 'High'
            return 'Other'

        range_counts = {'Low': 0, 'Med': 0, 'High': 0, 'Other': 0}

        while i < len(filtered_notes):
            time, note, duration, velocity, beats = filtered_notes[i]
            selected_dur = duration
            selected_beats = beats

            # Detect chords (notes starting at nearly the same time)
            chord_group = [(time, note, duration, velocity, beats)]
            j = i + 1

            while j < len(filtered_notes):
                next_time, next_note, next_dur, next_vel, next_beats = filtered_notes[j]
                if abs(next_time - time) <= self.chord_time_window:
                    chord_group.append((next_time, next_note, next_dur, next_vel, next_beats))
                    j += 1
                else:
                    break

            if len(chord_group) > 1:
                # Multiple notes at the same time - output as chord
                if self.polyphonic_mode:
                    # Apply max_chord_size limit if set
                    if self.max_chord_size > 0 and len(chord_group) > self.max_chord_size:
                        # Sort by pitch (higher notes first - usually melody) then by velocity
                        chord_group.sort(key=lambda x: (-self._get_midi_from_jianpu(x[1]), -x[3]))
                        chord_group = chord_group[:self.max_chord_size]

                    # Output chord in bracket notation for simultaneous key presses
                    chord_notes = []
                    for chord_time, chord_note, chord_dur, chord_vel, chord_beats in chord_group:
                        note_with_duration = self._add_duration_marker(chord_note, chord_dur, chord_beats)
                        chord_notes.append(note_with_duration)
                        range_counts[_range_from_label(chord_note)] += 1
                    # Format: [Med1:q Med3:q Med5:q] for simultaneous playback
                    jianpu_sequence.append("[" + " ".join(chord_notes) + "]")
                    selected_dur = max((c[2] for c in chord_group), default=duration)
                    selected_beats = max((c[4] for c in chord_group if c[4] is not None), default=beats)
                else:
                    # Legacy: output all notes in the chord group sequentially
                    for chord_time, chord_note, chord_dur, chord_vel, chord_beats in chord_group:
                        note_with_duration = self._add_duration_marker(chord_note, chord_dur, chord_beats)
                        jianpu_sequence.append(note_with_duration)
                        range_counts[_range_from_label(chord_note)] += 1
                    selected_dur = max((c[2] for c in chord_group), default=duration)
                    selected_beats = max((c[4] for c in chord_group if c[4] is not None), default=beats)
            else:
                selected_time, selected_note, selected_dur, selected_vel, selected_beats = chord_group[0]
                note_with_duration = self._add_duration_marker(selected_note, selected_dur, selected_beats)
                jianpu_sequence.append(note_with_duration)
                range_counts[_range_from_label(selected_note)] += 1

            # Calculate gap to next note (if not part of current chord)
            next_idx = j if j > i + 1 else i + 1
            if next_idx < len(filtered_notes):
                next_time = filtered_notes[next_idx][0]
                gap = next_time - (time + duration)

                # Add gap marker only when configured and gap exceeds threshold.
                if self.add_wait_commands and gap > self.wait_threshold:
                    # Derive a rough beat estimate for the gap from the current note.
                    sec_per_beat = selected_dur / selected_beats if (selected_beats and selected_beats > 0) else None
                    gap_beats = (gap / sec_per_beat) if sec_per_beat else None
                    jianpu_sequence.append(self._add_duration_marker("0", gap, gap_beats))

            i = next_idx

        if self.debug:
            logger.info(
                f"Final Jianpu sequence stats: total_items={len(jianpu_sequence)}, "
                f"ranges={range_counts}"
            )

        result = " ".join(jianpu_sequence)
        logger.info(f"Transcribed {after_trunc} notes (chords collapsed) to: {result[:100]}...")

        return result

    def _duration_code_from_beats(self, beats: float) -> str:
        """Quantize beat length to duration code."""
        if beats >= 3.0:
            return 'w'
        if beats >= 1.5:
            return 'h'
        if beats >= 0.75:
            return 'q'
        if beats >= 0.375:
            return 'e'
        if beats >= 0.1875:
            return 's'
        return 't'

    def _duration_code_from_seconds(self, duration: float) -> str:
        """Fallback quantization when beat information is unavailable."""
        if duration >= 2.0:
            return 'w'
        if duration >= 1.0:
            return 'h'
        if duration >= 0.5:
            return 'q'
        if duration >= 0.25:
            return 'e'
        if duration >= 0.125:
            return 's'
        return 't'

    def _add_duration_marker(self, note: str, duration: float, duration_beats: Optional[float] = None) -> str:
        """
        Add duration marker to note based on musical timing.

        Args:
            note: Jianpu note (e.g., "High1")
            duration: Duration in seconds

        Returns:
            Note with duration marker (e.g., "High1:q" for quarter note)
        """
        if duration_beats is not None and duration_beats > 0:
            code = self._duration_code_from_beats(duration_beats)
        else:
            code = self._duration_code_from_seconds(duration)
        return f"{note}:{code}"

    def _remove_duplicate_notes_advanced(self, notes: List[Tuple[float, str, float, float, Optional[float]]]) -> List[Tuple[float, str, float, float, Optional[float]]]:
        """Remove rapid repeated notes with velocity awareness."""
        if not notes:
            return notes

        filtered = [notes[0]]  # Always keep the first note

        for time, note, duration, velocity, beats in notes[1:]:
            last_time, last_note, _, last_velocity, _ = filtered[-1]

            # If it's the same note within the threshold time, keep only louder one
            if note == last_note and (time - last_time) < self.duplicate_threshold:
                # Replace if current note is louder
                if velocity > last_velocity:
                    filtered[-1] = (time, note, duration, velocity, beats)
                continue

            filtered.append((time, note, duration, velocity, beats))

        return filtered

    def set_transcription_options(self, max_notes: int = 2000,
                                min_duration: float = 0.05,
                                add_waits: bool = True,
                                wait_threshold: float = 0.3,
                                remove_duplicates: bool = True,
                                duplicate_threshold: float = 0.1):
        """Configure transcription options for better accuracy and length control.

        max_notes controls how many notes are kept after filtering. Increase this
        if long MIDIs are being cut short; decrease it if you only want a short
        excerpt or need to limit playback length in-game.
        """
        self.max_notes = max_notes
        self.min_duration = min_duration
        self.add_wait_commands = add_waits
        self.wait_threshold = wait_threshold
        self.remove_duplicates = remove_duplicates
        self.duplicate_threshold = duplicate_threshold

        logger.info(f"Transcription options updated: max_notes={max_notes}, "
                   f"min_duration={min_duration}, add_waits={add_waits}, "
                   f"wait_threshold={wait_threshold}, remove_duplicates={remove_duplicates}")

    def analyze_midi_file(self, midi_path: str) -> dict:
        """Analyze a MIDI file to understand its characteristics."""
        try:
            import mido

            mid = mido.MidiFile(midi_path)

            analysis = {
                'tracks': len(mid.tracks),
                'ticks_per_beat': mid.ticks_per_beat,
                'length_seconds': 0,
                'note_count': 0,
                'note_range': {'min': 127, 'max': 0},
                'tempo_changes': 0,
                'instruments': set()
            }

            current_time = 0
            tempo = 500000

            for track in mid.tracks:
                for msg in track:
                    current_time += msg.time

                    if msg.type == 'set_tempo':
                        analysis['tempo_changes'] += 1
                        tempo = msg.tempo
                    elif msg.type == 'note_on' and msg.velocity > 0:
                        analysis['note_count'] += 1
                        analysis['note_range']['min'] = min(analysis['note_range']['min'], msg.note)
                        analysis['note_range']['max'] = max(analysis['note_range']['max'], msg.note)
                    elif msg.type == 'program_change':
                        analysis['instruments'].add(msg.program)

            # Convert final time to seconds
            seconds_per_tick = tempo / (1000000 * mid.ticks_per_beat)
            analysis['length_seconds'] = current_time * seconds_per_tick
            analysis['instruments'] = list(analysis['instruments'])

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing MIDI: {e}")
            return {}


def install_midi_dependencies():
    """Install required dependencies for MIDI transcription."""
    dependencies = [
        "mido",         # MIDI I/O
        "music21",      # Music analysis
        "pretty_midi",  # Alternative MIDI handling
    ]

    print("Installing dependencies for MIDI transcription...")
    print("Required packages:")
    for dep in dependencies:
        print(f"  - {dep}")

    print("\nTo install all dependencies, run:")
    print("pip install mido music21 pretty_midi")
    print("\nNote: music21 may require additional setup for audio features")


def main():
    """Demo function to test MIDI transcription.

    Deprecated: this script is now intended to be used as a library only.
    """
    print("This module is now library-only. Please use MIDIToJianpuTranscriber in your own scripts.")


if __name__ == "__main__":
    main()
