#!/usr/bin/env python3
"""Find when each word is spoken, for word-timed captions.

  python words.py clip.mp4 --lang ml          -> prints "start  word" lines, saves clip.words.json
  options: --model small|base|medium  (default small)   --lang ml|en|auto (default ml)

Uses faster-whisper, installed into this skill's own environment the first time it is needed.
The result is a list of {"t": start, "e": end, "w": word} ready to paste into a `captions` scene.
"""
import argparse, json, os, subprocess, sys

os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', '1')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')   # Windows consoles cannot print Malayalam by default

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('--lang', default='ml'); ap.add_argument('--model', default='small')
a = ap.parse_args()

try:
    from faster_whisper import WhisperModel
except ImportError:
    print('Installing the speech model library (one time, a minute or two)...', flush=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'faster-whisper'], check=True)
    from faster_whisper import WhisperModel

# Decode the audio with ffmpeg ourselves (16 kHz mono) so we do not depend on the PyAV version.
import numpy as np
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', a.src, '-vn', '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                     capture_output=True, check=True).stdout
audio = np.frombuffer(raw, dtype=np.float32)

model = WhisperModel(a.model, device='cpu', compute_type='int8')
segs, info = model.transcribe(audio, word_timestamps=True, vad_filter=True,
                              language=None if a.lang == 'auto' else a.lang)
words = [{'t': round(w.start, 2), 'e': round(w.end, 2), 'w': w.word.strip()}
         for s in segs for w in (s.words or []) if w.word.strip()]

out = os.path.splitext(a.src)[0] + '.words.json'
json.dump(words, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for w in words:
    print(f"{w['t']:7.2f}  {w['w']}")
print(f"\nLanguage: {info.language}. Saved {len(words)} words to {out}")
