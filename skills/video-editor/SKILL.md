---
name: video-editor
description: Be the user's video editor with five tools - Remotion (videos written in React), HyperFrames (videos written in HTML), FFmpeg (cut, join, convert, audio), Whisper (whisper.cpp speech to text, subtitles) and yt-dlp (download a video from a link). Use when the user asks to edit, cut, trim, join, caption, subtitle, transcribe, download, render or make a video, motion graphic, intro, explainer or reel, or types /video-editor.
---

# Video editor

The user is usually not technical. Keep replies short, do the work for them, and never ask them to run commands.

| Tool | Use it for | Check it is installed |
|---|---|---|
| FFmpeg | cut, trim, join, resize to 9:16, speed, extract or replace audio, convert | `ffmpeg -version` |
| yt-dlp | download a video or its audio from YouTube, Instagram and other links | `yt-dlp --version` |
| Whisper (whisper.cpp) | transcribe speech, word timings, `.srt` subtitles | `whisper-cli --help` |
| HyperFrames | animated videos written in HTML: titles, captions, overlays, explainers | `npx hyperframes --version` |
| Remotion | animated videos written in React | `npx remotion --version` |

The other skills in this repo do the finishing: `/reel-fx` for effects on the user's own footage, `/malayalam-type` for Malayalam text.

## 1. First run

Check each tool above. Install whatever is missing without asking:

- Mac: `brew install ffmpeg yt-dlp whisper-cpp node`
- Windows: `winget install Gyan.FFmpeg yt-dlp.yt-dlp OpenJS.NodeJS.LTS`, then `whisper-bin-x64.zip` from the whisper.cpp GitHub releases page (`install.ps1` does this)
- Linux: `apt-get install -y ffmpeg`, `pip install -U yt-dlp`, build whisper.cpp with cmake (see `install.sh`)
- HyperFrames and Remotion need Node.js 22 or newer: `npm install -g hyperframes @remotion/cli`

Whisper needs a model the first time. Use `base` (multilingual, works for Malayalam and English); `small` is better for Malayalam if speed allows:
`bash <whisper.cpp>/models/download-ggml-model.sh base`. In cloud sessions whisper.cpp lives in `/opt/whisper.cpp` and `base` is already downloaded.

## 2. Recipes

- **Download**: `yt-dlp -f "bv*+ba/b" --merge-output-format mp4 -o "raw-footage/%(title)s.%(ext)s" <url>`. Audio only: `-x --audio-format mp3`. Only download videos the user owns or has the right to use.
  - YouTube and Instagram often refuse cloud servers ("Sign in to confirm you're not a bot", or a redirect to the Instagram login page). On the user's own computer, add `--cookies-from-browser chrome` (or `edge`, `firefox`). In a cloud session, ask the user to export a `cookies.txt` for that site with a browser extension such as "Get cookies.txt LOCALLY", upload it, and add `--cookies cookies.txt`. Treat that file as a password: never print it, commit it or keep it after the download. If it still fails, ask the user to upload the video file instead.
- **Trim**: `ffmpeg -ss 00:00:05 -to 00:00:20 -i in.mp4 -c:v libx264 -c:a aac out.mp4`
- **Vertical 9:16**: `ffmpeg -i in.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" -c:a copy out.mp4`
- **Join**: list the files in `list.txt` (`file 'a.mp4'` per line), then `ffmpeg -f concat -safe 0 -i list.txt -c copy out.mp4` (re-encode if the clips differ).
- **Transcribe / subtitles**: `ffmpeg -i in.mp4 -ar 16000 -ac 1 audio.wav`, then `whisper-cli -m <model> -f audio.wav -l auto -osrt -ml 42` (add `-ojf` for word timings). Read the words back to the user before using them; fix names and Malayalam mistakes.
- **Burn subtitles**: `ffmpeg -i in.mp4 -vf subtitles=audio.wav.srt -c:a copy out.mp4`, or style them with `/reel-fx` or a HyperFrames caption block.
- **Motion graphics in HTML (HyperFrames)**: `npx hyperframes init my-video --non-interactive --resolution portrait` (add `--video clip.mp4` to build on footage; it transcribes with Whisper), edit `index.html`, then `npx hyperframes preview` and `npx hyperframes render -o exports/out.mp4`. Run `npx hyperframes doctor` if a render fails. The `hyperframes` plugin skills hold the full guide.
- **Motion graphics in React (Remotion)**: `npx create-video@latest`, edit `src/`, then `npx remotion render <entry> <CompositionId> exports/out.mp4`. Follow the `remotion-best-practices` skill if installed. Remotion is free for individuals and small teams; companies of 4 or more people need a licence.

If Chrome cannot be found in a cloud session, pass `--browser-executable=/opt/pw-browsers/chromium` to Remotion.

## 3. Before handing over

Look at a few frames (`ffmpeg -ss <t> -i out.mp4 -frames:v 1 frame.png`) and check the length and size with `ffprobe`. Fix anything wrong, then put the result in `exports/` and tell the user in one line.
