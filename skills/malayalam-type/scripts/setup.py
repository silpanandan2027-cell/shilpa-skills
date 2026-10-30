#!/usr/bin/env python3
"""One-time setup: makes a private Python environment for this skill and installs Playwright.
Prints READY when everything works. Safe to run again."""
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
subprocess.run([str(py), '-m', 'pip', 'install', '-q', '-r', str(root / 'requirements.txt')], check=True)

check = ('from playwright.sync_api import sync_playwright\n'
         'with sync_playwright() as p:\n'
         '    for ch in ("chrome", "msedge", None):\n'
         '        try:\n'
         '            b = p.chromium.launch(channel=ch) if ch else p.chromium.launch(); b.close(); print("READY", ch or "chromium"); raise SystemExit\n'
         '        except SystemExit: raise\n'
         '        except Exception: pass\n'
         'print("NEED_BROWSER")\n')
r = subprocess.run([str(py), '-c', check], capture_output=True, text=True)
out = (r.stdout or '').strip()
if 'READY' in out:
    print(out)
else:
    print('Installing a browser for rendering (one time)...', flush=True)
    subprocess.run([str(py), '-m', 'playwright', 'install', 'chromium'], check=True)
    print('READY chromium')
