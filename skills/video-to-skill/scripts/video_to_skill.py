#!/usr/bin/env python3
"""Turn a video link into a Claude skill.

  run  URL   downloads the video, grabs frames, makes a transcript and writes notes.md
  save DIR   copies a finished skill (DIR/SKILL.md plus the frames you kept) into a skills folder

Needs ffmpeg and ffprobe on PATH, and the packages in requirements.txt (scripts/setup.py installs them).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

MEDIA_EXT = {".mp4", ".mkv", ".webm", ".mov", ".m4a", ".mp3"}
SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def need_tool(name):
    if not shutil.which(name):
        die(f"NEED_{name.upper()}: install {name} first (Windows: winget install ffmpeg, Mac: brew install ffmpeg)")


def hms(seconds):
    s = int(seconds)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def file_stamp(seconds):
    s = int(seconds)
    return f"{s // 3600:02d}-{(s % 3600) // 60:02d}-{s % 60:02d}"


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:60].strip("-")


def ffprobe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def has_audio(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return bool(r.stdout.strip())


# ---------- step 1: find the video and download it ----------

def probe_info(url):
    import yt_dlp
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("_type") == "playlist" and info.get("entries"):
        info = info["entries"][0]
    return info


def download(url, work, lang, redownload):
    import yt_dlp
    existing = [p for p in work.glob("source.*") if p.suffix.lower() in MEDIA_EXT]
    if existing and not redownload:
        print(f"Using existing download: {existing[0].name}")
        return existing[0]
    opts = {
        "format": "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]/b",
        "merge_output_format": "mp4",
        "outtmpl": str(work / "source.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "writesubtitles": True,        # uploader's captions
        "writeautomaticsub": True,     # machine captions, used only if no uploaded ones
        "subtitleslangs": [f"{lang}.*"],
        "subtitlesformat": "vtt",
        "convertsubtitles": "vtt",
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    media = [p for p in work.glob("source.*") if p.suffix.lower() in MEDIA_EXT]
    if not media:
        die("Download finished but no video file was found. Check the link opens in a browser.")
    return media[0]


def keep_captions(work, lang):
    """Keep one caption file as captions.vtt. Returns True if found."""
    pattern = "source.*.vtt" if lang == "auto" else f"source.{lang}*.vtt"
    vtts = sorted(work.glob(pattern))
    if not vtts:
        return False
    shutil.copyfile(vtts[0], work / "captions.vtt")
    for v in work.glob("source.*.vtt"):
        v.unlink()
    return True


# ---------- step 2: frames and contact sheets ----------

def grab_frames(media, work, every, max_frames, scene):
    frames_dir = work / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)
    tmp = frames_dir / "_raw"
    tmp.mkdir()

    # Pick a frame at the start, then one every N seconds, plus any scene change.
    expr = f"isnan(prev_selected_t)+gte(t-prev_selected_t\\,{every})"
    if scene:
        expr += f"+gt(scene\\,{scene})"
    vf = f"select='{expr}',showinfo,scale=960:-2"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "info", "-y", "-i", str(media),
           "-vf", vf, "-fps_mode", "vfr", "-frames:v", str(max_frames), "-q:v", "4",
           str(tmp / "raw_%03d.jpg")]
    r = subprocess.run(cmd, capture_output=True, text=True)
    times = [float(m.group(1)) for m in re.finditer(r"pts_time:([\d.]+)", r.stderr)]
    raws = sorted(tmp.glob("raw_*.jpg"))

    index = []
    for i, (raw, t) in enumerate(zip(raws, times), start=1):
        name = f"{i:03d}_{file_stamp(t)}.jpg"
        raw.rename(frames_dir / name)
        index.append({"file": name, "seconds": round(t, 2), "time": hms(t)})
    shutil.rmtree(tmp)
    (frames_dir / "frames.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    make_contact_sheets(frames_dir, index)
    return index


def make_contact_sheets(frames_dir, index, per_sheet=12, cols=3, cell_w=320):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow not installed; skipping contact sheets (view frames one by one).")
        return
    try:
        font = ImageFont.load_default(size=20)
    except TypeError:
        font = ImageFont.load_default()
    for s, start in enumerate(range(0, len(index), per_sheet), start=1):
        chunk = index[start:start + per_sheet]
        rows = (len(chunk) + cols - 1) // cols
        frame_h = int(cell_w * 9 / 16)
        cell_h = frame_h + 28
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (24, 24, 24))
        draw = ImageDraw.Draw(sheet)
        for n, item in enumerate(chunk):
            x, y = (n % cols) * cell_w, (n // cols) * cell_h
            img = Image.open(frames_dir / item["file"]).convert("RGB")
            img.thumbnail((cell_w, frame_h))
            sheet.paste(img, (x, y))
            label = f"#{start + n + 1}  {item['time']}"
            draw.text((x + 6, y + frame_h + 4), label, fill=(240, 240, 240), font=font)
        sheet.save(frames_dir / f"sheet_{s:02d}.jpg", quality=85)


# ---------- step 3: transcript ----------

def hms_to_seconds(text):
    parts = [float(p) for p in text.replace(",", ".").split(":")]
    secs = 0.0
    for p in parts:
        secs = secs * 60 + p
    return secs


def parse_vtt(path):
    segments = []
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8", errors="replace"))
    for block in blocks:
        lines = [ln.strip() for ln in block.strip().splitlines()]
        arrow = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if arrow is None:
            continue
        start = hms_to_seconds(lines[arrow].split("-->")[0].strip())
        text = " ".join(re.sub(r"<[^>]+>", "", ln) for ln in lines[arrow + 1:]).strip()
        if not text:
            continue
        # YouTube auto-captions "roll": each cue repeats the previous line and adds words.
        if segments:
            prev = segments[-1]
            if text == prev["text"] or prev["text"].startswith(text):
                continue
            if text.startswith(prev["text"]):
                prev["text"] = text
                continue
        segments.append({"start": start, "text": text})
    return segments


def whisper_segments(media, work, lang, model_name):
    audio = work / "audio.wav"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(media),
                    "-vn", "-ac", "1", "-ar", "16000", str(audio)], check=True)
    try:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            die("faster-whisper is missing. Run scripts/setup.py first.")
        try:
            model = WhisperModel(model_name, device="auto", compute_type="default")
        except Exception as e:  # usually the model download is blocked or offline
            die(f"Could not load Whisper model '{model_name}' ({e}). "
                "It downloads once from huggingface.co; check the network, or pass a model you already have.")
        segs, info = model.transcribe(str(audio), language=None if lang == "auto" else lang, vad_filter=True)
        out = [{"start": s.start, "text": s.text.strip()} for s in segs if s.text.strip()]
    finally:
        audio.unlink(missing_ok=True)
    print(f"Detected language: {info.language} ({info.language_probability:.0%})")
    return out


def make_transcript(media, work, lang, model_name):
    if not has_audio(media):
        (work / "transcript.txt").write_text("(This video has no audio track.)\n", encoding="utf-8")
        return "none", []
    if (work / "captions.vtt").exists():
        segments = parse_vtt(work / "captions.vtt")
        source = "captions"
    else:
        segments = whisper_segments(media, work, lang, model_name)
        source = f"whisper-{model_name}"
    lines = [f"[{hms(s['start'])}] {s['text']}" for s in segments]
    (work / "transcript.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (work / "transcript.json").write_text(
        json.dumps({"source": source, "segments": segments}, indent=2, ensure_ascii=False), encoding="utf-8")
    return source, segments


# ---------- run ----------

def write_notes(work, info, source, segments, index, url, duration):
    words = sum(len(s["text"].split()) for s in segments)
    sheets = sorted(p.name for p in (work / "frames").glob("sheet_*.jpg"))
    lines = [
        f"# {info.get('title', 'Untitled video')}",
        "",
        f"- Link: {url}",
        f"- Uploader: {info.get('uploader') or info.get('channel') or 'unknown'}",
        f"- Length: {hms(duration)}",
        f"- Transcript: {source} ({words} words, {len(segments)} segments)",
        f"- Frames: {len(index)}",
        "",
        "## Read these first",
        "",
        "- `transcript.txt` : what is said, with timestamps",
        f"- `frames/{sheets[0]}` ... : contact sheets, 12 frames each, labelled with time" if sheets else "- (no contact sheets)",
        "- `frames/frames.json` : frame file names and times",
        "",
        "## Description (from the uploader)",
        "",
        (info.get("description") or "(none)")[:1500],
        "",
    ]
    if source == "captions":
        lines.insert(7, "- Note: captions may be machine-made. Check names, numbers and technical words.")
    (work / "notes.md").write_text("\n".join(lines), encoding="utf-8")
    (work / "source.json").write_text(json.dumps({
        "url": url,
        "title": info.get("title"),
        "uploader": info.get("uploader") or info.get("channel"),
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration"),
    }, indent=2, ensure_ascii=False), encoding="utf-8")


def cmd_run(args):
    need_tool("ffmpeg")
    need_tool("ffprobe")
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        die("yt-dlp is missing. Run scripts/setup.py first.")

    print("Reading video info...", flush=True)
    info = probe_info(args.url)
    slug = args.name or slugify(info.get("title")) or f"video-{info.get('id', 'clip')}"
    work = Path(args.work) / slug
    work.mkdir(parents=True, exist_ok=True)
    print(f"Work folder: {work.resolve()}", flush=True)

    print("Downloading video...", flush=True)
    media = download(args.url, work, args.lang, args.redownload)
    if args.redownload or not (work / "captions.vtt").exists():
        keep_captions(work, args.lang)

    print("Grabbing frames...", flush=True)
    index = grab_frames(media, work, args.every, args.max_frames, args.scene)

    print("Making transcript...", flush=True)
    source, segments = make_transcript(media, work, args.lang, args.model)

    duration = info.get("duration") or ffprobe_duration(media)
    write_notes(work, info, source, segments, index, args.url, duration)
    print("\nDone.")
    print(f"  Work folder : {work.resolve()}")
    print(f"  Frames      : {len(index)} (plus contact sheets in frames/)")
    print(f"  Transcript  : {source}, {len(segments)} segments")
    print(f"  Read first  : {(work / 'notes.md').resolve()}")


# ---------- save ----------

def read_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        die(f"{path} has no frontmatter. It must start with a --- block containing name and description.")
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm


def cmd_save(args):
    work = Path(args.work)
    skill_md = work / "SKILL.md"
    if not skill_md.exists():
        die(f"No SKILL.md in {work}. Write it first, then save.")
    fm = read_frontmatter(skill_md)
    name = fm.get("name", "")
    if not SKILL_NAME.match(name):
        die(f"name in SKILL.md must be lowercase letters, digits and hyphens (got '{name}').")
    if not fm.get("description"):
        die("SKILL.md frontmatter needs a description.")

    dest = Path(args.dest).expanduser() / name
    if dest.exists():
        if not args.force:
            die(f"{dest} already exists. Pass --force to replace it, or pick another name in SKILL.md.")
        shutil.rmtree(dest)
    (dest / "references").mkdir(parents=True)
    shutil.copyfile(skill_md, dest / "SKILL.md")

    # The video itself is never copied. Frames are copied only if they are still in frames/
    # (delete the ones you do not need first). The transcript is copied only with --transcript.
    frames_src = work / "frames"
    if frames_src.exists():
        frames_dst = dest / "references" / "frames"
        frames_dst.mkdir()
        kept = []
        for f in sorted(frames_src.glob("*.jpg")):
            if f.name.startswith("sheet_"):
                continue
            shutil.copyfile(f, frames_dst / f.name)
            kept.append(f.name)
        index = frames_src / "frames.json"
        if index.exists():
            all_meta = json.loads(index.read_text(encoding="utf-8"))
            kept_meta = [m for m in all_meta if m["file"] in kept]
            (frames_dst / "frames.json").write_text(json.dumps(kept_meta, indent=2), encoding="utf-8")

    if args.transcript and (work / "transcript.txt").exists():
        shutil.copyfile(work / "transcript.txt", dest / "references" / "transcript.txt")

    if (work / "source.json").exists():
        src = json.loads((work / "source.json").read_text(encoding="utf-8"))
        (dest / "references" / "source.md").write_text(
            "# Source\n\n"
            f"- Original video: {src.get('url')}\n"
            f"- Title: {src.get('title')}\n"
            f"- Uploader: {src.get('uploader') or 'unknown'}\n"
            f"- Upload date: {src.get('upload_date') or 'unknown'}\n\n"
            "This skill was written from the video above. The steps are a summary in new words, "
            "not a copy of the video.\n",
            encoding="utf-8")

    size = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())
    frames_kept = len(list((dest / "references" / "frames").glob("*.jpg"))) if (dest / "references" / "frames").exists() else 0
    size_text = f"{size / 1_000_000:.1f} MB" if size >= 1_000_000 else f"{size / 1000:.0f} KB"
    print(f"Saved skill '{name}' to {dest}")
    print(f"  {frames_kept} frames kept, transcript {'included' if args.transcript else 'not included'}, {size_text}")
    print("Restart Claude Code (or open a new session) and type /" + name)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="download, frames, transcript")
    r.add_argument("url")
    r.add_argument("--work", default="video-to-skill-work", help="folder that holds work folders")
    r.add_argument("--name", help="work folder name (default: from the video title)")
    r.add_argument("--lang", default="en", help="spoken language code, e.g. en, ml, hi, or auto")
    r.add_argument("--every", type=float, default=10, help="seconds between frames (default 10)")
    r.add_argument("--max-frames", type=int, default=60)
    r.add_argument("--scene", type=float, default=0.35,
                   help="also grab frames at scene changes above this score, 0 to turn off (default 0.35)")
    r.add_argument("--model", default="base", help="Whisper model: tiny, base, small, medium, large-v3")
    r.add_argument("--redownload", action="store_true", help="download again even if the video is there")
    r.set_defaults(func=cmd_run)

    s = sub.add_parser("save", help="copy a finished skill into a skills folder")
    s.add_argument("work", help="the work folder that has SKILL.md")
    s.add_argument("--dest", default="~/.claude/skills", help="skills folder (default ~/.claude/skills)")
    s.add_argument("--transcript", action="store_true", help="also copy transcript.txt into references/")
    s.add_argument("--force", action="store_true", help="replace an existing skill of the same name")
    s.set_defaults(func=cmd_save)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
