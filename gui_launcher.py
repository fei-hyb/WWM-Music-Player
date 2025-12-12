"""
Simple GUI Launcher - Directly launches the GUI interface
"""

def main():
    print("Starting Game Music Player GUI...")
    print("Make sure to focus your game window during the countdown!")
    print()

    try:
        import tkinter as tk
        from music_player_gui import MusicPlayerGUI

        root = tk.Tk()
        app = MusicPlayerGUI(root)

        # Handle window closing gracefully
        def on_closing():
            if hasattr(app, 'is_playing') and app.is_playing:
                import tkinter.messagebox as messagebox
                if messagebox.askokcancel("Quit", "A song is currently playing. Do you want to quit?"):
                    app.is_playing = False
                    root.destroy()
            else:
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()

    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Please make sure all dependencies are installed:")
        print("  pip install pydirectinput")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
