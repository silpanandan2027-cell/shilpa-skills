# GTA 6: Everything You Need to Know (YouTube video)

A 4-minute English explainer for the GTA 6 launch on November 19, 2026, built here from scratch.
Backgrounds are official GTA VI screenshots and key art from rockstargames.com/VI, with camera moves,
light leaks, grain and flash cuts on top. Graphics are drawn in code, the music is generated from scratch,
and the voiceover is offline text-to-speech.

## What's here

| File | What it is |
|---|---|
| `script.md` | The script, on-screen notes, the YouTube description and chapters |
| `build/out/GTA6_explainer.mp4` | The finished video, 1920x1080, 30 fps, about 4:16 including an 18 s end screen |
| `build/out/GTA6_thumbnail.jpg` | 1280x720 thumbnail |
| `build/out/GTA6_explainer.en.srt` | English subtitles: upload them under Subtitles in YouTube Studio |

The video files are not committed to git because they're too big. Rebuild them with the steps below.

## Upload checklist

1. **Title:** `GTA 6: Everything You Need to Know Before November 19`
2. **Description and chapters:** copy them from the bottom of `script.md`.
3. **Thumbnail:** `GTA6_thumbnail.jpg`.
4. **Subtitles:** upload the `.srt` file under Subtitles → Add language → English → Upload file.
5. **End screen:** the last 18 seconds have dashed boxes. Put two video elements on the left and right boxes and the Subscribe element on the circle.
6. **Altered or synthetic content:** the voice is AI-generated, but nothing shows real people or
   realistic events, so YouTube usually doesn't require the label. If you're unsure, ticking it is harmless.
7. **Rockstar images:** the description credits them. Commentary channels use these images all the time,
   but YouTube can still flag Rockstar material. If that happens you'll see it in Studio under Copyright.

## Adding official trailer clips (optional)

If you want real game footage, download clips from Rockstar's official trailers yourself and lay them
over these spots in CapCut or another editor. Keep each clip short (3 to 6 seconds) and leave the
"Footage © Rockstar Games" line in the description.

| Time | Suggested trailer moment |
|---|---|
| 0:09–0:19 | Opening beach and sunset shots |
| 1:15–1:20 | Aerial view of Vice City |
| 1:25–1:32 | Swamps, the Keys, the countryside |
| 1:38–1:43 | Crowds and phones (the social media shots) |
| 1:56–2:01 | Lucia in prison |
| 2:02–2:06 | Jason |
| 3:25–3:37 | Final shot of the latest trailer |

## Official images

`build/prep_assets.sh` copies the chosen images from the downloaded set into `build/assets/rs/` and
cuts three of the site's sticker animations (flamingo, gator, crab) into transparent frames. These
files belong to Rockstar, so they stay out of git. Download them again from rockstargames.com/VI to rebuild.

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
