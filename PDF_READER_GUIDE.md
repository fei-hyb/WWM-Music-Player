# Music Score PDF Reader - Installation Guide

This document explains how to install and use the PDF music score reading feature.

## Overview

The PDF music score reader can convert PDF music scores into the game music player format. It uses multiple approaches:

1. **Music21** - For analyzing embedded music data
2. **OCR (Optical Character Recognition)** - For text-based music notation

## Installation

To install all dependencies for complete functionality:
```bash
pip install PyMuPDF Pillow pytesseract music21
```

### Additional Requirements

**For OCR functionality**, you also need to install Tesseract:
- **Windows**: Download from https://github.com/tesseract-ocr/tesseract
- **Linux**: `sudo apt-get install tesseract-ocr`
- **Mac**: `brew install tesseract`

## How It Works

### Supported Input Types

1. **Text-based PDF scores** - PDFs containing note names (C, D, E, F, G, A, B) or solfege (do, re, mi)
2. **Simple music notation** - Clear, text-readable music symbols

### What Gets Converted

The system looks for:
- Note names: C, D, E, F, G, A, B
- Solfege syllables: do, re, mi, fa, sol, la, ti
- These are converted to game format: High1-High7, Med1-Med7, Low1-Low7

### Limitations

- **Complex scores**: Multi-voice, complex rhythms not supported
- **Image-only PDFs**: Scanned sheet music without text may not work
- **Advanced notation**: Sharps, flats, and complex symbols have limited support
- **Professional scores**: Commercial sheet music PDFs may be too complex

## Usage

### In the GUI

1. **Launch the GUI**: `python gui_launcher.py`
2. **Click "📁 Upload PDF Score"** - Upload your own PDF music score
3. **Wait for processing** - The app will extract notes and populate the song input
4. **Play the result** - Use normal playback controls

### Programmatically

```python
from music_score_reader import MusicScoreReader

reader = MusicScoreReader()

# Read a PDF score
notes = reader.read_pdf_score("my_score.pdf")
if notes:
    print(f"Extracted notes: {notes}")
    # Use with game music player
    from game_music_player import GameMusicPlayer
    player = GameMusicPlayer()
    player.play_song(notes)
else:
    print("Could not extract notes from PDF")
```

## Best Results

To get the best results from PDF music scores:

### PDF Format
- **Text-based PDFs** work better than scanned images
- **Simple notation** is more reliable than complex scores
- **Clear, large text** improves OCR accuracy

### Music Content
- **Single melody lines** work best
- **Simple note sequences** (C D E F G A B)
- **Solfege notation** (do re mi fa sol la ti)
- **Avoid complex rhythms** and multi-part harmonies

### File Quality
- **High resolution** for scanned PDFs
- **Clear, non-handwritten** text
- **Standard music fonts** if possible

## Troubleshooting

### "Could not extract music from PDF"
1. **Check file format** - Ensure it's a PDF
2. **Check dependencies** - Install missing libraries
3. **Verify content** - Ensure PDF contains readable note names

### Missing Dependencies
```bash
# Install missing packages one by one
pip install PyMuPDF       # For PDF processing
pip install Pillow        # For image processing
pip install pytesseract   # For OCR
pip install music21       # For music analysis
```

### OCR Not Working
1. **Install Tesseract** - System-level OCR engine required
2. **Check PATH** - Ensure Tesseract is in system PATH
3. **Test with simple PDFs** - Start with clear, simple text

### Poor Recognition Results
1. **Use simpler scores** - Avoid complex notation
2. **Check PDF quality** - Ensure text is readable
3. **Try different PDFs** - Test with various file types and content
4. **Manual input** - As fallback, type notes manually

## Examples

### Supported Text Patterns
- `C D E F G A B` → `Med1 Med2 Med3 Med4 Med5 Med6 Med7`
- `do re mi fa sol` → `Med1 Med2 Med3 Med4 Med5`
- Mixed case works: `c d e` or `Do Re Mi`

## Future Improvements

Potential enhancements for the PDF reader:
- Support for sharps and flats (C#, Bb)
- Rhythm and timing information
- Multi-voice score separation
- Advanced OMR using machine learning
- Support for MusicXML import/export
- Integration with online music libraries

## Getting Help

If you encounter issues:
1. **Check logs**: Look at the status log in the GUI for error details
2. **Try different PDFs**: Test with various file types and content
3. **Manual fallback**: You can always type notes manually in the song input area

The PDF reading feature is experimental and works best with simple, text-based music notation. For complex scores, manual input may be more reliable.
