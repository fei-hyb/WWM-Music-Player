You are a Python + music-theory expert helping me improve a script called GameMusicPlayer (shown below).
It plays the Guqin in a PC game using Jianpu (numbered notation) and pydirectinput.

Right now the script only supports natural notes 1–7 for three octaves:

High: High1–High7 → keys Q W E R T Y U

Medium: Med1–Med7 → keys A S D F G H J

Low: Low1–Low7 → keys Z X C V B N M

The game’s Guqin actually has extra semitone notes as shown in the in-game layout:

#1 between 1 and 2

b3 between 2 and 3

#4 between 4 and 5

#5 between 5 and 6

b7 between 6 and 7

In the game:

Holding Shift while pressing the base key = higher semitone (#)

Holding Ctrl while pressing the base key = lower semitone (b)

Example:

3 (medium) = key D

b3 (medium) = Ctrl + D

#4 (high) = Shift + R

What I want you to change

Take the existing GameMusicPlayer class and extend it with clean, well-structured support for sharps/flats based on the screenshot and rules above.

1. Note naming & parsing

Keep the existing note names backwards compatible, but add semitone variants:

Allow notes like:

High#1, Highb3, Med#4, Lowb7

With durations: High#4:q, Medb3:h, etc.

The pattern should be:

(<octave><accidental?><degree>)[:<duration_code>]

where <octave> is High, Med, or Low

<accidental?> is optional # or b

<degree> is 1–7

Keep existing syntax working:

High1, Med3:e, Low5, rests (0, 0:q) and wait keywords.

You can add small helper functions if needed, e.g.:

def split_note_components(note: str) -> tuple[str, Optional[str], Optional[str]]:
"""Return (base_octave, accidental, degree) without duration."""


…but design it however is clearest.

2. Internal mapping for semitones

Keep self.note_map as the mapping for base natural notes (already there).

Add logic that, given a parsed note:

Determines:

the base note key (e.g., High3 → 'e')

and the modifier:

None for natural notes

'shift' for sharps (#)

'ctrl' for flats (b)

You can either:

parse the accidental from the note string (High#4 → accidental #), or

add a small helper:

def get_modifier_for_accidental(accidental: Optional[str]) -> Optional[str]:
# '#' -> 'shift', 'b' -> 'ctrl'

3. Actually pressing modifier + key

Add a small method that encapsulates pressing one note, with or without modifier, using pydirectinput:

def _press_key_with_modifier(self, key: str, modifier: Optional[str]) -> None:
"""
Press `key` alone, or with 'shift' / 'ctrl' held for semitones.
"""


Implementation requirements:

Natural notes: just pydirectinput.press(key).

Sharp notes: Shift + key.

Flat notes: Ctrl + key.

Use keyDown / keyUp so that the modifier is held during the key press, not pressed sequentially.

Pseudo:

if modifier:
pydirectinput.keyDown(modifier)
pydirectinput.press(key)
pydirectinput.keyUp(modifier)
else:
pydirectinput.press(key)


Then modify play_single_note to:

Parse duration (:q, :h, etc.) as it already does.

Parse the accidental/degree.

Look up the base note in self.note_map.

Call _press_key_with_modifier(base_key, modifier) instead of calling pydirectinput.press directly.

All existing behavior for durations, waits, rests, and warnings should still work.

4. Validation

Update validate_note so that:

It recognizes semitone note names like High#1, Medb3, Low#5:e as valid.

It still accepts:

Wait keywords (wait, hold, -, etc.)

Rests (0, 0:q).

It uses the same parsing logic as play_single_note (to avoid duplicated parsing bugs).

If a note has an accidental but its base note isn’t in self.note_map, treat it as invalid and surface a warning the same way the current code does.

5. Display & documentation

Update display_note_map() to mention semitones:

Add lines explaining:

“Hold Shift for higher semitone (#), Ctrl for lower semitone (b)”

Example text for Jianpu input:

High1 High#1 High2 Medb3 Med3 Med#4 Low5 Low#5 Low6 Lowb7 Low7

Do not remove the existing mapping display; just extend it.

6. Cleanliness & safety

Keep the public API of GameMusicPlayer the same:

play_song, play_single_note, display_note_map, etc.

Make parsing helpers small and easily testable.

Add docstrings or comments where behavior might not be obvious (especially parsing and modifier logic).

Do not break existing songs that only use natural notes.

Quick test cases (for you to try in code comments / docstring examples)

After the change, the following should work:

player.play_song("High1 High#1 High2 Medb3 Med3 Med#4 Low5 Low#5 Low6 Lowb7 Low7")

With durations:
player.play_song("High1:q High#1:e Medb3:h 0:q Med3:q Med#4:s")

None of the existing examples that only use High1–High7, Med1–Med7, Low1–Low7, waits, or rests should need any modification.

Use these instructions to modify the existing code in place; don’t rewrite the whole file from scratch.