#!/usr/bin/env python3
"""One-time setup: a private Python environment for reel-studio with Playwright (renders the reels)
and edge-tts (free voiceover). Prints READY when everything works. Safe to run again."""
import os, shutil, subprocess, sys, venv, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
vdir = root / '.venv'
py = vdir / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')

if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
    sys.exit('NEED_FFMPEG: install ffmpeg first (Windows: winget install ffmpeg, Mac: brew install ffmpeg)')
if sys.version_info < (3, 9):
    sys.exit('NEED_PYTHON: Python 3.9 or newer is required (python.org/downloads)')
if not (root.parent / 'malayalam-type' / 'fonts').is_dir():
    sys.exit('NEED_MALAYALAM_TYPE: the malayalam-type skill (it holds the fonts) must sit next to this one')

if not py.exists():
    venv.create(vdir, with_pip=True)
subprocess.run([str(py), '-m', 'pip', 'install', '-q', '-U', '-r', str(root / 'requirements.txt')], check=True)

r = subprocess.run([str(py), str(root / 'scripts' / 'browser.py')], capture_output=True, text=True)
if 'READY' in r.stdout:
    print(r.stdout.strip())
else:
    print('Installing a browser for rendering (one time)...', flush=True)
    subprocess.run([str(py), '-m', 'playwright', 'install', 'chromium'], check=True)
    print('READY chromium')
