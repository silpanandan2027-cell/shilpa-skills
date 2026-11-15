"""Write the YouTube subtitle file (out/GTA6_explainer.en.srt) from the sentence timings."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(f"{HERE}/out/timing.json"))

def ts(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

cues = []
for s in T:
    words = s["text"].split(); chunks, cur = [], []
    for w in words:                       # chunks of at most ~42 chars, one line each
        if cur and len(" ".join(cur + [w])) > 42: chunks.append(cur); cur = []
        cur.append(w)
    if cur: chunks.append(cur)
    total = sum(len(" ".join(c)) for c in chunks); t = s["start"]
    for c in chunks:
        d = (s["end"] - s["start"]) * len(" ".join(c)) / total
        cues.append((t, t + d, " ".join(c))); t += d
with open(f"{HERE}/out/GTA6_explainer.en.srt", "w") as f:
    for i, (a, b, txt) in enumerate(cues, 1):
        f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n\n")
print(len(cues), "subtitle cues")
