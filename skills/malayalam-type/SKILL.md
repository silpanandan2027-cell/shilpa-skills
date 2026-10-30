---
name: malayalam-type
description: Animate Malayalam text for videos and reels. Makes titles, one-word pops, lower thirds, quotes, counters, checklists, call-to-action pills and word-timed subtitles that never break Malayalam letters. Renders to MP4 or to a transparent overlay you can lay over your own footage. Use when the user types /malayalam-type or asks for Malayalam text animation, titles, captions, subtitles or an animated text overlay.
---

# malayalam-type

Animated Malayalam text, rendered with Chrome and ffmpeg. You describe scenes in a small JSON file and the skill draws them.

The user is usually not technical. Keep replies short and friendly, do the work for them, and never ask them to run commands.

All paths are relative to this skill's folder. Use its absolute path in commands.

After setup, run every `python ...` command below with this skill's own Python: `.venv\Scripts\python.exe` on Windows, `.venv/bin/python` on Mac and Linux. (Setup itself runs with any Python.)

## 1. First run

Run `python scripts/setup.py`. It prints `READY` when done (about a minute the first time).
- `NEED_FFMPEG`: install it for them (Windows: `winget install ffmpeg`, Mac: `brew install ffmpeg`), then run setup again.
- `NEED_PYTHON`: install Python 3.12 (Windows: `winget install Python.Python.3.12`), then run setup again.

## 2. Ask only for what is missing

- The Malayalam lines (or a script to pull lines from).
- Where it goes: a stand-alone video (default 1080x1920), or an overlay on their footage.
- A look: `paper` (cream, orange), `night` (dark, amber), `sky` (pale blue), or `clear` for overlays (white text with a soft shadow). They can set their own colours.

Write the lines the way people say them (ഓട്ടോമാറ്റിക്, റീൽ). Keep brand names in English. If you fix a typo in their text, say so in the final message.

## 3. Write the scene file

`scenes.json`, next to their files. Times are in seconds from the start of the video.

```json
{"size": "1080x1920", "theme": "paper",
 "scenes": [
   {"kind": "title", "at": 0, "dur": 2.6, "kicker": "ടിപ്", "lines": [{"ml": "ഇനി എല്ലാം", "en": "all in one place"}, {"ml": "ഓട്ടോമാറ്റിക്", "accent": "ഓട്ടോമാറ്റിക്"}]},
   {"kind": "cta", "at": 3, "dur": 2.4, "ml": "കമന്റ് ചെയ്യൂ"}
 ]}
```

See `examples/demo.json` for one of every kind.

| `kind` | What it draws | Fields (all but `at`, `dur` optional) |
|---|---|---|
| `title` | Big centred lines, one word can be coloured | `lines` (`ml`, `en`, `accent`) or `ml`, `en`, `accent`; `kicker`, `size`, `y` |
| `keyword` | One giant word with an underline that draws itself | `ml` (needed), `en`, `kicker`, `size`, `bar` |
| `lower` | A card at the bottom: small label, title, English line | `ml`, `kicker`, `en`, `accent`, `y` |
| `quote` | A serif quote with the speaker's name | `ml`, `accent`, `by` |
| `counter` | A number that counts up, with a Malayalam label | `from`, `to`, `prefix`, `suffix`, `decimals`, `ml` |
| `list` | A card per item, each ticking in one after another | `title`, `items` (list), `step` |
| `cta` | A pill button that pulses, for "comment X" moments | `ml`, `en` |
| `captions` | Subtitles that follow the speech, the spoken word lit | `words` (`[{"t": 1.2, "e": 1.6, "w": "വാക്ക്"}]`), `max`, `size`, `y` |

Common fields on every scene: `anim` (`rise`, `blur`, `pop`, `fade`), `font` (`display`, `sans`, `serif`, `round`, `soft`, `hand`), `fade` (how long it takes to leave, seconds), `y` (top position, percent of the height).

Rules that keep Malayalam correct (the engine does the first three for you):
- Letters are animated as whole clusters. Never split a conjunct such as ക്ഷ, സ്റ്റ or ന്ത.
- Lines only break between words, and a line that is too wide shrinks to fit.
- There is no clipping box around the text, so vowel signs above and below the line stay visible.
- Keep each line short: about 20 letters at the default size. Break longer text into two lines with `\n` or two scenes.
- One display font per scene. English is always in Inter.
- A visual change at least every 2.5 seconds keeps a reel moving.

For subtitles from speech, run `python scripts/words.py <video>` (see section 6), then put its word times in a `captions` scene.

## 4. Check, then render

1. Check frames first (fast): `python scripts/render.py scenes.json check --still 1.5,4.0` writes `check_1.50.png` and so on. Use a time in the middle of each scene. Look at the PNGs yourself and fix anything cut off, too small or wrong.
2. Video: `python scripts/render.py scenes.json out.mp4`
3. Transparent overlay for their own footage: `python scripts/render.py scenes.json overlay.mov --alpha`, then lay it over the video (or use the `reel-fx` skill, which does this for them).
4. Options: `--fps 30`, `--size 1080x1920`, `--range 2,9` to render only part of the timeline.

Tell them where the file is. Remind them in one line to watch it before posting.

## 5. Fonts

All fonts are free under the SIL Open Font Licence (licence files are in `fonts/`).

| `font` | Face | Good for |
|---|---|---|
| `display` | Anek Malayalam ExtraBold | titles, captions |
| `sans` | Noto Sans Malayalam | cards, lists, small text |
| `serif` | Noto Serif Malayalam | quotes, stories |
| `round` | Baloo Chettan 2 | friendly keywords, buttons |
| `soft` | Manjari | calm, rounded text (uses traditional letter forms) |
| `hand` | Chilanka | handwritten asides |
| English | Inter | everything in English, numbers |

## 6. Word times for captions

`python scripts/words.py <video-or-audio> --lang ml` listens to the speech and writes `<name>.words.json` with each word's start and end time. It installs its own speech model on first use (a few minutes, once). Whisper's Malayalam is good but not perfect: read the words back to the user and fix mistakes before you render.

## 7. Limits to be honest about

- The text is drawn on top of or beside the video. It does not go behind a person.
- Rendering runs about 1 to 3 frames per second at 1080x1920, so a 30 second clip takes a few minutes.
