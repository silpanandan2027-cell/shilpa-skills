#!/usr/bin/env python3
"""Check a reel before it goes out: the technical things Instagram punishes, measured with ffmpeg.

  python check.py reel.mp4            -> a report, plus reel.check.json
Needs only Python and ffmpeg. The content score (hook, retention, payoff, ask) is done by Claude
with references/score.md; this script covers what can be measured.
"""
import json, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    info = json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', src]).stdout or '{}')
    if not info.get('streams'):
        sys.exit(f'Could not read {src}')
    v = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
    a = next((s for s in info['streams'] if s['codec_type'] == 'audio'), None)
    dur = float(info['format'].get('duration', 0))
    size_mb = int(info['format'].get('size', 0)) / 1e6
    res = []   # (status, check, detail)  status: ok / warn / fail

    def add(st, name, detail):
        res.append({'status': st, 'check': name, 'detail': detail})

    w, h = int(v['width']), int(v['height'])
    rot = next((sd.get('rotation') for sd in v.get('side_data_list', []) if 'rotation' in sd), 0) or 0
    if abs(int(rot)) in (90, 270):
        w, h = h, w
    ratio = w / h
    add('ok' if abs(ratio - 9 / 16) < 0.02 else 'fail', 'Shape 9:16', f'{w}x{h}' + ('' if abs(ratio - 9 / 16) < 0.02 else ' - Reels need vertical 9:16 or they get bars'))
    add('ok' if w >= 1080 else ('warn' if w >= 720 else 'fail'), 'Sharpness', f'{w} px wide' + ('' if w >= 1080 else ' - export at 1080x1920'))
    fps = eval(v.get('avg_frame_rate', '0/1').replace('/0', '/1')) if v.get('avg_frame_rate') else 0
    add('ok' if 23 <= fps <= 60 else 'warn', 'Frame rate', f'{fps:.0f} fps')
    if dur < 3:
        add('fail', 'Length', f'{dur:.1f}s - Instagram needs at least 3 seconds')
    elif dur > 90:
        add('warn', 'Length', f'{dur:.0f}s - over 90s is allowed but rarely watched to the end; aim for 15-45s')
    else:
        add('ok', 'Length', f'{dur:.1f}s' + (' (sweet spot)' if 7 <= dur <= 45 else ''))
    add('ok' if size_mb < 300 else 'fail', 'File size', f'{size_mb:.0f} MB' + ('' if size_mb < 300 else ' - the upload limit is 300 MB'))
    vc = v.get('codec_name')
    add('ok' if vc in ('h264', 'hevc') else 'warn', 'Video codec', vc + ('' if vc in ('h264', 'hevc') else ' - re-export as H.264'))

    if not a:
        add('warn', 'Sound', 'no audio track - reels with sound or trending audio reach more people')
    else:
        lo = run(['ffmpeg', '-hide_banner', '-nostats', '-i', src, '-map', '0:a:0', '-af', 'ebur128', '-f', 'null', '-']).stderr
        m = re.findall(r'I:\s+(-?[\d.]+) LUFS', lo)
        if m:
            lufs = float(m[-1])
            st = 'ok' if -17 <= lufs <= -11 else 'warn'
            add(st, 'Loudness', f'{lufs:.1f} LUFS' + ('' if st == 'ok' else ' - aim for about -14 (too quiet loses people, too loud distorts)'))
        sil = run(['ffmpeg', '-hide_banner', '-nostats', '-t', '3', '-i', src, '-map', '0:a:0', '-af', 'silencedetect=n=-40dB:d=0.6', '-f', 'null', '-']).stderr
        starts = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', sil)]
        if starts and starts[0] <= 0.3:
            end = re.findall(r'silence_end: ([\d.]+)', sil)
            add('warn', 'Opening sound', f'silent for the first {float(end[0]) if end else 3:.1f}s - start talking on frame one')
        else:
            add('ok', 'Opening sound', 'sound starts right away')

    blk = run(['ffmpeg', '-hide_banner', '-nostats', '-t', '2', '-i', src, '-vf', 'blackdetect=d=0.3:pix_th=0.08:pic_th=0.995', '-an', '-f', 'null', '-']).stderr
    bs = re.findall(r'black_start:([\d.]+)', blk)
    add('warn' if bs and float(bs[0]) < 0.2 else 'ok', 'First frame', 'opens on black - the first frame must show the hook' if bs and float(bs[0]) < 0.2 else 'opens on a picture')
    sc = run(['ffmpeg', '-hide_banner', '-nostats', '-i', src, '-vf', "scale=270:-2,select='gt(scene,0.04)',showinfo", '-an', '-f', 'null', '-']).stderr
    cuts = len(re.findall(r'pts_time:', sc))
    every = dur / (cuts + 1)
    add('ok' if every <= 3.5 else 'warn', 'Pace', f'a visual change about every {every:.1f}s' + ('' if every <= 3.5 else ' - add a cut, zoom or text change every 2-3s'))

    icon = {'ok': 'OK  ', 'warn': 'WARN', 'fail': 'FIX '}
    for r in res:
        print(f"{icon[r['status']]}  {r['check']:14} {r['detail']}")
    fails = sum(r['status'] == 'fail' for r in res); warns = sum(r['status'] == 'warn' for r in res)
    tech = max(0, 100 - 25 * fails - 8 * warns)
    print(f'\nTechnical score: {tech}/100  ({fails} to fix, {warns} warnings)')
    out = src.rsplit('.', 1)[0] + '.check.json'
    json.dump({'file': src, 'duration': dur, 'technical_score': tech, 'checks': res}, open(out, 'w', encoding='utf-8'), indent=1)


if __name__ == '__main__':
    main()
