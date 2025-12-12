# Game Music Player

Automates playing musical instruments for the game "Where Winds Meet"

To download the .exe, navigate to the dist folder and download GameMusicPlayer.zip

## Features

- **GUI Interface** - User-friendly graphical interface with paste functionality
- **PDF Music Score Reader** - Upload PDF music scores and automatically convert to notes
- **MIDI to Jianpu Transcription** - Upload MIDI files and convert to game-playable notation with accurate rhythm
  - ✅ **NEW**: Duration markers (`:h`, `:e`, `:q`) for accurate rhythm preservation
  - ✅ **NEW**: Chord detection and melody extraction
  - ✅ **NEW**: Rest symbols (`0`) for proper silence
  - ✅ **NEW**: Velocity-aware note filtering
- **Jianpu Wait Commands** - Add sustain effects with wait/hold/延音 commands for Guqin-style playing
- **Command-line Interface** - Text-based menu system for advanced users
- Maps musical notes to keyboard keys for game instrument controls
- Supports High, Medium, and Low pitch ranges (1-7 notes each)
- Adjustable delay between notes for precise timing
- Real-time note validation and error handling
- Countdown timer to give you time to focus the game window

## Quick Start

**Option 1: GUI Only (Easiest)**
- Double-click `run_gui.bat` (Windows)
- Or run: `python gui_launcher.py`

**Option 2: Use the Main Launcher**
- Double-click `run_music_player.bat` (Windows)  
- Or run: `python launcher.py`

**Option 3: Run Directly**
- GUI: `python music_player_gui.py`
- CLI: `python game_music_player.py`

**Option 4: Test Setup First**
- Run: `python test_setup.py` to verify all dependencies

## Installation

1. Make sure you have Python installed
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Note Mapping

The script maps musical notes to your keyboard as follows:

**High Pitch (High1-High7):** Q W E R T Y U  
**Medium Pitch (Med1-Med7):** A S D F G H J  
**Low Pitch (Low1-Low7):** Z X C V B N M  

## Usage

### GUI Interface (Recommended)

Run the graphical interface:
```
python music_player_gui.py
```

The GUI provides:
- **Visual note mapping reference** - See the keyboard layout at a glance
- **PDF music score upload** - Convert PDF sheet music to game notes automatically
- **MIDI file transcription** - Upload MIDI files for automatic Jianpu conversion
- **Jianpu wait commands** - Add sustain effects with wait/hold/延音 for expressive playing
- **Large text area** - Paste long song strings easily
- **Real-time validation** - Check your notes before playing
- **Adjustable settings** - Change note delay and countdown timer
- **Play controls** - Play, stop, and clear buttons
- **Status log** - See what's happening during playback

### Command Line Interface

Run the command-line script:
```
python game_music_player.py
```

The script provides an interactive menu with the following options:

1. **Play a song** - Enter notes separated by spaces
2. **Show note mapping** - Display the keyboard layout
3. **Change note delay** - Adjust timing between notes
4. **Quit** - Exit the program

### Example Song Input

```
High1 High2 Med3 Low5 High7 Med1 Low3
```

This would play:
- High note 1 (Q key)
- High note 2 (W key)  
- Medium note 3 (D key)
- Low note 5 (B key)
- High note 7 (U key)
- Medium note 1 (A key)
- Low note 3 (C key)

## PDF Music Score Reading

The app can automatically convert PDF music scores to game notes! 

### Quick Start with PDF
1. **Launch GUI** and click **"📁 Upload PDF Score"** to load your score
2. **Wait for processing** - notes will appear in the song input area
3. **Play the extracted notes** using normal playback controls

### What Works Best
- PDFs with text-based note names (C, D, E, F, G, A, B)
- Simple melody lines rather than complex scores
- Clear, readable music notation
- Solfege notation (do, re, mi, fa, sol, la, ti)

### Installation for PDF Reading
```bash
# Full PDF reading (recommended)
pip install reportlab PyMuPDF Pillow pytesseract music21
```

For complete setup instructions, see [PDF_READER_GUIDE.md](PDF_READER_GUIDE.md)

## MIDI to Jianpu Transcription

Convert your favorite MIDI files directly to game-playable notation with **accurate rhythm preservation**! 

### Quick Start with MIDI
1. **Launch GUI** and click **"🎹 Upload MIDI"**
2. **Select MIDI file** - Works with both simple and complex music
3. **Wait for transcription** - Notes with duration markers appear automatically
4. **Play the result** - Enjoy accurate rhythm in-game!

### Enhanced Features (NEW! ✅)
- **Duration Markers**: Notes include timing (`:h` = half, `:e` = eighth, `:q` = quarter)
- **Chord Detection**: Multiple simultaneous notes → single melody note (highest pitch)
- **Rest Symbols**: Gaps represented as `0` for proper silence
- **Track Merging**: All MIDI tracks synchronized for perfect timing
- **Velocity Filtering**: Keeps musically important notes

### Example Output
**Before:**
```
Med1 Med3 Med5 wait Med6
```

**After (with rhythm):**
```
Med1:h Med5:e 0:q Med6:q Med7:e
```
- `:h` = Half note (1.0s @ 120 BPM)
- `:e` = Eighth note (0.25s)
- `0:q` = Quarter rest (silence)

### What Works Best
- Any MIDI file! Simple melodies to complex arrangements
- Standard MIDI format (.mid or .midi)
- Music in playable pitch ranges

### Automatic Features
- **Note Mapping**: MIDI notes → Jianpu (C4 = Med1, etc.)
- **Octave Detection**: Low/Med/High ranges based on pitch
- **Rhythm Preservation**: Actual note durations from MIDI
- **Chord Simplification**: Polyphonic → monophonic melody

📖 **For details, see [MIDI_FIX_COMPLETE.md](MIDI_FIX_COMPLETE.md)**
- **Wait Commands**: Longer notes get sustain effects automatically
- **Game Optimization**: Limited to reasonable length for performance

### Installation for MIDI Support
```bash
# Basic MIDI transcription
pip install mido

# Full featured (recommended)
pip install mido music21 pretty_midi
```

## Jianpu Wait Commands for Guqin

Add natural sustain effects perfect for traditional Chinese instruments!

### Wait Command Types
- **English**: `wait`, `hold`, `sustain`
- **Chinese**: `延音` (extend sound), `延` (extend)
- **Symbol**: `-` (brief sustain)

### Usage Examples
```
Original:  Med1 Med2 Med3 Med4
Enhanced:  Med1 wait Med2 延音 Med3 hold Med4 sustain

Nirvana with expression:
Med5 wait Med1 Med1 hold Med1 Med2 延音 Med1 Med4 sustain Med2 Med1 延音 Med3 Med2 Med1 wait Med2 Med4 延音
```

### Perfect for Guqin
- **Natural Resonance**: Random 0.5-2.0s sustain mimics string decay
- **Expressive Playing**: Add pauses for emotional depth  
- **Cultural Authenticity**: Traditional Chinese notation support
- **Configurable**: Adjust timing ranges for different playing styles

## Tips for Use

1. **Focus the game window** - Make sure your game window is active and focused before the countdown ends
2. **Adjust timing** - Different games may need different delays between notes (default is 0.1 seconds)
3. **Test first** - Try a short sequence first to ensure the game is receiving the inputs correctly
4. **Failsafe** - Move your mouse to the top-left corner to abort if needed (pydirectinput failsafe)

## Troubleshooting

### Note Delay Issues (FIXED)
If notes were playing too rapidly without delay:
- ✅ **Fixed**: Replaced incorrect `threading.Event().wait()` with proper `time.sleep()`
- ✅ **Fixed**: Improved delay setting mechanism with real-time updates
- ✅ **Added**: Test Delay button in GUI to verify timing
- ✅ **Added**: Better logging and validation

### Other Common Issues
- **Keys not registering:** Make sure the game window is focused and try increasing the note delay
- **Game not responding:** Some games may require running as administrator
- **Wrong notes playing:** Double-check your note mapping matches your game's instrument layout

## Safety Features

- Input validation prevents invalid notes from being sent
- Countdown timer gives you time to prepare
- Failsafe mouse movement to abort (move to top-left corner)
- Clear feedback on what notes are being played

Enjoy automating your musical performances!
