"""Original synthwave bed, generated from scratch (no samples, no licensing issues).

usage: python3 music.py SECONDS OUT.wav
100 BPM, Am - F - C - G. Intro is pads only, drums come in at ~27s (chapter 1),
everything drops back to pads for the end screen.
"""
import sys
import numpy as np, soundfile as sf

DUR = float(sys.argv[1]); OUT = sys.argv[2]
SR = 44100; BPM = 100; BEAT = 60 / BPM; BAR = BEAT * 4
N = int(DUR * SR); t = np.arange(N) / SR
rng = np.random.default_rng(7)

def note(m): return 440 * 2 ** ((m - 69) / 12)
def lowpass(x, cut):
    a = np.exp(-2 * np.pi * cut / SR); y = np.empty_like(x); acc = 0.0
    # vectorised one-pole via lfilter-style loop in chunks is slow; use scipy if present
    try:
        from scipy.signal import lfilter
        return lfilter([1 - a], [1, -a], x)
    except ImportError:
        for i, v in enumerate(x): acc = (1 - a) * v + a * acc; y[i] = acc
        return y
def saw(f, tt): return 2 * ((tt * f) % 1) - 1

CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]   # Am F C G
ROOTS = [45, 41, 36, 43]

pad = np.zeros(N); bass = np.zeros(N); arp = np.zeros(N)
nbars = int(DUR / BAR) + 1
for b in range(nbars):
    s0 = int(b * BAR * SR); s1 = min(N, int((b + 1) * BAR * SR))
    if s0 >= N: break
    tt = t[s0:s1] - b * BAR; ch = CHORDS[b % 4]
    env = np.minimum(1, tt / 0.6) * np.minimum(1, (BAR - tt) / 0.3)
    for m in ch:
        for det in (-0.08, 0.08):
            pad[s0:s1] += saw(note(m + 12) * (1 + det / 12), tt) * env * 0.08
    # bass: driving eighth notes
    for k in range(8):
        e0 = s0 + int(k * BEAT / 2 * SR); e1 = min(s1, e0 + int(BEAT / 2 * SR * 0.85))
        if e0 >= N: break
        te = t[e0:e1] - t[e0]
        bass[e0:e1] += saw(note(ROOTS[b % 4]), te) * np.exp(-te * 6) * 0.5
    # arp: sixteenths over the chord, an octave up
    for k in range(16):
        e0 = s0 + int(k * BEAT / 4 * SR); e1 = min(s1, e0 + int(BEAT / 4 * SR))
        if e0 >= N: break
        te = t[e0:e1] - t[e0]; m = ch[k % 3] + 24
        arp[e0:e1] += np.sign(np.sin(2 * np.pi * note(m) * te)) * np.exp(-te * 18) * 0.06

pad = lowpass(pad, 1800); bass = lowpass(bass, 420); arp = lowpass(arp, 3200)

kick = np.zeros(N); snare = np.zeros(N); hat = np.zeros(N)
nb = int(DUR / BEAT) + 1
for k in range(nb):
    s0 = int(k * BEAT * SR)
    if s0 >= N: break
    L = min(N - s0, int(0.35 * SR)); te = np.arange(L) / SR
    kick[s0:s0 + L] += np.sin(2 * np.pi * (45 + 90 * np.exp(-te * 30)) * te) * np.exp(-te * 9) * 0.9
    if k % 2 == 1:
        Ls = min(N - s0, int(0.3 * SR)); ts = np.arange(Ls) / SR
        snare[s0:s0 + Ls] += rng.standard_normal(Ls) * np.exp(-ts * 14) * 0.35 + np.sin(2 * np.pi * 190 * ts) * np.exp(-ts * 20) * 0.3
    for half in (0, 0.5):
        h0 = s0 + int(half * BEAT * SR); Lh = min(N - h0, int(0.05 * SR))
        if Lh > 0: hat[h0:h0 + Lh] += rng.standard_normal(Lh) * np.exp(-np.arange(Lh) / SR * 80) * (0.12 if half else 0.07)
hat = hat - lowpass(hat, 6000)
snare = lowpass(snare, 5000)
# cheap room: a few decaying echoes on the snare
room = snare.copy()
for d, gn in ((0.023, .5), (0.041, .35), (0.067, .25), (0.11, .15)):
    sh = int(d * SR); room[sh:] += snare[:-sh] * gn
snare = room

def ramp(a, b):   # 0 before a, fades to 1 at b
    return np.clip((t - a) / max(b - a, 1e-3), 0, 1)
drums_in = ramp(25.5, 27.5) * (1 - ramp(DUR - 19, DUR - 17))
arp_in = ramp(60, 64) * (1 - ramp(DUR - 19, DUR - 17))
mix = pad * 1.0 + bass * (0.35 + 0.65 * drums_in) + arp * arp_in + (kick + snare + hat) * drums_in * 0.8
mix *= np.minimum(1, t / 2.5) * np.minimum(1, (DUR - t) / 3)
st = np.stack([mix + np.roll(arp * arp_in, 300) * 0.3, mix + np.roll(pad, 220) * 0.15], 1)
st /= np.abs(st).max() * 1.12
sf.write(OUT, st.astype(np.float32), SR)
print("music", DUR, "s ->", OUT)
