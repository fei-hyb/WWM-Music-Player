"""
Music Player Launcher
Choose between GUI and command-line interface
"""

import sys
import subprocess

def main():
    print("=== Game Music Player ===")
    print("Choose your interface:")
    print("1. GUI (Graphical User Interface) - Recommended")
    print("2. CLI (Command Line Interface)")
    print("3. Quit")

    while True:
        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == '1':
            print("Starting GUI...")
            try:
                # Use subprocess to run in the same Python environment
                subprocess.run([sys.executable, "music_player_gui.py"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error starting GUI: {e}")
            except KeyboardInterrupt:
                print("\nGUI closed.")
            break

        elif choice == '2':
            print("Starting CLI...")
            try:
                # Use subprocess to run in the same Python environment
                subprocess.run([sys.executable, "game_music_player.py"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error starting CLI: {e}")
            except KeyboardInterrupt:
                print("\nCLI closed.")
            break

        elif choice == '3':
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
