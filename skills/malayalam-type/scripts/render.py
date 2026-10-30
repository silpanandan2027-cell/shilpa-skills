#!/usr/bin/env python3
"""Render a malayalam-type scene file to video, transparent overlay, or still frames.

  python render.py scenes.json out.mp4                 # video
  python render.py scenes.json out.mov --alpha         # transparent overlay (ProRes 4444)
  python render.py scenes.json out --still 1.0,3.5     # PNG check frames: out_1.00.png ...
  options: --fps 30  --size 1080x1920  --range 2.0,9.5   (render only this part of the timeline)
"""
import argparse, json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = HERE.parent / 'engine' / 'engine.html'


def launch(p):
    """Use the browser the person already has: Chrome, then Edge, then Playwright's own Chromium."""
    args = ['--allow-file-access-from-files', '--force-color-profile=srgb', '--font-render-hinting=none']
    for ch in ('chrome', 'msedge'):
        try:
            return p.chromium.launch(channel=ch, args=args)
        except Exception:
            pass
    return p.chromium.launch(args=args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scenes'); ap.add_argument('out')
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--size', default=None)
    ap.add_argument('--alpha', action='store_true')
    ap.add_argument('--still')
    ap.add_argument('--range')
    a = ap.parse_args()

    spec = json.load(open(a.scenes, encoding='utf-8'))
    size = a.size or spec.get('size', '1080x1920')
    w, h = (size if isinstance(size, list) else [int(x) for x in size.lower().split('x')])
    if a.alpha:
        spec['transparent'] = True
        spec.setdefault('theme', 'clear')

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={'width': w, 'height': h})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        pg.goto(ENGINE.as_uri())
        info = pg.evaluate('([s, z]) => mlInit(s, z)', [spec, [w, h]])
        if errs:
            sys.exit('Page error: ' + '; '.join(errs))
        t0, t1 = 0.0, info['duration']
        if a.range:
            t0, t1 = map(float, a.range.split(','))
        transparent = a.alpha or spec.get('theme') == 'clear'

        if a.still:
            for t in [float(x) for x in a.still.split(',')]:
                pg.evaluate('t => mlSeek(t)', t)
                pg.screenshot(path=f'{a.out}_{t:.2f}.png', omit_background=transparent)
            print('saved stills'); b.close(); return

        if a.alpha:
            codec = ['-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le']
        else:
            codec = ['-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
        n = max(1, int(round((t1 - t0) * a.fps)))
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'image2pipe', '-framerate', str(a.fps), '-i', '-'] + codec + [a.out],
                               stdin=subprocess.PIPE)
        for i in range(n):
            pg.evaluate('t => mlSeek(t)', t0 + i / a.fps)
            enc.stdin.write(pg.screenshot(type='png', omit_background=transparent))
            if i % 60 == 0:
                print(f'{i}/{n}', flush=True)
        enc.stdin.close(); enc.wait(); b.close()
    print('Done:', a.out)


if __name__ == '__main__':
    main()
