"""
Music Score Reader - Converts MusicXML scores to game music player format
Uses music21 to read musical notation from MusicXML (.mxl/.musicxml/.xml) files.
"""

import os
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MusicScoreReader:
    """Reads MusicXML scores and converts them to game music player format."""

    def __init__(self):
        # Support compressed and plain MusicXML
        self.supported_formats = ['.mxl', '.musicxml', '.xml']
        self.note_mapping = {
            # Standard music notation to game notation mapping
            'C': 1, 'D': 2, 'E': 3, 'F': 4, 'G': 5, 'A': 6, 'B': 7,
            'c': 1, 'd': 2, 'e': 3, 'f': 4, 'g': 5, 'a': 6, 'b': 7
        }

    def is_supported_file(self, filename: str) -> bool:
        """Check if the file format is supported."""
        _, ext = os.path.splitext(filename.lower())
        return ext in self.supported_formats

    def read_score(self, path: str) -> Optional[str]:
        """Read a MusicXML score (.mxl/.musicxml/.xml) and convert it to game format."""
        if not os.path.exists(path):
            logger.error(f"Score file not found: {path}")
            return None

        if not self.is_supported_file(path):
            logger.error(f"Unsupported score format (expected .mxl/.musicxml/.xml): {path}")
            return None

        try:
            return self._try_music21_approach(path)
        except Exception as e:
            logger.error(f"Error reading score: {e}")
            return None

    def read_pdf_score(self, pdf_path: str) -> Optional[str]:
        """Backward-compatible wrapper: still called read_pdf_score but now expects MusicXML.

        For compatibility with existing GUI code, this method accepts a path and
        forwards to read_score. Pass a .mxl/.musicxml/.xml file here.
        """
        return self.read_score(pdf_path)

    def _try_music21_approach(self, score_path: str) -> Optional[str]:
        """Use music21 to parse a MusicXML score and extract notes."""
        try:
            from music21 import converter, note

            logger.info("Attempting to read MusicXML with music21...")

            score = converter.parse(score_path)
            if score is None:
                return None

            notes: List[str] = []

            for element in score.flat.notes:
                if isinstance(element, note.Note):
                    game_note = self._convert_music21_note_to_game_format(element)
                    if game_note:
                        notes.append(game_note)
                elif isinstance(element, note.Chord):
                    highest_note = max(element.notes, key=lambda n: n.pitch.midi)
                    game_note = self._convert_music21_note_to_game_format(highest_note)
                    if game_note:
                        notes.append(game_note)

            if notes:
                logger.info(f"Successfully extracted {len(notes)} notes from MusicXML")
                return " ".join(notes)

        except ImportError:
            logger.info("music21 library not available")
        except Exception as e:
            logger.warning(f"music21 MusicXML approach failed: {e}")

        return None

    def _convert_music21_note_to_game_format(self, note_obj) -> Optional[str]:
        """Convert a music21 note object to game format."""
        try:
            note_name = note_obj.pitch.name
            octave = note_obj.pitch.octave

            if note_name not in self.note_mapping:
                return None

            note_number = self.note_mapping[note_name]

            # Map octaves to pitch ranges (this is approximate and can be adjusted)
            if octave >= 6:  # High octaves
                pitch_range = "High"
            elif octave >= 4:  # Medium octaves
                pitch_range = "Med"
            else:  # Low octaves
                pitch_range = "Low"

            return f"{pitch_range}{note_number}"

        except Exception:
            return None

    def _extract_notes_from_text(self, text: str) -> List[str]:
        """Extract note patterns from OCR text."""
        notes = []

        # Look for common text representations of notes
        # This is a simple pattern - could be improved with better music notation recognition
        note_patterns = [
            r'\b[CDEFGAB][b#]?\d?\b',  # Standard note names
            r'\bdo\b|\bre\b|\bmi\b|\bfa\b|\bsol?\b|\bla\b|\bti\b|\bsi\b',  # Solfege
        ]

        for pattern in note_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                game_note = self._convert_text_note_to_game_format(match)
                if game_note:
                    notes.append(game_note)

        return notes

    def _convert_text_note_to_game_format(self, text_note: str) -> Optional[str]:
        """Convert text note representation to game format."""
        text_note = text_note.lower().strip()

        # Map solfege to note numbers
        solfege_map = {
            'do': 1, 're': 2, 'mi': 3, 'fa': 4, 'sol': 5, 'so': 5, 'la': 6, 'ti': 7, 'si': 7
        }

        if text_note in solfege_map:
            return f"Med{solfege_map[text_note]}"

        # Handle standard note names
        note_char = text_note[0].upper()
        if note_char in self.note_mapping:
            return f"Med{self.note_mapping[note_char]}"

        return None


def install_dependencies():
    """Install required dependencies for music score reading."""
    dependencies = [
        "music21",  # For music analysis
    ]

    print("Installing dependencies for music score reading...")
    print("Required packages:")
    for dep in dependencies:
        print(f"  - {dep}")

    print("\nTo install all dependencies, run:")
    print("pip install music21")


def main():
    """Library-only entry point (no demo functionality)."""
    print("MusicScoreReader is a library; import and use MusicScoreReader.read_pdf_score().")


if __name__ == "__main__":
    main()
