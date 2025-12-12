"""
Huangpu Converter
-----------------
Convert classic staff notation (MusicXML or PDF) into Huangpu (jianpu-like) tokens.

Inputs:
- MusicXML (.musicxml/.xml): parsed via music21
- PDF: optional conversion to MusicXML via MuseScore or Audiveris CLI

Outputs:
- Huangpu string: degree tokens (1..7 with b/# accidentals), octave marks (' ,), duration markers (:w/:h/:q/:e/:s), rests as 0:dur

Example:
(1 3 5):h 0:q 5':e

Usage:
    python huangpu_converter.py path/to/score.musicxml
    python huangpu_converter.py path/to/score.pdf    # requires MuseScore or Audiveris

"""
from __future__ import annotations
import os
import shutil
import subprocess
import tempfile
from typing import List, Tuple, Optional

try:
    from music21 import converter, note, chord, key as m21key, stream
except Exception:
    converter = None  # lazy import guard

# Duration mapping (quarterLength -> symbol)
DUR_MAP = {
    4.0: "w",
    2.0: "h",
    1.0: "q",
    0.5: "e",
    0.25: "s",
}
DUR_VALUES = sorted(DUR_MAP.keys(), reverse=True)

# Major scale semitone offsets (relative to tonic) for degrees 1..7
MAJOR_SCALE_OFFSETS = [0, 2, 4, 5, 7, 9, 11]


def _nearest_duration_symbol(q_len: float) -> str:
    """Choose nearest standard duration symbol."""
    best = min(DUR_VALUES, key=lambda x: abs(x - q_len))
    return DUR_MAP[best]


def _pitch_to_huangpu_degree(pitch_midi: int, tonic_midi: int) -> Tuple[str, int]:
    """
    Map a MIDI pitch to (degree_string, octave_offset) in a major key.
    - degree_string: '1'..'7' with optional 'b' or '#' accidental when chromatic
    - octave_offset: 0=same, >0=octaves above tonic, <0=below
    """
    semitone_diff = (pitch_midi - tonic_midi)
    octave_offset = semitone_diff // 12
    semitone_in_octave = semitone_diff % 12

    if semitone_in_octave in MAJOR_SCALE_OFFSETS:
        degree_index = MAJOR_SCALE_OFFSETS.index(semitone_in_octave) + 1
        return str(degree_index), octave_offset

    # nearest scale degree with accidental
    best_idx = min(range(len(MAJOR_SCALE_OFFSETS)),
                   key=lambda i: abs(MAJOR_SCALE_OFFSETS[i] - semitone_in_octave))
    base_offset = MAJOR_SCALE_OFFSETS[best_idx]
    diff = semitone_in_octave - base_offset
    degree_index = best_idx + 1
    if diff == 1 or diff == -11:
        degree = "#" + str(degree_index)
    elif diff == -1 or diff == 11:
        degree = "b" + str(degree_index)
    else:
        degree = f"{degree_index}?"  # uncommon alteration
    return degree, octave_offset


def _format_octave_marker(octave_offset: int) -> str:
    """Use ' for up-oktave and , for down-oktave markers."""
    if octave_offset > 0:
        return "'" * octave_offset
    if octave_offset < 0:
        return "," * (-octave_offset)
    return ""


def musicxml_to_huangpu(musicxml_path: str) -> str:
    """Convert a MusicXML file to Huangpu (jianpu-like) token string.

    Handles chords, notes, and rests; groups all simultaneous notes into
    chord tokens so that full polyphony is preserved in the Huangpu
    representation instead of collapsing to a single voice.
    """
    if converter is None:
        raise RuntimeError("music21 is required: pip install music21")

    score: stream.Score = converter.parse(musicxml_path)
    try:
        k: Optional[m21key.Key] = score.analyze("key")
    except Exception:
        k = None
    if k is None:
        k = m21key.Key("C")

    tonic_pitch = k.tonic
    tonic_midi = tonic_pitch.midi if tonic_pitch is not None else 60  # C4 fallback

    tokens: List[str] = []

    # Collect notes/rests/chords and group by offset
    flat = score.flat.notesAndRests
    events: dict[float, List[object]] = {}
    for el in flat:
        if isinstance(el, (note.Note, note.Rest, chord.Chord)):
            off = float(el.offset)
            events.setdefault(off, []).append(el)

    for off in sorted(events.keys()):
        elems = events[off]

        # Partition by type
        chord_elems = [e for e in elems if isinstance(e, chord.Chord)]
        note_elems = [e for e in elems if isinstance(e, note.Note)]
        rest_elems = [e for e in elems if isinstance(e, note.Rest)]

        # 1) Any explicit Chord objects: emit each as a Huangpu chord token
        for ch in chord_elems:
            dur_sym = _nearest_duration_symbol(float(ch.quarterLength))
            degree_parts = []
            for p in ch.pitches:
                deg, octo = _pitch_to_huangpu_degree(p.midi, tonic_midi)
                degree_parts.append(f"{deg}{_format_octave_marker(octo)}")
            if degree_parts:
                tokens.append(f"({' '.join(degree_parts)}):{dur_sym}")

        # 2) Notes at the same offset that are not part of a Chord:
        #    if more than one, treat them as a chord-like group
        if note_elems:
            if len(note_elems) > 1:
                # Use duration of first note in the group as representative
                dur_sym = _nearest_duration_symbol(float(note_elems[0].quarterLength))
                parts = []
                for n in note_elems:
                    deg, octo = _pitch_to_huangpu_degree(n.pitch.midi, tonic_midi)
                    parts.append(f"{deg}{_format_octave_marker(octo)}")
                tokens.append(f"({' '.join(parts)}):{dur_sym}")
            else:
                n = note_elems[0]
                deg, octo = _pitch_to_huangpu_degree(n.pitch.midi, tonic_midi)
                dur_sym = _nearest_duration_symbol(float(n.quarterLength))
                tokens.append(f"{deg}{_format_octave_marker(octo)}:{dur_sym}")

        # 3) Rests at this offset: emit the first as a Huangpu rest token
        if rest_elems:
            r = rest_elems[0]
            dur_sym = _nearest_duration_symbol(float(r.quarterLength))
            tokens.append(f"0:{dur_sym}")

    return " ".join(tokens)


def find_musescore_executable() -> Optional[str]:
    candidates = [
        "mscore", "musescore", "MuseScore", "MuseScore3", "MuseScore4", "MuseScore.exe",
        "MuseScore3.exe", "MuseScore4.exe"
    ]
    for c in candidates:
        path = shutil.which(c)
        if path:
            return path
    return None


def convert_pdf_to_musicxml(pdf_path: str, out_musicxml: Optional[str] = None) -> str:
    """
    Convert a PDF with printed staff notation into MusicXML using external tools.
    Prefers MuseScore CLI; falls back to Audiveris if available.
    """
    if out_musicxml is None:
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        out_musicxml = os.path.join(os.path.dirname(pdf_path), base + ".musicxml")

    ms_exec = find_musescore_executable()
    if ms_exec:
        # MuseScore CLI example: mscore -o output.musicxml input.pdf
        cmd = [ms_exec, "-o", out_musicxml, pdf_path]
        subprocess.check_call(cmd)
        if os.path.exists(out_musicxml):
            return out_musicxml
        raise RuntimeError("MuseScore did not produce output; check CLI options for your version.")

    audiveris = shutil.which("audiveris") or shutil.which("audiveris.bat")
    if audiveris:
        tmpdir = tempfile.mkdtemp(prefix="aud_")
        cmd = [audiveris, "-export", "-output", tmpdir, pdf_path]
        subprocess.check_call(cmd)
        for root, _, files in os.walk(tmpdir):
            for f in files:
                if f.lower().endswith(".musicxml") or f.lower().endswith(".xml"):
                    cand = os.path.join(root, f)
                    shutil.move(cand, out_musicxml)
                    return out_musicxml
        raise RuntimeError("Audiveris finished but no MusicXML found in output.")

    raise RuntimeError(
        "No MuseScore or Audiveris found on PATH. Install MuseScore (recommended) or Audiveris "
        "and ensure their CLI is available. MuseScore CLI: mscore -o out.musicxml in.pdf"
    )


def convert_input_to_huangpu(input_path: str) -> str:
    """Entry point: PDF or MusicXML to Huangpu string."""
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".pdf":
        musicxml = convert_pdf_to_musicxml(input_path)
    else:
        musicxml = input_path
    return musicxml_to_huangpu(musicxml)


def huangpu_to_game_tokens(hp: str, pseudo_polyphonic: bool = False) -> str:
    """Convert Huangpu tokens (e.g., 1:q, 5':e, (1 3 5):h, 0:q) to game tokens using High/Med/Low mapping.

    Rules:
    - Octave markers: none -> Med, one quote ' -> High, one comma , -> Low
      Additional quotes/commas are clamped to High/Low respectively.
    - Accidentals (#/b) are ignored for mapping to key names; we keep the base degree 1..7.
    - Durations (:w/:h/:q/:e/:s) are preserved.
    - Rests (0:dur) are preserved.

    If pseudo_polyphonic is False (default):
        - Chords ("(...)") are collapsed to a single highest note (prefers ' over none over ,;
          ties resolved by larger degree), matching the original behavior.

    If pseudo_polyphonic is True:
        - Chords are expanded to a short arpeggiated sequence of notes, ordered from lowest to
          highest by range and degree, all sharing the original duration code. This allows
          GameMusicPlayer to render richer chord textures while still playing notes sequentially.
    """
    import re

    def parse_item(token: str):
        """Parse a Huangpu token into (is_chord, payload, duration_code)."""
        dur = None
        core = token
        if ':' in token:
            core, dur = token.split(':', 1)
        core = core.strip()
        if core.startswith('(') and core.endswith(')'):
            inner = core[1:-1].strip()
            parts = inner.split() if inner else []
            return True, parts, dur
        return False, core, dur

    def degree_to_game(deg_token: str) -> tuple[Optional[str], int, int]:
        """Map a Huangpu degree token to (game_note_name, range_priority, degree_value).

        game_note_name is like 'High3', 'Med5', 'Low1'.
        range_priority: High=3, Med=2, Low=1, used for ordering.
        degree_value: 1..7 numeric degree for tie-breaking/sorting.
        """
        # detect octave markers counts
        octave_up = deg_token.count("'")
        octave_down = deg_token.count(",")

        # strip markers and accidentals for mapping
        base = deg_token.replace("'", "").replace(",", "")
        base = base.lstrip('#b')

        # pick range based on markers
        if octave_up > 0:
            prefix = 'High'
            pr = 3
        elif octave_down > 0:
            prefix = 'Low'
            pr = 1
        else:
            prefix = 'Med'
            pr = 2

        # degree number fallback
        m = re.match(r"(\d)", base)
        if not m:
            return None, 0, 0
        num = int(m.group(1))
        return f"{prefix}{num}", pr, num

    out_tokens: List[str] = []

    # Tokenize while preserving parenthesized chord groups
    # Match either: (1) parenthesized groups with content, or (2) non-whitespace sequences
    tokens = re.findall(r'\([^)]+\)(?::\w+)?|\S+', hp)

    for raw in tokens:
        is_chord, payload, dur = parse_item(raw)

        if is_chord:
            if not payload:
                continue

            # Build list of (name, range_priority, degree_value) for each chord tone
            mapped = []
            for part in payload:
                name, pr, deg_val = degree_to_game(part)
                if name is None:
                    continue
                mapped.append((name, pr, deg_val))

            if not mapped:
                continue

            if not pseudo_polyphonic:
                # Original behavior: choose highest voice only
                best_name, _, _ = max(mapped, key=lambda x: (x[1], x[2]))
                out_tokens.append(f"{best_name}:{dur}" if dur else best_name)
            else:
                # Pseudo-polyphonic: arpeggiate chord tones from low to high
                # Sort by (range_priority, degree_value)
                mapped.sort(key=lambda x: (x[1], x[2]))
                for name, _, _ in mapped:
                    out_tokens.append(f"{name}:{dur}" if dur else name)

        else:
            note = payload
            if note == '0' or note.startswith('0'):
                out_tokens.append(f"0:{dur}" if dur else "0")
                continue

            name, _, _ = degree_to_game(note)
            if name is None:
                # skip unknown
                continue
            out_tokens.append(f"{name}:{dur}" if dur else name)

    return ' '.join(out_tokens)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python huangpu_converter.py <score.musicxml|score.pdf>")
        sys.exit(1)
    src = sys.argv[1]
    try:
        out = convert_input_to_huangpu(src)
        print(out)
    except Exception as e:
        print("Error:", e)
        sys.exit(2)
