# GTA 6: Everything You Need to Know (YouTube video)

A 4-minute English explainer for the GTA 6 launch on November 19, 2026, built here from scratch.
All visuals are drawn in code, the music is generated, and the voiceover is offline text-to-speech,
so there are no copyright problems with any of it.

## What's here

| File | What it is |
|---|---|
| `script.md` | The script, on-screen notes, the YouTube description and chapters |
| `build/out/GTA6_explainer.mp4` | The finished video, 1920x1080, 30 fps, about 4:10 including a 18 s end screen |
| `build/out/GTA6_thumbnail.jpg` | 1280x720 thumbnail |
| `build/out/GTA6_explainer.en.srt` | English subtitles: upload them under Subtitles in YouTube Studio |

The video files are not committed to git because they're too big. Rebuild them with the steps below.

## Upload checklist

1. **Title:** `GTA 6 Is 4 Days Away: Everything You Need to Know`
2. **Description and chapters:** copy them from the bottom of `script.md`.
3. **Thumbnail:** `GTA6_thumbnail.jpg`.
4. **Subtitles:** upload the `.srt` file under Subtitles → Add language → English → Upload file.
5. **End screen:** the last 18 seconds have dashed boxes. Put two video elements on the left and right boxes and the Subscribe element on the circle.
6. **Altered or synthetic content:** the voice is AI-generated, but nothing shows real people or
   realistic events, so YouTube usually doesn't require the label. If you're unsure, ticking it is harmless.

## Adding official trailer clips (optional)

If you want real game footage, download clips from Rockstar's official trailers yourself and lay them
over these spots in CapCut or another editor. Keep each clip short (3 to 6 seconds) and leave the
"Footage © Rockstar Games" line in the description.

| Time | Suggested trailer moment |
|---|---|
| 0:03–0:11 | Opening beach and sunset shots |
| 1:10–1:15 | Aerial view of Vice City |
| 1:20–1:27 | Swamps, the Keys, the countryside |
| 1:33–1:39 | Crowds and phones (the social media shots) |
| 1:51–1:56 | Lucia in prison |
| 1:56–2:01 | Jason |
| 3:20–3:30 | Final shot of the latest trailer |

## Rebuild

Needs ffmpeg, Node with Playwright, and Python with `sherpa-onnx soundfile numpy scipy`.
The speech models download from the sherpa-onnx GitHub releases into `/tmp/claude-0/models`
(`kokoro-int8-multi-lang-v1_0`).

```bash
cd build
python3 tts.py                 # voiceover + sentence timings  -> out/vo.wav, out/timing.json
python3 music.py 250.4 out/music.wav
python3 extras.py              # subtitles
node render.js video out/seg/p0.mp4 0 63    # ...and 63-126, 126-189, 189-999 in parallel
node thumb.js
# then concat the parts, mux with the ducked mix (see the ffmpeg lines in the session log)
```

Change the words in `script.md` and rerun `tts.py`. The visuals follow the new timings automatically,
because every callout is pinned to a sentence, not to a fixed time.
