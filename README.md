# WWM Music Player

Music Player for Where Winds Meet (WWM) Focused on Guqin. Download the exe file in dist folder, run with administrator privileges.

## Features

### MIDI Conversion
- **Polyphonic and Monophonic Modes**: Convert MIDI files to game-friendly note sequences, supporting both chords (simultaneous notes) and single-note (sequential) playback.
- **Multi-Track MIDI Support**:
  - **Melody Only**: Automatically detects and uses the main melody track.
  - **Track Picker**: Lets you manually select which tracks to include from complex MIDI files.
  - **Exclude Drums**: Filters out percussion tracks (MIDI channel 10).
  - **Max Chord Size**: Limit the number of notes played simultaneously (0 = unlimited).
- **Tempo Adjustment**: Change playback speed (Guqin, Fast, or Custom tempo).
- **MIDI Filtering**: Choose between full, clean, or minimal note filtering for best results.

### Game Music Playback
- **Automatic Key Mapping**: Maps notes to keyboard keys, including support for semitones (sharps/flats) using Shift/Ctrl modifiers.
- **Polyphonic Playback**: Simultaneously presses multiple keys for chords.
- **Rest and Wait Handling**: Supports rests and sustained notes for expressive playback.
- **Multiple Modes**:
  - **Guqin Style**: Slow, expressive, with natural waits.
  - **Fast Mode**: Minimal delays, no waits.
  - **Custom Mode**: User-defined tempo multiplier.

### GUI Features
- **Drag-and-Drop or Button Upload**: Supports PDF, MusicXML, MIDI, and image files.
- **Track Picker Dialog**: Visual interface to select tracks from multi-track MIDI files.
- **Settings Panel**: Adjust note delay, tempo, MIDI filter, polyphonic mode, max chord size, and more.

### File Support
- **MIDI**: Full support for multi-track, polyphonic, and monophonic files.
- **PDF/MusicXML/Image**: Converts sheet music and images to playable note sequences (best with simple melodies).

### Installer/Packaging
- **Windows Installer**: Build scripts and icons for creating a standalone .exe installer.

## Usage
1. **Upload a music file** (MIDI, PDF, MusicXML, or image).
2. **Adjust settings** as needed (polyphonic, melody only, exclude drums, etc.).
3. **(Optional) Use the Track Picker** to select specific tracks from a MIDI file.
4. **Play the music** in your game using the automated keypress system.

## Requirements
- Python 3.8+
- See `requirements.txt` for dependencies (e.g., mido, pydirectinput, tkinter, etc.)

## Tips
- For best results with complex MIDI files, use the Track Picker to select only the melody or main instrument track.
- Use "Melody Only" mode for single-voice output, or enable polyphonic mode for richer chords.
- Exclude drums to avoid unwanted noise from percussion tracks.

## License
See LICENSE file.
