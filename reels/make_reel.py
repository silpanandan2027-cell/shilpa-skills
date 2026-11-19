"""Build a soft, pastel 9:16 Instagram fashion reel from stills.

Usage: python3 make_reel.py reel.json [fonts_dir]

reel.json has:
  output    : mp4 path (relative to the json)
  segments  : shots in order: image, seconds, motion {zoom, fx, fy}, handheld, fade (crossfade into this shot)
  texts     : overlays on the whole timeline: text, style (brand | script | small | price), y, start, end,
              reveal (type | pop | fade)
  sparkles  : twinkling stars: x, y, size, start, end
  sticker   : true for the pink flower in the corner

Frames are drawn with Pillow and piped to FFmpeg; no AI-video credits needed.
"""
import json, math, subprocess, sys
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
FONTS = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "fonts"
PINK, HOT, WHITE = (255, 105, 160), (236, 24, 122), (255, 255, 255)

STYLES = {
    "brand":  dict(font="Poppins-ExtraBold.ttf", size=104, fill=HOT, stroke=8, glow=(255, 255, 255)),
    "script": dict(font="GreatVibes-Regular.ttf", size=96, fill=PINK, stroke=4, glow=(255, 255, 255)),
    "price":  dict(font="Poppins-ExtraBold.ttf", size=92, fill=WHITE, stroke=7, glow=HOT, stroke_fill=HOT),
    "small":  dict(font="Poppins-SemiBold.ttf", size=34, fill=WHITE, stroke=3, glow=None, stroke_fill=(90, 40, 60)),
}


@lru_cache(None)
def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def back_out(t):
    t = min(max(t, 0.0), 1.0)
    c = 1.7
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


@lru_cache(None)
def text_image(text, style, size=None):
    s = STYLES[style]
    f = font(s["font"], size or s["size"])
    pad = 60
    box = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), text, font=f, stroke_width=s["stroke"])
    w, h = box[2] - box[0] + pad * 2, box[3] - box[1] + pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    org = (pad - box[0], pad - box[1])
    if s.get("glow"):
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).text(org, text, font=f, fill=s["glow"] + (200,), stroke_width=s["stroke"] + 6,
                               stroke_fill=s["glow"] + (200,))
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(img).text(org, text, font=f, fill=s["fill"], stroke_width=s["stroke"],
                             stroke_fill=s.get("stroke_fill", WHITE))
    return img


def place_text(frame, t, now):
    life = now - t["start"]
    if life < 0 or now > t["end"]:
        return
    out = min(1.0, (t["end"] - now) / 0.25)
    reveal = t.get("reveal", "fade")
    text = t["text"]
    full = text_image(text, t["style"], t.get("size"))
    img = full
    alpha = min(1.0, life / 0.3) * out
    if reveal == "type":
        n = max(1, int(len(text) * min(1.0, life / max(0.6, len(text) * 0.055))))
        part = text_image(text[:n], t["style"], t.get("size"))
        img = Image.new("RGBA", full.size, (0, 0, 0, 0))
        img.paste(part, (0, 0))  # left-aligned inside the full-width box so letters don't jump
        alpha = out
    elif reveal == "pop":
        k = 0.6 + 0.4 * back_out(life / 0.45)
        img = full.resize((max(1, int(full.width * k)), max(1, int(full.height * k))), Image.LANCZOS)
    if alpha < 1:
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
    x = (W - (full.width if reveal == "type" else img.width)) // 2 + t.get("dx", 0)
    y = t["y"] - img.height // 2
    frame.alpha_composite(img, (int(x), int(y)))


@lru_cache(None)
def star(size):
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, r, w = s / 2, s / 2, s / 14
    d.polygon([(c, c - r), (c + w, c - w), (c + r, c), (c + w, c + w), (c, c + r), (c - w, c + w), (c - r, c), (c - w, c - w)],
              fill=(255, 255, 255, 255))
    glow = img.filter(ImageFilter.GaussianBlur(s / 10))
    glow.alpha_composite(img)
    return glow.resize((size * 2, size * 2), Image.LANCZOS)


def place_sparkle(frame, sp, now):
    life = now - sp["start"]
    if life < 0 or now > sp["end"]:
        return
    k = abs(math.sin(life * math.pi / sp.get("period", 0.9)))
    size = max(2, int(sp["size"] * (0.25 + 0.75 * k)))
    img = star(size)
    frame.alpha_composite(img, (int(sp["x"] - img.width / 2), int(sp["y"] - img.height / 2)))


@lru_cache(None)
def flower():
    s = 600
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([(300, 330), (285, 580)], fill=(110, 150, 95, 255), width=9)
    d.ellipse([200, 470, 290, 510], fill=(130, 170, 110, 255))
    for i in range(6):
        petal = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        pd = ImageDraw.Draw(petal)
        pd.ellipse([262, 120, 338, 300], fill=(255, 196, 214, 255))
        pd.ellipse([276, 150, 324, 290], fill=(255, 170, 198, 255))
        img.alpha_composite(petal.rotate(i * 60 + 12, center=(300, 300), resample=Image.BICUBIC))
    d.ellipse([272, 272, 328, 328], fill=(250, 205, 90, 255))
    d.ellipse([286, 286, 314, 314], fill=(235, 160, 60, 255))
    return img.filter(ImageFilter.GaussianBlur(0.8)).resize((150, 150), Image.LANCZOS)


@lru_cache(None)
def sticker_image(path, width):
    img = Image.open(path).convert("RGBA")
    return img.resize((width, int(img.height * width / img.width)), Image.LANCZOS)


def grade(img):
    img = ImageEnhance.Brightness(img).enhance(1.05)
    img = ImageEnhance.Color(img).enhance(1.06)
    r, g, b = img.split()
    r = r.point(lambda v: min(255, int(v * 1.03 + 3)))
    b = b.point(lambda v: int(v * 0.97))
    img = Image.merge("RGB", (r, g, b))
    bloom = img.filter(ImageFilter.GaussianBlur(18))
    return Image.blend(img, bloom, 0.12)


def shot(seg, img, t):
    p = ease(t / seg["seconds"])
    m = seg.get("motion", {})
    z0, z1 = m.get("zoom", [1.0, 1.06])
    fx0, fx1 = m.get("fx", [0.5, 0.5])
    fy0, fy1 = m.get("fy", [0.3, 0.3])
    zoom, fx, fy = z0 + (z1 - z0) * p, fx0 + (fx1 - fx0) * p, fy0 + (fy1 - fy0) * p
    rot = 0.0
    if seg.get("handheld"):
        zoom += 0.03
        fx += 0.012 * math.sin(t * 1.7) + 0.006 * math.sin(t * 4.1)
        fy += 0.010 * math.sin(t * 1.3 + 1)
        rot = 0.35 * math.sin(t * 1.1)
    iw, ih = img.size
    base = min(iw / W, ih / H)
    cw, ch = W * base / zoom, H * base / zoom
    x, y = (iw - cw) * min(max(fx, 0), 1), (ih - ch) * min(max(fy, 0), 1)
    frame = img.resize((W, H), Image.BICUBIC, box=(x, y, x + cw, y + ch))
    if rot:
        frame = frame.rotate(rot, resample=Image.BICUBIC, expand=False)
    return frame


def main():
    cfg_path = Path(sys.argv[1])
    cfg = json.loads(cfg_path.read_text())
    root = cfg_path.parent
    segs = cfg["segments"]
    imgs = [grade(Image.open(root / s["image"]).convert("RGB")) for s in segs]
    starts, t = [], 0.0
    for i, s in enumerate(segs):
        if i:
            t -= s.get("fade", 0.3)
        starts.append(t)
        t += s["seconds"]
    total = t
    out = root / cfg["output"]
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=44100:cl=stereo",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    for n in range(int(total * FPS)):
        now = n / FPS
        active = [i for i, s in enumerate(segs) if starts[i] <= now < starts[i] + s["seconds"]]
        frame = shot(segs[active[0]], imgs[active[0]], now - starts[active[0]])
        if len(active) > 1:
            j = active[1]
            mix = (now - starts[j]) / max(segs[j].get("fade", 0.3), 1e-3)
            frame = Image.blend(frame, shot(segs[j], imgs[j], now - starts[j]), ease(mix))
        frame = frame.convert("RGBA")
        for sp in cfg.get("sparkles", []):
            place_sparkle(frame, sp, now)
        st = cfg.get("sticker")
        if st:
            fl = sticker_image(root / st["file"], st["w"]) if isinstance(st, dict) and st.get("file") else flower()
            x, y = (st["x"], st["y"]) if isinstance(st, dict) else (W - fl.width - 70, H - fl.height - 230)
            frame.alpha_composite(fl, (int(x), int(y + 5 * math.sin(now * 2))))
        for tx in cfg.get("texts", []):
            place_text(frame, tx, now)
        ff.stdin.write(frame.convert("RGB").tobytes())
    ff.stdin.close()
    ff.wait()
    print(out, f"{total:.1f}s")


if __name__ == "__main__":
    main()
