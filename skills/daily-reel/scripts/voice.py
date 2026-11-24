#!/usr/bin/env python3
"""Step 3: voiceover in the cloned ElevenLabs voice, plus word timings.

    python3 voice.py script.txt OUT_DIR --voice VOICE_ID [--model eleven_multilingual_v2] [--scribe]

Writes OUT_DIR/voice.mp3 and OUT_DIR/words.json ([{"text","start","end"}] in seconds).
Timings come from the text-to-speech alignment; --scribe re-times the words from the
audio with ElevenLabs Scribe (speech to text) instead.

The API key comes from ELEVENLABS_API_KEY. In cloud sessions the network proxy adds the
saved key for api.elevenlabs.io, so the placeholder below is replaced on the way out.
"""
import argparse, base64, json, os, pathlib, sys
import requests

API = "https://api.elevenlabs.io/v1"
KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_proxy_injected")


def tts(text, voice, model):
    r = requests.post(
        f"{API}/text-to-speech/{voice}/with-timestamps",
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": KEY},
        json={"text": text, "model_id": model,
              "voice_settings": {"stability": 0.45, "similarity_boost": 0.85, "style": 0.2,
                                 "use_speaker_boost": True}},
        timeout=180)
    if r.status_code != 200:
        sys.exit(f"ElevenLabs text-to-speech failed {r.status_code}: {r.text[:400]}")
    return r.json()


def words_from_alignment(al):
    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    out, cur, s = [], "", None
    for c, a, b in zip(chars, st, en):
        if c.isspace():
            if cur:
                out.append({"text": cur, "start": round(s, 3), "end": round(last, 3)})
            cur, s = "", None
            continue
        if s is None:
            s = a
        cur += c
        last = b
    if cur:
        out.append({"text": cur, "start": round(s, 3), "end": round(last, 3)})
    return out


def scribe(mp3):
    with open(mp3, "rb") as f:
        r = requests.post(f"{API}/speech-to-text", headers={"xi-api-key": KEY},
                          data={"model_id": "scribe_v1", "timestamps_granularity": "word"},
                          files={"file": ("voice.mp3", f, "audio/mpeg")}, timeout=300)
    if r.status_code != 200:
        sys.exit(f"ElevenLabs Scribe failed {r.status_code}: {r.text[:400]}")
    return [{"text": w["text"], "start": round(w["start"], 3), "end": round(w["end"], 3)}
            for w in r.json().get("words", []) if w.get("type", "word") == "word"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("out")
    ap.add_argument("--voice", required=True)
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--scribe", action="store_true")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    text = pathlib.Path(a.script).read_text(encoding="utf-8").strip()
    res = tts(text, a.voice, a.model)
    mp3 = out / "voice.mp3"
    mp3.write_bytes(base64.b64decode(res["audio_base64"]))
    words = scribe(mp3) if a.scribe else words_from_alignment(res.get("normalized_alignment") or res["alignment"])
    (out / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    dur = words[-1]["end"] if words else 0
    print(json.dumps({"audio": str(mp3), "words": len(words), "seconds": dur}))


if __name__ == "__main__":
    main()
