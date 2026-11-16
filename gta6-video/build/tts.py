"""Voice the narration in script.md, one sentence at a time.

Writes build/out/vo/NNN.wav, build/out/vo.wav (full track with natural pauses)
and build/out/timing.json [{section, idx, text, start, end}].
"""
import json, os, re, sys
import numpy as np, soundfile as sf, sherpa_onnx

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("OUTDIR", f"{HERE}/out"); os.makedirs(f"{OUT}/vo", exist_ok=True)
SCRIPT = os.environ.get("SCRIPT", f"{HERE}/../script.md")
GAPK = float(os.environ.get("GAPK", 1.0))   # pause multiplier: <1 for punchy Shorts
K = "/tmp/claude-0/models/kokoro-int8-multi-lang-v1_0"
VOICE = int(os.environ.get("VOICE", 16))    # 16 = am_michael
SPEED = float(os.environ.get("SPEED", 1.0))

md = open(SCRIPT).read().split("\n---\n")[1]
sections = []
for block in re.split(r"\n## ", md)[1:]:
    title, *body = block.split("\n")
    paras = [p.strip() for p in "\n".join(body).split("\n\n")]
    paras = [" ".join(p.split()) for p in paras if p and not p.startswith("[")]
    sections.append((title.strip(), paras))

# --- pronunciation: spoken-text rewrites + extra dictionary entries ----------
SAY = [(r"\$79\.99", "seventy nine ninety nine"), (r"\bPS5\b", "P S five"), (r"\bGTA\b", "G T A"),
       (r"\bPC\b", "P C"), (r"\b2013\b", "twenty thirteen"), (r"\b2023\b", "twenty twenty three"),
       (r"\b2025\b", "twenty twenty five"), (r"\b2026\b", "twenty twenty six"), (r"\b19th\b", "nineteenth"),
       (r"\b26th\b", "twenty sixth"), (r"\b12th\b", "twelfth"), (r"\b6\b", "six"), (r"\b5\b", "five"),
       (r"\b2\b", "two")]
def spoken(s):
    for a, b in SAY: s = re.sub(a, b, s)
    return s
base = {}
for line in open(f"{K}/lexicon-us-en.txt", encoding="utf-8"):
    w, *ph = line.rstrip("\n").split(" ")
    base.setdefault(w, ph)
def P(*parts): return sum((base[x] if x in base else x.split() for x in parts), [])
EXTRA = {
  "rockstar": P("rock", "star"), "xbox": P("x", "box"), "grassrivers": P("grass", "river") + ["z"],
  "gellhorn": P("gel", "horn"), "leonida": "l ˌ i ə n ˈ i d ə".split(), "lucia": "l u s ˈ i ə".split(),
  "caminos": "k ə m ˈ i n O s".split(), "duval": "d u v ˈ æ l".split(), "bonnie": "b ˈ ɑ n i".split(),
  "andreas": "æ n d ɹ ˈ A ə s".split(), "kalaga": "k ə l ˈ ɑ ɡ ə".split(),
}
# regular plurals / past tenses the dictionary is missing
words = set(re.findall(r"[a-z']+", md.lower()))
for w in words:
    if w in base or w in EXTRA: continue
    if w.endswith("'s") and (w[:-2] in base or w[:-2] in EXTRA):
        stem = EXTRA.get(w[:-2]) or base[w[:-2]]; last = stem[-1]
        EXTRA[w] = stem + (["s"] if last in "ptkfθ" else ["z"]); continue
    if w.endswith("ies") and w[:-3] + "y" in base:
        EXTRA[w] = base[w[:-3] + "y"] + ["z"]; continue
    for suf, add in (("s", None), ("ed", None)):
        st = w[:-len(suf)]
        if w.endswith(suf) and st in base:
            last = base[st][-1]
            if suf == "s": add = "s" if last in "ptkfθ" else ("ᵻ z" if last in "szʃʒʧʤ" else "z")
            else: add = "ᵻ d" if last in "td" else ("t" if last in "pkfsʃʧθ" else "d")
            EXTRA[w] = base[st] + add.split(); break
LEX = f"{OUT}/lexicon.txt"
with open(LEX, "w", encoding="utf-8") as f:
    for w, ph in EXTRA.items(): f.write(w + " " + " ".join(ph) + "\n")
    f.write(open(f"{K}/lexicon-us-en.txt", encoding="utf-8").read())

tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
    kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(model=f"{K}/model.int8.onnx", voices=f"{K}/voices.bin",
                                                  tokens=f"{K}/tokens.txt", data_dir=f"{K}/espeak-ng-data",
                                                  lexicon=LEX, lang="en-us"),
    num_threads=4)))

SR = 24000
track, timing, t, n = [], [], 0.6, 0
track.append(np.zeros(int(0.6 * SR), np.float32))
for si, (title, paras) in enumerate(sections):
    for pi, p in enumerate(paras):
        sents = re.split(r"(?<=[.?!])\s+(?=[A-Z\"'])", p)
        for s in sents:
            a = tts.generate(spoken(s), sid=VOICE, speed=SPEED)
            x = np.array(a.samples, np.float32); SR = a.sample_rate
            # trim leading/trailing near-silence so pauses are ours
            nz = np.where(np.abs(x) > 0.01)[0]
            if len(nz): x = x[max(nz[0] - 600, 0): nz[-1] + 1200]
            sf.write(f"{OUT}/vo/{n:03d}.wav", x, SR)
            d = len(x) / SR
            timing.append({"section": si, "title": title, "idx": n, "text": s,
                           "start": round(t, 3), "end": round(t + d, 3)})
            track.append(x); t += d
            gap = 0.32 if s.endswith(",") else 0.42
            if s.endswith("?"): gap = 0.55
            gap *= GAPK
            track.append(np.zeros(int(gap * SR), np.float32)); t += gap
            n += 1; print(f"{t:6.1f}s  {s[:70]}", file=sys.stderr)
        track.append(np.zeros(int(0.35 * GAPK * SR), np.float32)); t += 0.35 * GAPK   # paragraph breath
    track.append(np.zeros(int(0.6 * GAPK * SR), np.float32)); t += 0.6 * GAPK   # section beat
track.append(np.zeros(int(2.0 * SR), np.float32)); t += 2.0
sf.write(f"{OUT}/vo.wav", np.concatenate(track), SR)
json.dump(timing, open(f"{OUT}/timing.json", "w"), indent=1)
print(f"total {t:.1f}s, {n} sentences", file=sys.stderr)
