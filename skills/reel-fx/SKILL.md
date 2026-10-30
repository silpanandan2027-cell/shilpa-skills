---
name: reel-fx
description: Add effects and animated Malayalam text to a video or reel (zoom in and out, punch-in, brightness and lighting, rotation, blur, mirror, camera shake, colour looks, vignette, flash, cinema bars, progress bar, titles, lower thirds, counters, call-to-action buttons, word-timed subtitles). Use when the user types /reel-fx, or asks to add an effect, zoom, colour grade, caption, subtitle, title or text animation to a video they give you.
---

# reel-fx

Takes the user's video and a short plan, and returns the same video (with its original audio) with effects and animated Malayalam text on top.

The user is usually not technical. Keep replies short and friendly, do the work for them, and never ask them to run commands.

All paths are relative to this skill's folder. Use its absolute path in commands. `fx.py` needs only Python and ffmpeg. The text effects use the sibling skill `malayalam-type`, which installs next to this one.

## 1. First run

1. ffmpeg must be installed. If `ffmpeg -version` fails, install it for them (Windows: `winget install ffmpeg`, Mac: `brew install ffmpeg`).
2. If the plan has any `text` effect, `malayalam-type` must be set up once: run `python ../malayalam-type/scripts/setup.py` and wait for `READY`. If `fx.py` prints `NEED_MALAYALAM_TYPE`, do that and try again.

## 2. Get the video and what they want

- Video: they drag the file into the chat or give a path. A vertical phone video works best. The output is 1080 pixels wide (short side), which is the standard for reels.
- What they want: effects by name, or a description ("make it dramatic", "caption what I say", "title at the start"). Match their words to the table. If they say "everything", pick what suits the video (about one change every 2 to 3 seconds); do not pile every effect on one clip.
- Timing: if they say "when I say X", get word times first, using the text skill's own Python: `../malayalam-type/.venv/Scripts/python.exe ../malayalam-type/scripts/words.py <video> --lang ml` (on Mac and Linux: `.venv/bin/python`). Read the words back to them and fix mistakes. Otherwise ask one short question, or choose sensible moments yourself.

## 3. The effects

Run `python scripts/fx.py --list` for this list.

| `fx` | What it does | Options |
|---|---|---|
| `punch` | Quick zoom in and back out on a moment | `zoom` (1.3), `x`, `y` (where to zoom, 0 to 1; use `y` around 0.3 to aim at a face) |
| `zoom` | Slow zoom in or out over the time given (`from` bigger than `to` zooms out) | `from` (1.0), `to` (1.3), `hold` (keep the end zoom), `x`, `y` |
| `brightness` (or `light`) | Brighten, darken or relight a moment | `amount` (0.15, negative darkens), `contrast`, `saturation`, `gamma`, `ramp` |
| `rotate` | Tilt the picture and back (the picture is zoomed a little so no corners show) | `angle` (6, up to 15 either way), `ramp` |
| `blur` | Blur the picture | `strength` (12) |
| `mirror` | Flip left to right | |
| `shake` | Camera shake | `amount` (0.012) |
| `grade` | A colour look | `look`: `warm`, `cool`, `mono`, `film`, `moody`, `pop`, `fade` |
| `vignette` | Dark edges | `strength` |
| `flash` | A white flash, good with a punch | `at`, `dur` (0.25) |
| `bars` | Cinema black bars | `size` (0.1) |
| `progress` | A thin bar across the top that fills | `color`, `height` |
| `text` | Animated Malayalam text | any malayalam-type scene: `kind`, `ml`, `en`, `accent`, `kicker`, `items`, `words_file` ... (see `../malayalam-type/SKILL.md`) |

Every effect takes `start` and `end` (seconds), or `start` and `dur`. Leave them out to cover the whole video. Effects run in the order listed in the plan.

## 4. Write the plan, check, render

1. Write `plan.json` next to their video:
   ```json
   {"theme": "clear", "effects": [
     {"fx": "grade", "look": "warm"},
     {"fx": "punch", "start": 3.2, "end": 4.8, "zoom": 1.3, "y": 0.3},
     {"fx": "text", "kind": "lower", "start": 1, "dur": 3, "kicker": "Day 01", "ml": "ജോലി തുടങ്ങാം", "accent": "ജോലി", "en": "work mode on"},
     {"fx": "text", "kind": "captions", "words_file": "clip.words.json"}
   ]}
   ```
   `theme` for text defaults to `clear` (white text with a soft shadow, made for lying over video). Other themes (`paper`, `night`, `sky`) give coloured cards and text. `colors` can override `ink`, `accent`, `card`.
2. Check frames first (fast): `python scripts/fx.py plan.json <video> check.png --still 2.5,6` writes `check_2.50.png` and so on, using a time in the middle of each effect. Look at the PNGs yourself. Fix anything that covers the face, is cut off or is hard to read.
3. Render: `python scripts/fx.py plan.json <video> <name>_fx.mp4`. A 30 second clip takes a few minutes when it has text; effects without text are much faster. Run it in the background if your tool times out.
4. Tell them where the file is and remind them in one line to watch it before posting.

## 5. Rules

- Do not put text over the face. Use `y` to move it (percent of the height from the top).
- Keep zoom at 1.5 or less so the video stays sharp.
- Short effects look best: 1 to 3 seconds each.
- Text is drawn on top of the video. It does not go behind a person, and effects do not follow a face.
- This skill adds visuals only. Sound effects and music are up to the user.
