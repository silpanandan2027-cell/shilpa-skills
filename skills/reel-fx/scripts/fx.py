#!/usr/bin/env python3
"""reel-fx: add effects and animated Malayalam text to a video.

  python fx.py plan.json input.mp4 output.mp4
  python fx.py plan.json input.mp4 check.png --still 2.5,6      # PNG check frames instead of a video
  python fx.py --list                                           # the effects

plan.json:  {"effects": [ {"fx": "punch", "start": 3, "end": 5, "zoom": 1.3}, ... ]}
Uses only the Python standard library and ffmpeg. Text effects are drawn by the malayalam-type skill.
"""
import argparse, json, os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
MT = HERE.parent.parent / 'malayalam-type'

LOOKS = {
    'warm':  'eq=saturation=1.15:contrast=1.05,colorbalance=rs=.08:gs=.02:bs=-.08:rm=.06:bm=-.06',
    'cool':  'eq=saturation=1.05,colorbalance=rs=-.06:bs=.08:rm=-.04:bm=.06',
    'mono':  'hue=s=0,eq=contrast=1.15',
    'film':  'eq=contrast=1.08:saturation=.9,curves=preset=medium_contrast,noise=alls=7:allf=t,vignette=PI/5',
    'moody': 'eq=brightness=-.05:contrast=1.15:saturation=.8,colorbalance=bs=.06:bh=.04,vignette=PI/4',
    'pop':   'eq=saturation=1.45:contrast=1.1',
    'fade':  'eq=contrast=.88:saturation=.8:brightness=.04',
}
EFFECTS = {
    'punch':    'Quick zoom in and back out. zoom (1.3), x, y (0..1 focus, default centre)',
    'shake':    'Camera shake. amount (0.012 of the width)',
    'grade':    'Colour look. look: ' + ', '.join(LOOKS),
    'vignette': 'Dark edges. strength (PI/4)',
    'flash':    'A white flash. at (seconds), dur (0.25)',
    'bars':     'Cinema black bars. size (0.1 of the height)',
    'progress': 'A thin bar across the top that fills. color (#FFD23F), height (0.008)',
    'text':     'Animated Malayalam text: any malayalam-type scene (kind, ml, en, ...), start, dur',
}


def esc(expr):
    return expr.replace(',', r'\,')


def probe(path):
    j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                   'stream=width,height:stream_side_data=rotation:format=duration', '-of', 'json', path],
                                  capture_output=True, text=True, check=True).stdout)
    s = j['streams'][0]; w, h = s['width'], s['height']
    rot = abs(int((s.get('side_data_list') or [{}])[0].get('rotation', 0)))
    if rot in (90, 270):
        w, h = h, w
    return w, h, float(j['format']['duration'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('args', nargs='*'); ap.add_argument('--still'); ap.add_argument('--list', action='store_true')
    ap.add_argument('--width', type=int, default=1080, help='short side of the output in pixels (default 1080)')
    ap.add_argument('--fps', type=int, default=30)
    a = ap.parse_args()
    if a.list:
        for k, v in EFFECTS.items():
            print(f'{k:9s} {v}')
        return
    plan_path, src, dst = a.args
    plan = json.load(open(plan_path, encoding='utf-8'))
    fxs = plan.get('effects', plan) if isinstance(plan, dict) else plan

    W0, H0, dur = probe(src)
    if W0 <= H0:
        W = a.width; H = int(round(H0 * W / W0 / 2)) * 2
    else:
        H = a.width; W = int(round(W0 * H / H0 / 2)) * 2
    W -= W % 2

    chain, state = [], {'n': 0, 'cur': 'v0'}
    chain.append(f'[0:v]scale={W}:{H},setsar=1,fps={a.fps}[v0]')

    def nxt():
        state['n'] += 1
        return f'v{state["n"]}'

    def apply(f):                       # whole-video filter
        o = nxt(); chain.append(f'[{state["cur"]}]{f}[{o}]'); state['cur'] = o

    def window(f, s, e):                # filter that only shows between s and e
        n = state['n'] + 1; state['n'] = n
        a_, b_, c_, o = f'w{n}a', f'w{n}b', f'w{n}c', f'v{n}'
        chain.append(f'[{state["cur"]}]split[{a_}][{b_}]')
        chain.append(f'[{b_}]{f}[{c_}]')
        chain.append(f'[{a_}][{c_}]overlay=enable=\'between(t,{s},{e})\'[{o}]'); state['cur'] = o

    texts = []
    for d in fxs:
        k = d['fx'].lower().lstrip('/')
        s = float(d.get('start', d.get('at', 0)))
        e = float(d['end']) if 'end' in d else (s + float(d['dur']) if 'dur' in d else dur)
        e = min(e, dur)
        if k == 'text':
            sc = {x: v for x, v in d.items() if x not in ('fx', 'start', 'end')}
            sc['at'] = s; sc['dur'] = round(e - s, 3) if 'dur' not in d else float(d['dur'])
            if 'words_file' in sc:
                sc['words'] = json.load(open(sc.pop('words_file'), encoding='utf-8'))
            texts.append(sc)
        elif k == 'grade':
            f = LOOKS.get(d.get('look', 'warm'))
            if not f:
                sys.exit(f"Unknown look '{d.get('look')}'. Looks: {', '.join(LOOKS)}")
            apply(f) if s <= 0 and e >= dur - 0.05 else window(f, s, e)
        elif k == 'vignette':
            f = f"vignette={d.get('strength', 'PI/4')}"
            apply(f) if s <= 0 and e >= dur - 0.05 else window(f, s, e)
        elif k == 'punch':
            z = float(d.get('zoom', 1.3)); zin = 0.22; zout = 0.3
            ramp = f'max(0,min(1,min((t-{s})/{zin},({e}-t)/{zout})))'
            zexp = esc(f'1+({z}-1)*{ramp}')
            fx_, fy_ = float(d.get('x', 0.5)), float(d.get('y', 0.5))
            apply(f"scale=w='trunc(iw*({zexp})/2)*2':h='trunc(ih*({zexp})/2)*2':eval=frame,"
                  f"crop={W}:{H}:x='(in_w-out_w)*{fx_}':y='(in_h-out_h)*{fy_}'")
        elif k == 'shake':
            amp = float(d.get('amount', 0.012)) * W
            window(f"scale=iw*1.08:ih*1.08,crop={W}:{H}:x='(in_w-out_w)/2+{amp:.1f}*sin(t*63)':y='(in_h-out_h)/2+{amp:.1f}*cos(t*51)'", s, e)
        elif k == 'flash':
            at = float(d.get('at', s)); fd = float(d.get('dur', 0.25))
            apply(esc(f"eq=brightness='0.75*max(0,1-(t-{at})/{fd})*between(t,{at},{at + fd})'") + ':eval=frame')
        elif k == 'bars':
            sz = float(d.get('size', 0.1))
            apply(f"drawbox=x=0:y=0:w=iw:h=ih*{sz}:color=black:t=fill:enable='between(t,{s},{e})',"
                  f"drawbox=x=0:y=ih-ih*{sz}:w=iw:h=ih*{sz}:color=black:t=fill:enable='between(t,{s},{e})'")
        elif k == 'progress':
            col = d.get('color', '#FFD23F').lstrip('#'); ht = max(2, int(H * float(d.get('height', 0.008))) // 2 * 2)
            chain.append(f'color=c=0x{col}:s={W}x{ht}:r={a.fps}[pb{state["n"]}]')
            o = nxt()
            ex = esc(f"-w+w*min(1,max(0,(t-{s})/({e}-{s})))")
            chain.append(f"[{state['cur']}][pb{state['n'] - 1}]overlay=x='{ex}':y=0:enable='between(t,{s},{e})':shortest=0[{o}]")
            state['cur'] = o
        else:
            sys.exit(f"Unknown effect '{k}'. Run with --list.")

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='reelfx_'))
    spec_path = None
    if texts:
        py = MT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        if not py.exists():
            sys.exit(f'NEED_MALAYALAM_TYPE: run  python "{MT / "scripts" / "setup.py"}"  first (the text skill is not set up yet).')
        spec = {'size': f'{W}x{H}', 'theme': plan.get('theme', 'clear') if isinstance(plan, dict) else 'clear', 'scenes': texts}
        if isinstance(plan, dict) and plan.get('colors'):
            spec['colors'] = plan['colors']
        spec_path = tmp / 'text.json'
        spec_path.write_text(json.dumps(spec, ensure_ascii=False), encoding='utf-8')

    def run(times=None, out=None):
        """Build the graph (adding the text overlay for the range wanted) and run ffmpeg."""
        g, cur, extra = list(chain), state['cur'], []
        if texts:
            t0, t1 = (times[0], times[0] + 0.1) if times else (min(x['at'] for x in texts), max(x['at'] + x['dur'] for x in texts))
            mov = tmp / f'text_{t0:.2f}.mov'
            subprocess.run([str(py), str(MT / 'scripts' / 'render.py'), str(spec_path), str(mov), '--alpha',
                            '--fps', str(a.fps), '--range', f'{t0},{t1}'], check=True, stdout=subprocess.DEVNULL)
            extra = ['-i', str(mov)]
            g.append(f'[1:v]format=yuva444p10le,setpts=PTS+{t0}/TB[tx]')
            g.append(f"[{cur}][tx]overlay=enable='between(t,{t0},{t1})':eof_action=pass:format=auto[vt]"); cur = 'vt'
        if times:
            g.append(f'[{cur}]trim=start={times[0]}:end={times[0] + 0.1},setpts=PTS-STARTPTS[vsel]'); cur = 'vsel'
        script = tmp / 'graph.txt'
        fmt = 'rgb24' if times else 'yuv420p'
        script.write_text(';\n'.join(g) + f';\n[{cur}]format={fmt}[vout]', encoding='utf-8')
        pre = ['-t', f'{times[0] + 0.3:.2f}'] if times else []
        cmd = ['ffmpeg', '-v', 'error', '-y'] + pre + ['-i', src] + extra + ['-/filter_complex', str(script), '-map', '[vout]']
        if times:
            cmd += ['-frames:v', '1', out]
        else:
            cmd += ['-map', '0:a?', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-c:a', 'aac', '-b:a', '192k',
                    '-movflags', '+faststart', '-shortest', out]
        subprocess.run(cmd, check=True)

    if a.still:
        ts = [float(x) for x in a.still.split(',')]
        for t in ts:
            out = (dst[:-4] if dst.endswith('.png') else dst) + f'_{t:.2f}.png'
            run([t], out); print('saved', out)
    else:
        run(None, dst); print('Done:', dst)


if __name__ == '__main__':
    main()
