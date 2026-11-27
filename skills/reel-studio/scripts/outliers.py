#!/usr/bin/env python3
"""Find the short videos that beat their own account: the ones worth copying the idea of.

  python outliers.py https://www.youtube.com/@someone/shorts https://www.tiktok.com/@other --last 40
  python outliers.py --csv reels.csv          (columns: account,url,views[,caption])  for Instagram, pasted by hand
  options: --min 3   (only keep videos with at least 3x the account's usual views)   --cookies cookies.txt

A video's "outlier score" is its views divided by the median views of that account's recent videos.
A 10x video on a 2,000-view account says more about the idea than a 1M video on a 5M-view account.
Writes swipe.csv and swipe.md into the current folder. Needs yt-dlp for links.
"""
import argparse, csv, json, shutil, statistics, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def fetch(url, last, cookies):
    exe = shutil.which('yt-dlp')
    cmd = ([exe] if exe else [sys.executable, '-m', 'yt_dlp']) + ['--flat-playlist', '-J', '--playlist-end', str(last), '--no-warnings']
    if cookies:
        cmd += ['--cookies', cookies]
    r = subprocess.run(cmd + [url], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        print(f'Could not read {url}: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "unknown error"}')
        return []
    d = json.loads(r.stdout)
    acct = d.get('uploader') or d.get('channel') or d.get('title') or url
    out = []
    for e in d.get('entries') or []:
        if e and e.get('view_count'):
            out.append({'account': acct, 'url': e.get('url') or e.get('webpage_url') or '', 'views': int(e['view_count']),
                        'caption': (e.get('title') or e.get('description') or '').replace('\n', ' ')[:140]})
    print(f'{acct}: {len(out)} videos')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('urls', nargs='*'); ap.add_argument('--csv'); ap.add_argument('--last', type=int, default=40)
    ap.add_argument('--min', type=float, default=2.0); ap.add_argument('--cookies')
    a = ap.parse_args()
    rows = []
    for u in a.urls:
        rows += fetch(u, a.last, a.cookies)
    if a.csv:
        for r in csv.DictReader(open(a.csv, encoding='utf-8-sig')):
            v = str(r.get('views', '')).replace(',', '').strip().upper()
            mult = 1_000_000 if v.endswith('M') else 1_000 if v.endswith('K') else 1
            try:
                views = int(float(v.rstrip('MK')) * mult)
            except ValueError:
                continue
            rows.append({'account': r.get('account', '?'), 'url': r.get('url', ''), 'views': views, 'caption': r.get('caption', '')})
    if not rows:
        sys.exit('No videos found. Give channel/profile links or a --csv file.')

    by = {}
    for r in rows:
        by.setdefault(r['account'], []).append(r)
    for acct, rs in by.items():
        med = statistics.median(x['views'] for x in rs) or 1
        for x in rs:
            x['median'] = int(med); x['score'] = round(x['views'] / med, 1)
    rows.sort(key=lambda x: x['score'], reverse=True)
    keep = [r for r in rows if r['score'] >= a.min] or rows[:10]

    with open('swipe.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=['score', 'views', 'median', 'account', 'caption', 'url'])
        w.writeheader(); [w.writerow({k: r[k] for k in w.fieldnames}) for r in keep]
    with open('swipe.md', 'w', encoding='utf-8') as f:
        f.write('# Swipe file\n\n| Score | Views | Account | Caption / hook | Link |\n|---|---|---|---|---|\n')
        for r in keep:
            f.write(f"| {r['score']}x | {r['views']:,} | {r['account']} | {r['caption'].replace('|', '/')} | {r['url']} |\n")
    for r in keep[:15]:
        print(f"{r['score']:6.1f}x  {r['views']:>10,}  {r['account'][:18]:18}  {r['caption'][:70]}")
    print(f'\n{len(keep)} outliers saved to swipe.csv and swipe.md')


if __name__ == '__main__':
    main()
