from pathlib import Path
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

_spec_source = globals().get('spec_filename')
if _spec_source:
    spec_path = Path(_spec_source).resolve()
elif '__file__' in globals():
    spec_path = Path(__file__).resolve()
else:
    spec_path = Path.cwd() / 'packaging' / 'game_music_player.spec'

project_root = spec_path.parent.parent
script_path = project_root / 'gui_launcher.py'
icon_path = spec_path.parent / 'game_music_player.ico'
icon_file = str(icon_path) if icon_path.exists() else None
repro_data = [
    'game_music_player.py',
    'music_player_gui.py',
    'music_score_reader.py',
    'midi_to_jianpu.py',
    'music_parser.py',
    'huangpu_converter.py',
    'playback_engine.py',
    'requirements.txt',
    'README.md',
    'PDF_READER_GUIDE.md',
    'achineseghoststory.mid',
    '(Yukiko Niijima) FFVIII - Balamb Garden.mid',
    "(Mielle Uccello) Tifa's Theme (Final Fantasy 7).mid",
]

a = Analysis(
    [str(script_path)],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(project_root / rel_path), rel_path) for rel_path in repro_data],
    hiddenimports=['tkinter', 'pydirectinput', 'pytesseract'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tests'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data,
    cipher=block_cipher,
)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GameMusicPlayer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon_file,
)
bundle = BUNDLE(
    exe,
    name='GameMusicPlayer',
    format='onefile',
    bundle_files=[]
)
