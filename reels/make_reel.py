"""Build a 9:16 Instagram reel from stills: slow zoom/pan, crossfades, price and call-to-action text.

Usage: python3 make_reel.py reel.json
The JSON lists segments (image, seconds, motion, text blocks). Frames are drawn with Pillow
and piped to FFmpeg, so no AI-video credits are needed.
"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, XF = 1080, 1920, 30, 0.35
FONTS = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "fonts"


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def ease(t):
    return t * t * (3 - 2 * t)


def cover(img, zoom, fx, fy):
    """Crop img to 9:16 at the given zoom, focused at (fx, fy) in 0..1, and resize to W x H."""
    iw, ih = img.size
    base = min(iw / W, ih / H)
    cw, ch = W * base / zoom, H * base / zoom
    x = (iw - cw) * fx
    y = (ih - ch) * fy
    return img.resize((W, H), Image.LANCZOS, box=(x, y, x + cw, y + ch))


def text_layer(blocks, alpha):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if alpha <= 0:
        return layer
    for b in blocks:
        f = font(b["font"], b["size"])
        d = ImageDraw.Draw(layer)
        box = d.textbbox((0, 0), b["text"], font=f)
        tw, th = box[2] - box[0], box[3] - box[1]
        x = (W - tw) / 2 - box[0]
        y = b["y"] - box[1]
        if b.get("pill"):
            px, py = 34, 18
            d.rounded_rectangle([x + box[0] - px, y + box[1] - py, x + box[2] + px, y + box[3] + py],
                                radius=999, fill=tuple(b["pill"]))
        else:
            shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(shadow).text((x, y + 3), b["text"], font=f, fill=(0, 0, 0, 170))
            layer.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)))
        d.text((x, y), b["text"], font=f, fill=tuple(b.get("color", [255, 255, 255])))
        if b.get("strike"):
            my = y + box[1] + th * 0.55
            d.line([x + box[0] - 6, my, x + box[2] + 6, my], fill=tuple(b.get("color", [255, 255, 255])), width=5)
    if alpha < 1:
        a = layer.getchannel("A").point(lambda v: int(v * alpha))
        layer.putalpha(a)
    return layer


def segment_frame(seg, img, t):
    p = ease(min(max(t / seg["seconds"], 0), 1))
    m = seg.get("motion", {})
    z = m.get("zoom", [1, 1.08])
    fx = m.get("fx", [0.5, 0.5])
    fy = m.get("fy", [0.3, 0.3])
    frame = cover(img, z[0] + (z[1] - z[0]) * p, fx[0] + (fx[1] - fx[0]) * p, fy[0] + (fy[1] - fy[0]) * p).convert("RGBA")
    if seg.get("shade"):
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        for i in range(H):
            top = max(0, 1 - i / 520) * 0.55
            bot = max(0, (i - (H - 760)) / 760) * 0.7
            gd.line([0, i, W, i], fill=(0, 0, 0, int(255 * max(top, bot))))
        frame.alpha_composite(g)
    alpha = min(1, max(0, (t - 0.25) / 0.35))
    frame.alpha_composite(text_layer(seg.get("text", []), alpha))
    return frame.convert("RGB")


def main():
    cfg_path = Path(sys.argv[1])
    cfg = json.loads(cfg_path.read_text())
    root = cfg_path.parent
    segs = cfg["segments"]
    imgs = [Image.open(root / s["image"]).convert("RGB") for s in segs]
    starts, t = [], 0.0
    for s in segs:
        starts.append(t)
        t += s["seconds"] - XF
    total = t + XF
    out = root / cfg["output"]
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=44100:cl=stereo",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    for n in range(int(total * FPS)):
        now = n / FPS
        active = [i for i, s in enumerate(segs) if starts[i] <= now < starts[i] + s["seconds"]]
        frame = segment_frame(segs[active[0]], imgs[active[0]], now - starts[active[0]])
        if len(active) > 1:
            j = active[1]
            mix = (now - starts[j]) / XF
            frame = Image.blend(frame, segment_frame(segs[j], imgs[j], now - starts[j]), mix)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    ff.wait()
    print(out, f"{total:.1f}s")


if __name__ == "__main__":
    main()
