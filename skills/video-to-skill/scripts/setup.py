#!/usr/bin/env python3
"""One-time setup: makes a private Python environment for this skill and installs yt-dlp,
faster-whisper and Pillow. Prints READY when done. Safe to run again (it also updates yt-dlp,
which YouTube breaks often)."""
import os, shutil, subprocess, sys, venv, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
vdir = root / '.venv'
py = vdir / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')

if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
    sys.exit('NEED_FFMPEG: install ffmpeg first (Windows: winget install ffmpeg, Mac: brew install ffmpeg)')
if sys.version_info < (3, 9):
    sys.exit('NEED_PYTHON: Python 3.9 or newer is required (python.org/downloads)')

if not py.exists():
    venv.create(vdir, with_pip=True)
subprocess.run([str(py), '-m', 'pip', 'install', '-q', '-U', '-r', str(root / 'requirements.txt')], check=True)
subprocess.run([str(py), '-c', 'import yt_dlp, faster_whisper, PIL'], check=True)
print('READY')
