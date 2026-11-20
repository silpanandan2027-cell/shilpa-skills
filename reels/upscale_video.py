"""Make a small AI clip reel-ready: smooth it to 30 fps with motion interpolation, upscale each frame
with FSRCNN x4 super-resolution, and fill a 2160x3840 (4K vertical) frame.

Usage: python3 upscale_video.py in.mp4 out.mp4 [threads]
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2

src, dst = sys.argv[1], sys.argv[2]
threads = int(sys.argv[3]) if len(sys.argv) > 3 else 4
cv2.setNumThreads(threads)
W, H = 2160, 3840
model = Path(__file__).parent / "models" / "FSRCNN_x4.pb"

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    smooth = tmp / "smooth.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
                    "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
                    "-c:v", "libx264", "-crf", "12", "-preset", "fast", str(smooth)], check=True)
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel(str(model))
    sr.setModel("fsrcnn", 4)
    cap = cv2.VideoCapture(str(smooth))
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", "30", "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", dst], stdin=subprocess.PIPE)
    n = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        big = sr.upsample(frame)
        h, w = big.shape[:2]
        s = max(W / w, H / h)
        big = cv2.resize(big, (round(w * s), round(h * s)), interpolation=cv2.INTER_LANCZOS4)
        y, x = (big.shape[0] - H) // 2, (big.shape[1] - W) // 2
        big = big[y:y + H, x:x + W]
        blur = cv2.GaussianBlur(big, (0, 0), 1.6)
        big = cv2.addWeighted(big, 1.4, blur, -0.4, 0)  # gentle sharpen after upscaling
        enc.stdin.write(big.tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
print(dst, n, "frames")
