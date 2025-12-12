"""
GUI Music Player for Game Instruments
Provides a graphical interface for pasting and playing music note strings
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import os
from game_music_player import GameMusicPlayer
from music_score_reader import MusicScoreReader
from midi_to_jianpu import MIDIToJianpuTranscriber
from huangpu_converter import convert_input_to_huangpu


class MusicPlayerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Music Player - GUI")
        # Slightly larger default size so all sections are visible without manual resize
        self.root.geometry("1000x900")  # Increased size for better default layout
        self.root.resizable(True, True)

        # Initialize the music player, score reader, and MIDI transcriber
        self.player = GameMusicPlayer(note_delay=0.1)
        self.score_reader = MusicScoreReader()
        self.midi_transcriber = MIDIToJianpuTranscriber()
        self.is_playing = False
        self.current_midi_file = None  # Track currently loaded MIDI for re-transcription

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface components."""

        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights for responsive design
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        # Let lower sections expand vertically so they are fully visible
        main_frame.rowconfigure(4, weight=2)  # Song input
        main_frame.rowconfigure(6, weight=1)  # Status & log

        # Title
        title_label = ttk.Label(main_frame, text="Game Music Player",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Note mapping display
        self.create_note_mapping_section(main_frame, row=1)

        # Settings section
        self.create_settings_section(main_frame, row=2)

        # PDF upload section
        self.create_pdf_upload_section(main_frame, row=3)

        # Song input section
        self.create_song_input_section(main_frame, row=4)

        # Control buttons
        self.create_control_buttons(main_frame, row=5)

        # Status and log section
        self.create_status_section(main_frame, row=6)

    def create_note_mapping_section(self, parent, row):
        """Create the note mapping reference section."""
        mapping_frame = ttk.LabelFrame(parent, text="Note Mapping Reference", padding="10")
        mapping_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        mapping_text = (
            "High Pitch (High1-High7):  Q  W  E  R  T  Y  U\n"
            "                          1  2  3  4  5  6  7\n\n"
            "Medium Pitch (Med1-Med7):  A  S  D  F  G  H  J\n"
            "                          1  2  3  4  5  6  7\n\n"
            "Low Pitch (Low1-Low7):     Z  X  C  V  B  N  M\n"
            "                          1  2  3  4  5  6  7\n\n"
            "Semitones: #1, b3, #4, #5, b7 between natural degrees.\n"
            "Hold Shift for higher semitone (#), Ctrl for lower semitone (b).\n"
            "Example: High1 High#1 High2 Medb3 Med3 Med#4 Low5 Low#5 Low6 Lowb7 Low7"
        )

        mapping_label = ttk.Label(
            mapping_frame,
            text=mapping_text,
            font=("Courier", 10),
            justify=tk.LEFT,
        )
        mapping_label.grid(row=0, column=0, sticky=tk.W)

    def create_settings_section(self, parent, row):
        """Create the settings section."""
        settings_frame = ttk.LabelFrame(parent, text="Settings", padding="10")
        settings_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Row 0: Note delay and countdown
        ttk.Label(settings_frame, text="Note Delay (seconds):").grid(row=0, column=0, sticky=tk.W)
        self.delay_var = tk.StringVar(value=str(self.player.note_delay))
        self.delay_var.trace('w', lambda *args: self.update_delay())  # Update when value changes
        delay_spinbox = ttk.Spinbox(settings_frame, from_=0.01, to=2.0, increment=0.01,
                                   width=10, textvariable=self.delay_var)
        delay_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(settings_frame, text="Countdown (seconds):").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.countdown_var = tk.StringVar(value="3")
        self.countdown_var.trace('w', lambda *args: self.validate_countdown())  # Validate when value changes
        countdown_spinbox = ttk.Spinbox(settings_frame, from_=1, to=10, increment=1, width=10,
                                       textvariable=self.countdown_var)
        countdown_spinbox.grid(row=0, column=3, sticky=tk.W, padx=(10, 0))

        # Test delay button
        test_delay_btn = ttk.Button(settings_frame, text="Test Delay",
                                   command=self.test_delay, width=12)
        test_delay_btn.grid(row=0, column=4, padx=(20, 0))

        # Row 1: Playing mode and tempo
        ttk.Label(settings_frame, text="Playing Mode:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.mode_var = tk.StringVar(value="guqin")
        mode_combo = ttk.Combobox(settings_frame, textvariable=self.mode_var, width=12,
                                  values=["guqin", "fast", "custom"], state="readonly")
        mode_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        mode_combo.bind("<<ComboboxSelected>>", lambda e: self.update_mode())

        ttk.Label(settings_frame, text="Tempo (1.0=normal):").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=(10, 0))
        self.tempo_var = tk.StringVar(value="1.0")
        self.tempo_var.trace('w', lambda *args: self.update_tempo())
        tempo_spinbox = ttk.Spinbox(settings_frame, from_=0.25, to=4.0, increment=0.25,
                                   width=10, textvariable=self.tempo_var)
        tempo_spinbox.grid(row=1, column=3, sticky=tk.W, padx=(10, 0), pady=(10, 0))

        # Mode info label
        self.mode_info_var = tk.StringVar(value="Guqin mode: slow, expressive")
        mode_info_label = ttk.Label(settings_frame, textvariable=self.mode_info_var, foreground="gray")
        mode_info_label.grid(row=1, column=4, sticky=tk.W, padx=(20, 0), pady=(10, 0))

        # Row 2: MIDI Filtering Mode
        ttk.Label(settings_frame, text="MIDI Filter:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.filter_var = tk.StringVar(value="full")
        filter_combo = ttk.Combobox(settings_frame, textvariable=self.filter_var, width=12,
                                    values=["full", "clean", "minimal"], state="readonly")
        filter_combo.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.update_filter_mode())

        # Filter info label
        self.filter_info_var = tk.StringVar(value="Full: all notes, no filtering")
        filter_info_label = ttk.Label(settings_frame, textvariable=self.filter_info_var, foreground="gray")
        filter_info_label.grid(row=2, column=2, columnspan=2, sticky=tk.W, padx=(20, 0), pady=(10, 0))

        # Polyphonic mode checkbox
        self.polyphonic_var = tk.BooleanVar(value=True)
        polyphonic_check = ttk.Checkbutton(settings_frame, text="Polyphonic (chords)",
                                           variable=self.polyphonic_var,
                                           command=self.update_polyphonic_mode)
        polyphonic_check.grid(row=2, column=4, sticky=tk.W, padx=(10, 0), pady=(10, 0))

        # Row 3: Multi-track MIDI options
        ttk.Label(settings_frame, text="Multi-track:").grid(row=3, column=0, sticky=tk.W, pady=(10, 0))

        # Melody only checkbox
        self.melody_only_var = tk.BooleanVar(value=False)
        melody_check = ttk.Checkbutton(settings_frame, text="Melody only",
                                       variable=self.melody_only_var,
                                       command=self.update_melody_mode)
        melody_check.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))

        # Exclude drums checkbox
        self.exclude_drums_var = tk.BooleanVar(value=True)
        drums_check = ttk.Checkbutton(settings_frame, text="Exclude drums",
                                      variable=self.exclude_drums_var,
                                      command=self.update_drums_setting)
        drums_check.grid(row=3, column=2, sticky=tk.W, padx=(10, 0), pady=(10, 0))

        # Max chord size
        ttk.Label(settings_frame, text="Max chord:").grid(row=3, column=3, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        self.max_chord_var = tk.StringVar(value="3")
        max_chord_spinbox = ttk.Spinbox(settings_frame, from_=0, to=10, increment=1,
                                        width=5, textvariable=self.max_chord_var)
        max_chord_spinbox.grid(row=3, column=4, sticky=tk.W, padx=(5, 0), pady=(10, 0))
        self.max_chord_var.trace('w', lambda *args: self.update_max_chord())

        # Help button
        help_button = ttk.Button(settings_frame, text="?", command=self.show_help, width=3)
        help_button.grid(row=0, column=5, padx=(10, 0))

    def update_melody_mode(self):
        """Toggle melody-only mode for MIDI transcription."""
        enabled = self.melody_only_var.get()
        self.midi_transcriber.melody_track_only = enabled
        self.log(f"Melody-only mode: {'enabled' if enabled else 'disabled'}")
        if self.current_midi_file:
            self._retranscribe_midi()

    def update_drums_setting(self):
        """Toggle drum exclusion for MIDI transcription."""
        enabled = self.exclude_drums_var.get()
        self.midi_transcriber.exclude_drums = enabled
        self.log(f"Exclude drums: {'enabled' if enabled else 'disabled'}")
        if self.current_midi_file:
            self._retranscribe_midi()

    def update_max_chord(self):
        """Update max chord size setting."""
        try:
            val = int(self.max_chord_var.get())
            if val < 0:
                val = 0
            self.midi_transcriber.max_chord_size = val
            # Don't log on every keystroke, only retranscribe if file loaded
        except ValueError:
            pass

    def update_polyphonic_mode(self):
        """Toggle polyphonic mode for MIDI transcription."""
        enabled = self.polyphonic_var.get()
        self.midi_transcriber.polyphonic_mode = enabled
        mode_str = "enabled (chords)" if enabled else "disabled (sequential)"
        self.log(f"Polyphonic mode: {mode_str}")

        # Regenerate notes if a MIDI file is loaded
        if self.current_midi_file:
            self.log(f"Re-transcribing MIDI with polyphonic={enabled}...")
            self._retranscribe_midi()

    def update_filter_mode(self):
        """Update the MIDI filtering mode and regenerate notes if MIDI is loaded."""
        mode = self.filter_var.get()
        if mode == "full":
            self.midi_transcriber.set_transcription_options(
                min_duration=0.001,
                remove_duplicates=False
            )
            self.filter_info_var.set("Full: all notes, no filtering")
        elif mode == "clean":
            self.midi_transcriber.set_transcription_options(
                min_duration=0.1,
                remove_duplicates=True,
                duplicate_threshold=0.1
            )
            self.filter_info_var.set("Clean: removes short notes (<100ms)")
        elif mode == "minimal":
            self.midi_transcriber.set_transcription_options(
                min_duration=0.2,
                remove_duplicates=True,
                duplicate_threshold=0.15
            )
            self.filter_info_var.set("Minimal: melody only, heavy filtering")
        self.log(f"MIDI filter mode: {mode}")

        # Regenerate notes if a MIDI file is currently loaded
        if self.current_midi_file:
            self.log(f"Re-transcribing MIDI with {mode} filter...")
            self._retranscribe_midi()

    def _retranscribe_midi(self):
        """Re-transcribe the currently loaded MIDI file with new filter settings."""
        if not self.current_midi_file:
            return

        def worker():
            try:
                jianpu_notes = self.midi_transcriber.transcribe_midi_file(self.current_midi_file)
                if jianpu_notes:
                    def update_ui():
                        self.song_text.delete(1.0, tk.END)
                        self.song_text.insert(1.0, jianpu_notes)
                        # Use proper parsing to count tokens (handles chords correctly)
                        tokens = self.player.parse_notes(jianpu_notes)
                        note_count = len(tokens)
                        poly_str = "polyphonic" if self.polyphonic_var.get() else "sequential"
                        self.upload_status_var.set(f"✅ Re-transcribed: {note_count} tokens ({self.filter_var.get()}, {poly_str})")
                        self.log(f"Re-transcribed: {note_count} tokens")
                    self.root.after(0, update_ui)
                else:
                    self.log("Re-transcription failed")
            except Exception as e:
                self.log(f"Error re-transcribing: {e}")

        import threading
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def show_help(self):
        """Display a help message explaining the settings."""
        help_text = (
            "Settings Help:\n\n"
            "Note Delay: Time between notes during playback.\n\n"
            "Countdown: Seconds before playback starts (to focus game window).\n\n"
            "Playing Mode:\n"
            "  • Guqin: Slow, expressive, with wait commands\n"
            "  • Fast: 4x speed, no waits\n"
            "  • Custom: User-defined tempo multiplier\n\n"
            "Tempo: Speed multiplier (1.0 = normal, 2.0 = 2x faster)\n\n"
            "MIDI Filter:\n"
            "  • Full: All notes, no filtering (may sound busy)\n"
            "  • Clean: Removes short notes <100ms (recommended)\n"
            "  • Minimal: Melody only, removes ornaments/fast runs\n\n"
            "Polyphonic (chords):\n"
            "  • Enabled: Simultaneous notes become chords [note1 note2]\n"
            "  • Disabled: Notes played sequentially\n\n"
            "Multi-track Options (for complex MIDIs):\n"
            "  • Melody only: Auto-detect and use melody track\n"
            "  • Exclude drums: Filters out percussion (channel 10)\n"
            "  • Max chord: Limits notes per chord (0 = unlimited)\n"
            "  • Pick Tracks: Manually select which tracks to use"
        )
        messagebox.showinfo("Settings Help", help_text)

    def create_pdf_upload_section(self, parent, row):
        """Create the music file upload section (PDF, images, MIDI)."""
        upload_frame = ttk.LabelFrame(parent, text="Music File Upload & Transcription", padding="10")
        upload_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        upload_frame.columnconfigure(1, weight=1)

        # Instructions
        instruction_label = ttk.Label(
            upload_frame,
            text=(
                "Upload a PDF score, image melody, MusicXML, or MIDI file for automatic transcription.\n"
                "Best results with PDFs and MusicXML that contain simple numeric or solfege melodies, e.g.\n"
                "  1 2 3 4 5 6 7  or  do re mi fa sol la ti do"
            ),
            justify=tk.LEFT,
            wraplength=520,
        )
        instruction_label.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        # Upload buttons row
        upload_btn = ttk.Button(upload_frame, text="📁 Upload Music File",
                               command=self.upload_music_file, width=18)
        upload_btn.grid(row=1, column=0, sticky=tk.W)

        # MIDI specific upload button
        midi_btn = ttk.Button(upload_frame, text="🎹 Upload MIDI",
                             command=self.upload_midi_file, width=18)
        midi_btn.grid(row=1, column=1, sticky=tk.W, padx=(5, 0))

        # Track picker button (for multi-track MIDIs)
        track_btn = ttk.Button(upload_frame, text="🎼 Pick Tracks",
                              command=self.show_track_picker, width=12)
        track_btn.grid(row=1, column=2, sticky=tk.W, padx=(5, 0))

        # Add Huangpu conversion button
        huangpu_btn = ttk.Button(upload_frame, text="📄 MusicXML→Huangpu",
                                 command=self.convert_musicxml_pdf_to_huangpu, width=18)
        huangpu_btn.grid(row=1, column=3, sticky=tk.W, padx=(5, 0))

        # File path display
        self.file_path_var = tk.StringVar(value="No file selected")
        path_label = ttk.Label(upload_frame, textvariable=self.file_path_var,
                              foreground="gray")
        path_label.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))

        # Status label for file processing
        self.upload_status_var = tk.StringVar(value="")
        upload_status_label = ttk.Label(upload_frame, textvariable=self.upload_status_var,
                                       foreground="blue")
        upload_status_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

    def create_song_input_section(self, parent, row):
        """Create the song input section."""
        input_frame = ttk.LabelFrame(parent, text="Song Input", padding="10")
        input_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(1, weight=1)

        # Instructions
        instruction_text = "Paste your song notes below (separated by spaces):\nExample: High1 High2 Med3 wait Low5\nUse 'wait', 'hold', 'sustain', or '延音' to prolong notes (perfect for Guqin)"
        ttk.Label(input_frame, text=instruction_text).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        # Song text area
        self.song_text = scrolledtext.ScrolledText(input_frame, height=8, width=50, wrap=tk.WORD)
        self.song_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def create_control_buttons(self, parent, row):
        """Create the control buttons section."""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=row, column=0, columnspan=2, pady=(0, 10))

        # Play button
        self.play_button = ttk.Button(control_frame, text="Play Song",
                                     command=self.play_song, style="Accent.TButton")
        self.play_button.grid(row=0, column=0, padx=(0, 10))

        # Stop button
        self.stop_button = ttk.Button(control_frame, text="Stop",
                                     command=self.stop_playing, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 10))

        # Validate button
        validate_button = ttk.Button(control_frame, text="Validate Notes",
                                   command=self.validate_notes)
        validate_button.grid(row=0, column=2, padx=(0, 10))

        # Clear button
        clear_button = ttk.Button(control_frame, text="Clear",
                                command=self.clear_song)
        clear_button.grid(row=0, column=3)

    def create_status_section(self, parent, row):
        """Create the status and log section."""
        status_frame = ttk.LabelFrame(parent, text="Status & Log", padding="10")
        status_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(1, weight=1)

        # Status label
        self.status_var = tk.StringVar(value="Ready to play")
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                               font=("Arial", 10, "bold"))
        status_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        # Log text area
        self.log_text = scrolledtext.ScrolledText(status_frame, height=6, width=50)
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def update_delay(self):
        """Update the note delay setting."""
        try:
            delay_str = self.delay_var.get().strip()
            if not delay_str:  # Handle empty string
                return

            delay = float(delay_str)
            if delay < 0.01:
                delay = 0.01
            elif delay > 2.0:
                delay = 2.0

            self.player.set_note_delay(delay)
            self.log(f"Note delay updated to {delay:.2f}s")

            # Update the variable if it was clamped
            if delay != float(delay_str):
                self.delay_var.set(str(delay))

        except ValueError:
            # Reset to last valid value
            self.delay_var.set(str(self.player.note_delay))
            self.log("Invalid delay value - reset to previous value")

    def update_mode(self):
        """Update the playing mode."""
        mode = self.mode_var.get()
        self.player.set_mode(mode)

        # Update mode info display
        if mode == "guqin":
            self.mode_info_var.set("Guqin: slow, expressive")
        elif mode == "fast":
            self.mode_info_var.set("Fast: 4x speed, no waits")
        else:
            tempo = float(self.tempo_var.get() or "1.0")
            self.mode_info_var.set(f"Custom: {tempo}x tempo")

        self.log(f"Playing mode changed to: {mode}")

    def update_tempo(self):
        """Update the tempo multiplier."""
        try:
            tempo_str = self.tempo_var.get().strip()
            if not tempo_str:
                return

            tempo = float(tempo_str)
            if tempo < 0.25:
                tempo = 0.25
            elif tempo > 4.0:
                tempo = 4.0

            self.player.set_tempo(tempo)
            self.mode_var.set("custom")  # Switch to custom mode when tempo is changed
            self.mode_info_var.set(f"Custom: {tempo}x tempo")
            self.log(f"Tempo set to {tempo}x (custom mode)")

            # Update the variable if it was clamped
            if tempo != float(tempo_str):
                self.tempo_var.set(str(tempo))

        except ValueError:
            self.tempo_var.set("1.0")
            self.log("Invalid tempo value - reset to 1.0")

    def validate_countdown(self):
        """Validate the countdown setting to ensure it's an integer."""
        try:
            countdown_str = self.countdown_var.get().strip()
            if not countdown_str:  # Handle empty string
                return

            # Try to convert to integer
            countdown = int(float(countdown_str))  # Convert to float first to handle decimals

            # Clamp to valid range
            if countdown < 1:
                countdown = 1
            elif countdown > 10:
                countdown = 10

            # Update the variable if it was changed
            if countdown != int(float(countdown_str)):
                self.countdown_var.set(str(countdown))

        except ValueError:
            # Reset to default value
            self.countdown_var.set("3")
            self.log("Invalid countdown value - reset to 3 seconds")

    def show_track_picker(self):
        """Show a dialog to pick specific tracks from a MIDI file."""
        if not self.current_midi_file:
            # Ask user to select a MIDI file first
            file_path = filedialog.askopenfilename(
                title="Select MIDI File to analyze tracks",
                filetypes=[("MIDI files", "*.mid;*.midi"), ("All files", "*.*")]
            )
            if not file_path:
                return
            self.current_midi_file = file_path
            self.file_path_var.set(os.path.basename(file_path))

        # Analyze the MIDI file tracks
        try:
            import mido
            mid = mido.MidiFile(self.current_midi_file)
        except Exception as e:
            messagebox.showerror("Error", f"Could not read MIDI file: {e}")
            return

        # Create track picker dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select MIDI Tracks")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Instructions
        ttk.Label(dialog, text="Select tracks to include in transcription:",
                  font=("Arial", 10, "bold")).pack(pady=(10, 5))
        ttk.Label(dialog, text="🎵 = likely melody, 🥁 = drums, 🎸 = bass",
                  foreground="gray").pack()

        # Scrollable frame for track list
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create listbox with scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE,
                             yscrollcommand=scrollbar.set, font=("Courier", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # Analyze and populate tracks
        track_info = []
        for i, track in enumerate(mid.tracks):
            notes = []
            channels = set()
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    channel = getattr(msg, 'channel', 0)
                    channels.add(channel)
                    notes.append(msg.note)

            if not notes:
                continue

            name = track.name[:20] if track.name else "(unnamed)"
            note_count = len(notes)
            avg_pitch = sum(notes) / len(notes)

            # Determine type icon
            if 9 in channels:
                icon = "🥁"
            elif avg_pitch > 70:
                icon = "🎵"
            elif avg_pitch < 50:
                icon = "🎸"
            else:
                icon = "🎹"

            display = f"{icon} Track {i}: {name:<20} ({note_count} notes, avg pitch {avg_pitch:.0f})"
            listbox.insert(tk.END, display)
            track_info.append((i, name, note_count, 9 in channels))

        # Buttons frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)

        def select_all():
            listbox.select_set(0, tk.END)

        def select_none():
            listbox.select_clear(0, tk.END)

        def select_no_drums():
            listbox.select_clear(0, tk.END)
            for idx, (track_idx, name, count, is_drum) in enumerate(track_info):
                if not is_drum:
                    listbox.select_set(idx)

        def apply_selection():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("No Selection", "Please select at least one track.")
                return

            # Get the actual track indices
            selected_tracks = [track_info[i][0] for i in selected_indices]
            self.midi_transcriber.selected_tracks = selected_tracks
            self.midi_transcriber.melody_track_only = False  # Disable melody-only when using manual selection
            self.melody_only_var.set(False)

            self.log(f"Selected tracks: {selected_tracks}")
            dialog.destroy()

            # Re-transcribe with selected tracks
            self._retranscribe_midi()

        ttk.Button(btn_frame, text="Select All", command=select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Select None", command=select_none).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="No Drums", command=select_no_drums).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Apply", command=apply_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Pre-select non-drum tracks
        select_no_drums()

    def test_delay(self):
        """Test the current delay setting with a short sequence."""
        if self.is_playing:
            messagebox.showinfo("Already Playing", "Please wait for current playback to finish.")
            return

        test_notes = "High1 High2 High3"
        self.log(f"Testing delay with notes: {test_notes}")
        self.log(f"Current delay: {self.player.note_delay}s")

        # Start the test in a separate thread
        self.is_playing = True
        self.play_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        test_thread = threading.Thread(target=self._test_delay_thread, args=(test_notes,))
        test_thread.daemon = True
        test_thread.start()

    def _test_delay_thread(self, test_notes):
        """Thread function to test delay."""
        try:
            self.update_status("Testing delay...")
            self.log("Starting delay test in 2 seconds...")
            time.sleep(2)

            if not self.is_playing:
                return

            notes = self.player.parse_notes(test_notes)
            for i, note in enumerate(notes, 1):
                if not self.is_playing:
                    return

                if self.player.validate_note(note):
                    self.player.play_single_note(note)
                    self.log(f"Test note {i}: {note}")

                    if i < len(notes) and self.is_playing:
                        self.log(f"Delay: {self.player.note_delay}s")
                        time.sleep(self.player.note_delay)

            self.log("Delay test completed!")

        except Exception as e:
            self.log(f"Error during delay test: {e}")
        finally:
            self.is_playing = False
            self.root.after(0, self._reset_play_ui)

    def upload_music_file(self):
        """Handle music file upload (PDF, image, MusicXML, or MIDI) and conversion."""
        file_path = filedialog.askopenfilename(
            title=(
                "Select Music File (PDF, Image, MusicXML, or MIDI) - "
                "PDFs/MusicXML work best with simple lines like '1 2 3 4 5 6 7' "
                "or 'do re mi fa sol la ti do'"
            ),
            filetypes=[
                ("All Music Files",
                 "*.pdf;*.png;*.jpg;*.jpeg;*.bmp;*.tiff;*.gif;*.mid;*.midi;*.mxl;*.musicxml;*.xml"),
                ("PDF files", "*.pdf"),
                ("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff;*.gif"),
                ("MusicXML files", "*.mxl;*.musicxml;*.xml"),
                ("MIDI files", "*.mid;*.midi"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name.lower())[1]

        self.file_path_var.set(file_name)

        # MIDI: use MIDI transcriber
        if file_ext in ['.mid', '.midi']:
            self.upload_status_var.set("Transcribing MIDI...")
            self.log(f"Selected MIDI file: {file_path}")
            processing_thread = threading.Thread(
                target=self._process_midi_file_thread,
                args=(file_path,)
            )
            processing_thread.daemon = True
            processing_thread.start()

        # MusicXML (.mxl/.musicxml/.xml): use MusicScoreReader directly
        elif file_ext in ['.mxl', '.musicxml', '.xml']:
            self.upload_status_var.set("Processing MusicXML...")
            self.log(f"Selected MusicXML score: {file_path}")

            def worker():
                try:
                    notes_string = self.score_reader.read_score(file_path)
                    if notes_string:
                        self.log(f"Successfully extracted notes from MusicXML: {notes_string}")

                        def update_song_input():
                            self.song_text.delete(1.0, tk.END)
                            self.song_text.insert(1.0, notes_string)
                            self.upload_status_var.set(
                                f"✅ Extracted {len(notes_string.split())} notes from MusicXML"
                            )
                        self.root.after(0, update_song_input)
                    else:
                        self.log("Could not extract notes from MusicXML score")

                        def show_error():
                            self.upload_status_var.set("❌ Could not extract music from MusicXML")
                            messagebox.showinfo(
                                "MusicXML Processing",
                                "Could not extract notes from this MusicXML file.\n\n"
                                "This feature works best with simple, single-melody scores."
                            )
                        self.root.after(0, show_error)
                except Exception as e:
                    self.log(f"Error processing MusicXML: {e}")

                    def show_error():
                        self.upload_status_var.set("❌ Error processing MusicXML")
                        messagebox.showerror(
                            "MusicXML Error",
                            f"An error occurred while processing the MusicXML file:\n{e}"
                        )
                    self.root.after(0, show_error)

            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()

        # Images: process as melody images
        elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']:
            self.upload_status_var.set("Processing image...")
            self.log(f"Selected melody image: {file_path}")
            processing_thread = threading.Thread(
                target=self._process_music_file_thread,
                args=(file_path,)
            )
            processing_thread.daemon = True
            processing_thread.start()

        # PDFs: process as score/PDF input
        elif file_ext == '.pdf':
            self.upload_status_var.set("Processing PDF/score file...")
            self.log(f"Selected score/PDF: {file_path}")
            processing_thread = threading.Thread(
                target=self._process_music_file_thread,
                args=(file_path,)
            )
            processing_thread.daemon = True
            processing_thread.start()

        # Anything else: unsupported
        else:
            self.upload_status_var.set("❌ Unsupported file type")
            self.log(f"Unsupported file type selected: {file_path}")
            messagebox.showwarning(
                "Unsupported File",
                "This file type is not supported. Please select a PDF, image, MusicXML (.mxl/.musicxml/.xml), or MIDI (.mid/.midi) file."
            )

    def upload_midi_file(self):
        """Handle MIDI file upload specifically."""
        file_path = filedialog.askopenfilename(
            title="Select MIDI File",
            filetypes=[
                ("MIDI files", "*.mid;*.midi"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        file_name = os.path.basename(file_path)
        self.file_path_var.set(file_name)
        self.upload_status_var.set("Transcribing MIDI...")
        self.log(f"Selected MIDI file: {file_path}")

        # Process MIDI in a separate thread
        processing_thread = threading.Thread(
            target=self._process_midi_file_thread,
            args=(file_path,)
        )
        processing_thread.daemon = True
        processing_thread.start()

    def convert_musicxml_pdf_to_huangpu(self):
        file_path = filedialog.askopenfilename(
            title="Select MusicXML or PDF",
            filetypes=[
                ("MusicXML files", "*.musicxml;*.xml"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )
        if not file_path:
            return

        self.file_path_var.set(os.path.basename(file_path))
        self.upload_status_var.set("Converting to Huangpu...")
        self.log(f"Selected for Huangpu conversion: {file_path}")

        def worker():
            try:
                huangpu = convert_input_to_huangpu(file_path)
                from huangpu_converter import huangpu_to_game_tokens
                game_tokens = huangpu_to_game_tokens(huangpu)
                def update_song_input():
                    self.song_text.delete(1.0, tk.END)
                    self.song_text.insert(1.0, game_tokens)
                    note_count = len(game_tokens.split())
                    self.upload_status_var.set(f"✅ Converted to Huangpu ({note_count} tokens)")
                self.root.after(0, update_song_input)
            except Exception as e:
                def show_error():
                    self.upload_status_var.set("❌ Huangpu conversion failed")
                    messagebox.showerror("Huangpu Conversion", f"Could not convert file to Huangpu.\n\nDetails:\n{e}")
                self.root.after(0, show_error)

        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    def _process_music_file_thread(self, file_path):
        """Process music file (PDF or image) in a separate thread."""
        try:
            file_ext = os.path.splitext(file_path.lower())[1]

            if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']:
                self.log("Attempting to extract melody from image...")
                self.log("Looking for: colored blocks, drawn shapes, line patterns")
            else:
                self.log("Attempting to extract music from PDF...")

            # Try to extract notes from file
            notes_string = self.score_reader.read_pdf_score(file_path)

            if notes_string:
                self.log(f"Successfully extracted notes: {notes_string}")

                # Update the song input with extracted notes
                def update_song_input():
                    self.song_text.delete(1.0, tk.END)
                    self.song_text.insert(1.0, notes_string)
                    self.upload_status_var.set(f"✅ Extracted {len(notes_string.split())} notes")

                self.root.after(0, update_song_input)

            else:
                error_msg = "Could not extract music from file"
                if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']:
                    self.log(error_msg)
                    self.log("For images, try:")
                    self.log("- Colored blocks (red, orange, yellow, green, blue, indigo, violet)")
                    self.log("- Simple drawn shapes or lines")
                    self.log("- Clear visual patterns")
                else:
                    self.log(error_msg)
                    self.log("This may be due to:")
                    self.log("- PDF contains scanned images without embedded music data")
                    self.log("- Required OCR/OMR libraries not installed")
                    self.log("- Complex music notation not supported")

                def show_error():
                    self.upload_status_var.set("❌ Could not extract music")
                    file_type = "image" if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif'] else "PDF"

                    if file_type == "image":
                        msg = ("Could not extract melody from this image.\n\n"
                               "This feature works best with:\n"
                               "• Colored blocks (red, orange, yellow, green, blue, indigo, violet)\n"
                               "• Simple drawn shapes or lines\n"
                               "• Clear visual patterns")
                    else:
                        msg = ("Could not extract music from this PDF.\n\n"
                               "This feature works best with:\n"
                               "• PDFs containing text-based music notation\n"
                               "• Simple melody lines\n"
                               "• Clear, high-quality scans")

                    messagebox.showinfo("File Processing", msg)

                self.root.after(0, show_error)

        except Exception as e:
            self.log(f"Error processing file: {e}")

            def show_error():
                self.upload_status_var.set("❌ Error processing file")
                messagebox.showerror("File Error", f"An error occurred while processing the file:\n{e}")

            self.root.after(0, show_error)

    def _process_midi_file_thread(self, file_path):
        """Process MIDI file in a separate thread."""
        try:
            self.log("Transcribing MIDI file to Jianpu notation...")

            # Try to transcribe MIDI to Jianpu
            jianpu_notes = self.midi_transcriber.transcribe_midi_file(file_path)

            if jianpu_notes:
                self.log(f"Successfully transcribed MIDI: {jianpu_notes[:100]}...")

                # Store the MIDI file path for re-transcription when filter changes
                self.current_midi_file = file_path

                # Update the song input with transcribed notes
                def update_song_input():
                    self.song_text.delete(1.0, tk.END)
                    self.song_text.insert(1.0, jianpu_notes)
                    note_count = len(jianpu_notes.split())
                    self.upload_status_var.set(f"✅ Transcribed {note_count} notes from MIDI ({self.filter_var.get()} filter)")

                self.root.after(0, update_song_input)

            else:
                self.log("Could not transcribe MIDI file")
                self.log("This may be due to:")
                self.log("- MIDI file format not supported")
                self.log("- Required MIDI libraries not installed")
                self.log("- Complex polyphonic music (try simpler melodies)")

                def show_error():
                    self.upload_status_var.set("❌ Could not transcribe MIDI")
                    messagebox.showinfo(
                        "MIDI Transcription",
                        "Could not transcribe this MIDI file.\n\n"
                        "This feature works best with:\n"
                        "• Simple melody lines (not complex polyphonic music)\n"
                        "• Standard MIDI files (.mid or .midi)\n"
                        "• Music in reasonable pitch ranges\n\n"
                        "Required libraries: mido, music21, or pretty_midi\n"
                        "Install with: pip install mido music21 pretty_midi"
                    )

                self.root.after(0, show_error)

        except Exception as e:
            self.log(f"Error transcribing MIDI: {e}")

            def show_error():
                self.upload_status_var.set("❌ Error transcribing MIDI")
                messagebox.showerror("MIDI Error", f"An error occurred while transcribing the MIDI:\n{e}")

            self.root.after(0, show_error)


    def _normalize_input(self, text: str) -> str:
        """Detect Huangpu-style input and convert to game tokens automatically."""
        hp_like = any(ch in text for ch in ["(", ")", ",", "'"]) or any(tok.strip().startswith(tuple(str(d) for d in range(1,8))) for tok in text.split())
        if hp_like:
            try:
                from huangpu_converter import huangpu_to_game_tokens
                return huangpu_to_game_tokens(text)
            except Exception:
                return text
        return text

    def validate_notes(self):
        """Validate the notes in the input area."""
        song = self.song_text.get(1.0, tk.END).strip()
        if not song:
            messagebox.showwarning("No Input", "Please enter some notes to validate.")
            return
        # Normalize Huangpu to game tokens if needed
        normalized = self._normalize_input(song)
        if normalized != song:
            self.song_text.delete(1.0, tk.END)
            self.song_text.insert(1.0, normalized)
            self.log("Auto-converted Huangpu to game tokens for validation")
        notes = self.player.parse_notes(normalized)
        invalid_notes = [note for note in notes if not self.player.validate_note(note)]

        if invalid_notes:
            self.log(f"Invalid notes found: {', '.join(invalid_notes)}")
            messagebox.showwarning("Invalid Notes",
                                 f"Invalid notes found:\n{', '.join(invalid_notes)}")
        else:
            self.log(f"All {len(notes)} notes are valid!")
            messagebox.showinfo("Validation Success",
                              f"All {len(notes)} notes are valid!")

    def clear_song(self):
        """Clear the song input area."""
        self.song_text.delete(1.0, tk.END)
        self.log("Song input cleared")

    def play_song(self):
        """Play the song in a separate thread."""
        song = self.song_text.get(1.0, tk.END).strip()
        if not song:
            messagebox.showwarning("No Input", "Please enter some notes to play.")
            return
        # Normalize Huangpu to game tokens if needed
        normalized = self._normalize_input(song)
        if normalized != song:
            self.song_text.delete(1.0, tk.END)
            self.song_text.insert(1.0, normalized)
            self.log("Auto-converted Huangpu to game tokens for playback")
        notes = self.player.parse_notes(normalized)
        invalid_notes = [note for note in notes if not self.player.validate_note(note)]

        if invalid_notes:
            result = messagebox.askyesno("Invalid Notes",
                                       f"Invalid notes found: {', '.join(invalid_notes)}\n\nContinue anyway?")
            if not result:
                return

        # Start playing in a separate thread
        self.is_playing = True
        self.play_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        play_thread = threading.Thread(target=self._play_song_thread, args=(normalized,))
        play_thread.daemon = True
        play_thread.start()

    def _play_song_thread(self, song):
        """Thread function to play the song."""
        try:
            try:
                countdown = int(float(self.countdown_var.get()))  # Convert to float first, then int
            except (ValueError, TypeError):
                countdown = 3  # Default fallback
                self.log("Invalid countdown value, using default 3 seconds")

            self.update_status(f"Preparing to play...")
            self.log(f"Starting playback with {countdown}s countdown")
            self.log(f"Note delay set to: {self.player.note_delay}s")

            # Countdown
            for i in range(countdown, 0, -1):
                if not self.is_playing:  # Check if stopped
                    return
                self.update_status(f"Starting in {i}...")
                self.log(f"Starting in {i}...")
                time.sleep(1)

            if not self.is_playing:  # Check if stopped
                return

            self.update_status("Playing...")
            self.log("Playing song!")

            # Parse and play notes
            notes = self.player.parse_notes(song)
            for i, note in enumerate(notes, 1):
                if not self.is_playing:  # Check if stopped
                    return

                if self.player.validate_note(note):
                    self.player.play_single_note(note)
                    self.log(f"Played note {i}/{len(notes)}: {note}")

                    # Add delay between notes (except after the last note)
                    if i < len(notes) and self.is_playing:
                        time.sleep(self.player.note_delay)

        except Exception as e:
            self.log(f"Error during playback: {e}")
            messagebox.showerror("Playback Error", f"An error occurred: {e}")
        finally:
            # Reset UI state
            self.is_playing = False
            self.root.after(0, self._reset_play_ui)

    def _reset_play_ui(self):
        """Reset the play UI state (must be called from main thread)."""
        self.play_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Ready to play")
        self.log("Playback completed")

    def stop_playing(self):
        """Stop the current playback."""
        self.is_playing = False
        self.log("Playback stopped by user")

    def update_status(self, message):
        """Update the status label (thread-safe)."""
        self.root.after(0, lambda: self.status_var.set(message))

    def log(self, message):
        """Add a message to the log (thread-safe)."""
        def _log():
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
        self.root.after(0, _log)


def main():
    """Main function to run the GUI."""
    root = tk.Tk()

    # Set up the style for better appearance
    style = ttk.Style()

    # Try to use a modern theme if available
    available_themes = style.theme_names()
    if 'vista' in available_themes:
        style.theme_use('vista')
    elif 'clam' in available_themes:
        style.theme_use('clam')

    # Create and run the application
    app = MusicPlayerGUI(root)

    # Handle window closing
    def on_closing():
        if app.is_playing:
            if messagebox.askokcancel("Quit", "A song is currently playing. Do you want to quit?"):
                app.is_playing = False
                root.destroy()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
