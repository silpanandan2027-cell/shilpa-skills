# Shilpa's Claude Skills

Two skills for [Claude Code](https://claude.com/claude-code) that edit your videos for you. You talk, Claude does the editing.

| Skill | What it does |
|---|---|
| `/malayalam-type` | Animated Malayalam text that never breaks the letters: titles, one-word pops, lower thirds, quotes, counters, checklists, call-to-action buttons and word-timed subtitles. Makes a video or a transparent overlay. |
| `/reel-fx` | Effects for your own video: zoom in and out, punch-in, brightness and lighting, rotation, blur, mirror, camera shake, 7 colour looks, vignette, flash, cinema bars, progress bar, plus any `/malayalam-type` text laid on top. Keeps your audio. |

## Install

You need Claude Code. The skills help install ffmpeg and Python the first time you use them.

**Windows (PowerShell)**
```powershell
git clone https://github.com/silpanandan2027-cell/shilpa-skills
cd shilpa-skills
powershell -ExecutionPolicy Bypass -File install.ps1
```

**Mac / Linux**
```bash
git clone https://github.com/silpanandan2027-cell/shilpa-skills
cd shilpa-skills && ./install.sh
```

Then restart Claude Code. Type `/` and the skills appear.

> Easier: open Claude Code and say **"Install the skills from github.com/silpanandan2027-cell/shilpa-skills"**.

## Use

1. Open Claude Code.
2. Drag your video into the chat.
3. Say what you want:

```
/reel-fx warm colour, a zoom when I say "ശ്രദ്ധ", and a title at the start
/reel-fx add subtitles to this reel
/malayalam-type make a title card: "ഇനി എല്ലാം ഓട്ടോമാറ്റിക്"
```

Claude checks a few frames first, fixes anything that looks wrong, then renders. The first time, it sets itself up (about 2 minutes).

## What you need

- Windows, Mac or Linux
- Chrome or Edge (already on most computers)
- ffmpeg and Python 3.9 or newer (Claude installs them if missing)

## Good to know

- Text is drawn on top of your video. It does not go behind a person.
- Subtitles come from a speech model. Malayalam speech recognition is good but not perfect, so read the words before you post.
- Always watch the result before posting.

## Licence

MIT, see `LICENSE`. Fonts in `skills/malayalam-type/fonts` are free under the SIL Open Font Licence (licence files next to them).
