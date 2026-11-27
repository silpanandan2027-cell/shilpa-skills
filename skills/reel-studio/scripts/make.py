#!/usr/bin/env python3
"""Turn a reel script (reel.json) into a finished, posted-ready reel: voiceover, styled visuals, captions, music, cover.

  python make.py reel.json                       -> reel.mp4 + reel_cover.jpg next to reel.json
  python make.py reel.json --still 1,4.5         -> check frames reel_1.00.png ... (fast, no render)
  python make.py reel.json --carousel            -> slides reel_slide01.png ... (1080x1350, no voice)
  python make.py --styles                        -> list the styles
  options: --out file.mp4   --fps 30   --no-voice

reel.json:
  {"style": "bold", "voice": "ml-IN-SobhanaNeural", "rate": "+5%", "brand": {"handle": "@you"},
   "music": "song.mp3", "music_volume": 0.12, "over": "my_talking_clip.mp4", "words_file": "clip.words.json",
   "beats": [{"type": "hook", "text": "Stop *posting* daily", "say": "Stop posting every day."}, ...]}
"""
import argparse, asyncio, json, os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = HERE.parent / 'engine' / 'studio.html'
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

STYLES = {
    'bold': 'Black, white type, yellow highlight. The default faceless reel.',
    'clean': 'Light SaaS look: white cards, blue accent. Good for product tips.',
    'editorial': 'Cream paper, serif type, red accent. Stories and opinions.',
    'news': 'News desk: navy, red BREAKING label, white ticker captions.',
    'neon': 'Dark purple with pink and cyan glow. Tech, AI, hype.',
    'brutalist': 'White, thick black borders, orange, mono type. Bold takes.',
    'retro': '80s sunset gradient, rounded type, stacked shadow. Fun, nostalgic.',
    'ledger': 'Money green grid, mint numbers. Revenue, pricing, finance.',
    'terminal': 'Black and green mono, typing effect. Dev tools, code.',
    'paper': 'Warm cream and orange, Malayalam display type. Friendly explainers.',
    'comic': 'Yellow halftone, outlined panels, slam-in text. Playful.',
    'minimal': 'Soft lavender gradient, quiet purple accent. Calm, premium.',
}


def probe_dur(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


async def tts(text, voice, rate, out_mp3):
    """Free neural voice (Microsoft Edge read-aloud voices). Returns word timings in seconds."""
    import edge_tts
    if os.environ.get('SSL_CERT_FILE'):   # behind a company or cloud proxy with its own certificate
        import ssl, edge_tts.communicate as c
        c._SSL_CTX = ssl.create_default_context(cafile=os.environ['SSL_CERT_FILE'])
    try:
        com = edge_tts.Communicate(text, voice, rate=rate, boundary='WordBoundary')
    except TypeError:
        com = edge_tts.Communicate(text, voice, rate=rate)
    words, sents = [], []
    with open(out_mp3, 'wb') as f:
        async for ch in com.stream():
            if ch['type'] == 'audio':
                f.write(ch['data'])
            elif ch['type'] in ('WordBoundary', 'SentenceBoundary'):
                item = {'t': ch['offset'] / 1e7, 'e': (ch['offset'] + ch['duration']) / 1e7, 'w': ch['text']}
                (words if ch['type'] == 'WordBoundary' else sents).append(item)
    if not words:   # only sentence times came back: spread each sentence's words by their length
        for s in sents:
            ws = s['w'].split(); total = sum(len(w) for w in ws) or 1; t = s['t']
            for w in ws:
                d = (s['e'] - s['t']) * len(w) / total
                words.append({'t': t, 'e': t + d, 'w': w}); t += d
    return words


def build_timeline(spec, base, tmp, use_voice):
    """Give every beat a start and length. Voiced beats last as long as their line, plus a breath."""
    voice = spec.get('voice', 'en-US-AndrewNeural')
    if str(voice).lower() in ('none', 'off', ''):
        use_voice = False
    rate = spec.get('rate', '+0%')
    clips, t = [], float(spec.get('lead', 0))
    over_words = []
    if spec.get('words_file'):
        over_words = json.load(open(base / spec['words_file'], encoding='utf-8'))
    for i, b in enumerate(spec['beats']):
        if spec.get('over') and b.get('at') is not None:
            t = float(b['at'])
        b['at'] = round(t, 3)
        say = b.get('say')
        if use_voice and say:
            mp3 = tmp / f'beat{i:02d}.mp3'
            print(f'Voice {i + 1}/{len(spec["beats"])}: {say[:60]}', flush=True)
            ws = asyncio.run(tts(say, voice, rate, mp3))
            d = probe_dur(mp3)
            b['words'] = [{'t': round(t + w['t'], 3), 'e': round(t + w['e'], 3), 'w': w['w']} for w in ws]
            clips.append((t, mp3))
            b['dur'] = round(max(float(b.get('dur', 0)), d + float(b.get('pad', 0.3))), 3)
        else:
            b['dur'] = float(b.get('dur', 2.6 if b.get('type') != 'cta' else 3))
            if over_words:
                b['words'] = [w for w in over_words if t <= w['t'] < t + b['dur']]
        if b.get('type') == 'hook' and b.get('cap') is None and say and \
                ''.join(say.split()).lower().strip('.!?') == ''.join(str(b.get('text', '')).replace('*', '').split()).lower().strip('.!?'):
            b['cap'] = False     # the hook already shows the same words big
        t = b['at'] + b['dur']
    total = t + float(spec.get('tail', 0.2))
    if spec.get('over'):
        total = max(total, 0) if not spec.get('fit_footage', True) else probe_dur(base / spec['over'])
    spec['duration'] = round(total, 3)
    return clips


def mix_audio(spec, base, clips, tmp):
    """Voice lines at their beat times, music underneath (ducked low), loudness set for Instagram (-14 LUFS)."""
    total = spec['duration']
    ins, parts = [], []
    if spec.get('over'):
        ins += ['-i', str(base / spec['over'])]; parts.append('[0:a]volume=1[s0]')
    for t, mp3 in clips:
        k = len(ins) // 2
        ins += ['-i', str(mp3)]; ms = int(t * 1000)
        parts.append(f'[{k}:a]adelay={ms}|{ms},aresample=48000[s{k}]')
    if spec.get('music'):
        k = len(ins) // 2
        ins += ['-stream_loop', '-1', '-i', str(base / spec['music'])]
        vol = float(spec.get('music_volume', 0.12 if (clips or spec.get('over')) else 0.8))
        parts.append(f'[{k}:a]volume={vol},atrim=0:{total},afade=t=out:st={max(0, total - 1.2)}:d=1.2,aresample=48000[s{k}]')
    n = len(ins) // 2
    out = tmp / 'mix.wav'
    if n == 0:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'anullsrc=r=48000:cl=stereo', '-t', str(total), str(out)], check=True)
        return out
    labels = ''.join(f'[s{i}]' for i in range(n))
    graph = ';'.join(parts) + f';{labels}amix=inputs={n}:normalize=0:duration=longest,apad,atrim=0:{total},loudnorm=I=-14:TP=-1.5:LRA=11[a]'
    has_audio = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0',
                                str(base / spec['over'])], capture_output=True, text=True).stdout.strip() if spec.get('over') else '1'
    if spec.get('over') and not has_audio:
        ins = ins[2:]; parts = parts[1:]
        parts = [p.replace(f'[{i}:a]', f'[{i - 1}:a]').replace(f'[s{i}]', f'[s{i - 1}]') for i, p in enumerate(parts, 1)]
        n -= 1
        if n == 0:
            spec_over = dict(spec); spec_over.pop('over'); return mix_audio(spec_over, base, [], tmp)
        labels = ''.join(f'[s{i}]' for i in range(n))
        graph = ';'.join(parts) + f';{labels}amix=inputs={n}:normalize=0:duration=longest,apad,atrim=0:{total},loudnorm=I=-14:TP=-1.5:LRA=11[a]'
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + ins + ['-filter_complex', graph, '-map', '[a]', '-ar', '48000', '-ac', '2', str(out)], check=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('reel', nargs='?'); ap.add_argument('--out'); ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--still'); ap.add_argument('--carousel', action='store_true'); ap.add_argument('--no-voice', action='store_true')
    ap.add_argument('--styles', action='store_true')
    a = ap.parse_args()
    if a.styles or not a.reel:
        for k, v in STYLES.items():
            print(f'{k:10} {v}')
        return

    src = pathlib.Path(a.reel).resolve(); base = src.parent
    spec = json.load(open(src, encoding='utf-8'))
    for b in spec['beats']:
        if b.get('type') == 'image' and b.get('src') and '://' not in b['src']:
            b['src'] = (base / b['src']).resolve().as_uri()
    carousel = a.carousel or spec.get('format') == 'carousel'
    w, h = (1080, 1350) if carousel else (1080, 1920)
    stem = src.with_suffix('')
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='reelstudio_'))

    if carousel:
        spec['format'] = 'carousel'; spec['captions'] = False; spec.pop('over', None)
        for i, b in enumerate(spec['beats']):
            b['at'], b['dur'] = i * 4.0, 4.0
        clips = []
    else:
        clips = build_timeline(spec, base, tmp, use_voice=not (a.no_voice or a.still))
    over = spec.get('over')
    render_spec = dict(spec); render_spec['over'] = bool(over)

    from playwright.sync_api import sync_playwright
    from browser import launch
    with sync_playwright() as p:
        br = launch(p)
        pg = br.new_page(viewport={'width': w, 'height': h})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(ENGINE.as_uri())
        info = pg.evaluate('([s, z]) => studioInit(s, z)', [render_spec, [w, h]])
        if errs:
            sys.exit('Page error: ' + '; '.join(errs))
        dur = info['duration']

        if carousel:
            for i, b in enumerate(spec['beats']):
                pg.evaluate('t => studioSeek(t)', b['at'] + 3.9)
                path = f'{stem}_slide{i + 1:02d}.png'; pg.screenshot(path=path); print('Saved', path)
            br.close(); return

        if a.still:
            for t in [float(x) for x in a.still.split(',')]:
                pg.evaluate('t => studioSeek(t)', t)
                path = f'{stem}_{t:.2f}.png'; pg.screenshot(path=path, omit_background=bool(over)); print('Saved', path)
            print('Beats:', ', '.join(f"{b['type']} {b['at']:.1f}s" for b in info['beats']), f'| total {dur:.1f}s')
            br.close(); return

        audio = mix_audio(spec, base, clips, tmp)
        out = pathlib.Path(a.out) if a.out else stem.with_suffix('.mp4')
        n = max(1, int(round(dur * a.fps)))
        enc_out = ['-map', '[v]', '-map', f'{2 if over else 1}:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                   '-pix_fmt', 'yuv420p', '-r', str(a.fps), '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', str(dur), str(out)]
        if over:
            fg = (f'[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={a.fps},setsar=1[bg];'
                  f'[1:v]format=rgba[ov];[bg][ov]overlay=0:0:shortest=0:eof_action=pass,format=yuv420p[v]')
            cmd = ['ffmpeg', '-v', 'error', '-y', '-i', str(base / over), '-f', 'image2pipe', '-framerate', str(a.fps), '-i', '-',
                   '-i', str(audio), '-filter_complex', fg] + enc_out
        else:
            cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'image2pipe', '-framerate', str(a.fps), '-i', '-', '-i', str(audio),
                   '-filter_complex', '[0:v]format=yuv420p[v]'] + enc_out
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n):
            pg.evaluate('t => studioSeek(t)', i / a.fps)
            frame = pg.screenshot(type='png', omit_background=True) if over else pg.screenshot(type='jpeg', quality=94)
            enc.stdin.write(frame)
            if i % 90 == 0:
                print(f'frame {i}/{n}', flush=True)
        enc.stdin.close(); enc.wait()
        if enc.returncode:
            sys.exit('ffmpeg failed while encoding')
        hook_t = min(dur - 0.05, (spec['beats'][0]['at'] + min(1.2, spec['beats'][0]['dur'] * 0.7)))
        pg.evaluate('t => studioSeek(t)', hook_t)
        cover = f'{stem}_cover.jpg'
        if over:
            png = tmp / 'cover.png'; pg.screenshot(path=str(png), omit_background=True)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(hook_t), '-i', str(base / over), '-i', str(png), '-filter_complex',
                            f'[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}[b];[b][1:v]overlay', '-frames:v', '1', cover], check=True)
        else:
            pg.screenshot(path=cover, type='jpeg', quality=92)
        br.close()
    json.dump(spec, open(f'{stem}.timed.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'Done: {out} ({dur:.1f}s)  cover: {cover}')


if __name__ == '__main__':
    main()
