#!/usr/bin/env python3
"""Post, schedule and measure reels on your own Instagram account, through Instagram's official API.

  python ig.py whoami                                  check the token works, show the account
  python ig.py post reel.mp4 --caption-file cap.txt    upload and publish a reel now
  python ig.py schedule reel.mp4 "2026-12-01 19:30" --caption-file cap.txt
  python ig.py queue                                   list scheduled posts
  python ig.py unschedule <n>                          remove item n from the queue
  python ig.py publish-due                             post everything whose time has come (run this from a timer)
  python ig.py stats [--limit 50]                      pull views, reach, saves, shares... into results.csv
  python ig.py refresh                                 renew the token (it lasts 60 days; renew monthly)

Settings live in the studio folder (default ~/reel-studio, or set REEL_STUDIO):
  .env           IG_ACCESS_TOKEN=...   (never share this file)
  queue.json     scheduled posts
  results.csv    stats, one row per post
Needs only Python. Uses the "Instagram API with Instagram Login" (graph.instagram.com) and a
Professional (Business or Creator) account. See references/instagram-setup.md to get a token.
"""
import argparse, csv, datetime as dt, json, os, pathlib, sys, time, urllib.error, urllib.parse, urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
API = 'https://graph.instagram.com/v23.0'
UPLOAD = 'https://rupload.facebook.com/ig-api-upload/v23.0'
HOME = pathlib.Path(os.environ.get('REEL_STUDIO', pathlib.Path.home() / 'reel-studio')).expanduser()


def token():
    t = os.environ.get('IG_ACCESS_TOKEN')
    env = HOME / '.env'
    if not t and env.exists():
        for line in env.read_text(encoding='utf-8').splitlines():
            if line.strip().startswith('IG_ACCESS_TOKEN='):
                t = line.split('=', 1)[1].strip().strip('"\'')
    if not t:
        sys.exit(f'NEED_TOKEN: put IG_ACCESS_TOKEN=... in {env} (see references/instagram-setup.md)')
    return t


def call(method, url, params=None, data=None, headers=None):
    params = dict(params or {})
    if 'rupload' not in url:
        params['access_token'] = token()
    full = url + ('?' + urllib.parse.urlencode(params) if params and method == 'GET' else '')
    body = data if data is not None else (urllib.parse.urlencode(params).encode() if method == 'POST' else None)
    req = urllib.request.Request(full, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        msg = e.read().decode('utf-8', 'replace')
        try:
            err = json.loads(msg).get('error', {}); msg = f"{err.get('message')} (code {err.get('code')})"
        except Exception:
            pass
        raise SystemExit(f'Instagram said: {msg}')


def me():
    return call('GET', f'{API}/me', {'fields': 'user_id,username,account_type,followers_count,media_count'})


def publish(video, caption, share_to_feed=True, thumb_ms=None):
    video = pathlib.Path(video)
    uid = me()['user_id']
    params = {'media_type': 'REELS', 'upload_type': 'resumable', 'caption': caption, 'share_to_feed': 'true' if share_to_feed else 'false'}
    if thumb_ms is not None:
        params['thumb_offset'] = str(int(thumb_ms))
    cont = call('POST', f'{API}/{uid}/media', params)
    cid = cont['id']
    size = video.stat().st_size
    print(f'Uploading {video.name} ({size / 1e6:.1f} MB)...', flush=True)
    call('POST', cont.get('uri') or f'{UPLOAD}/{cid}', data=video.read_bytes(),
         headers={'Authorization': f'OAuth {token()}', 'offset': '0', 'file_size': str(size)})
    for _ in range(120):   # Instagram processes the video; usually under a minute
        st = call('GET', f'{API}/{cid}', {'fields': 'status_code,status'})
        if st.get('status_code') == 'FINISHED':
            break
        if st.get('status_code') in ('ERROR', 'EXPIRED'):
            raise SystemExit(f"Instagram could not process the video: {st.get('status')}")
        time.sleep(5)
    else:
        raise SystemExit('Instagram is still processing after 10 minutes; try publish-due later')
    pub = call('POST', f'{API}/{uid}/media_publish', {'creation_id': cid})
    link = call('GET', f"{API}/{pub['id']}", {'fields': 'permalink'}).get('permalink', '')
    print(f"Posted: {link or pub['id']}")
    return pub['id'], link


def read_caption(a):
    if getattr(a, 'caption_file', None):
        return pathlib.Path(a.caption_file).read_text(encoding='utf-8').strip()
    return a.caption or ''


def qload():
    q = HOME / 'queue.json'
    return json.loads(q.read_text(encoding='utf-8')) if q.exists() else []


def qsave(items):
    HOME.mkdir(parents=True, exist_ok=True)
    (HOME / 'queue.json').write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding='utf-8')


METRICS = ['views', 'reach', 'likes', 'comments', 'shares', 'saved', 'total_interactions',
           'ig_reels_avg_watch_time', 'ig_reels_video_view_total_time', 'follows', 'profile_visits']


def insights(mid, kind):
    want = list(METRICS) if kind == 'REELS' else ['views', 'reach', 'likes', 'comments', 'shares', 'saved', 'total_interactions']
    out = {}
    while want:
        try:
            r = call('GET', f'{API}/{mid}/insights', {'metric': ','.join(want)})
            for m in r.get('data', []):
                vals = m.get('values') or [{}]
                out[m['name']] = vals[0].get('value', m.get('total_value', {}).get('value'))
            break
        except SystemExit as e:   # a metric this post does not support: drop it and ask again
            bad = next((m for m in want if m in str(e)), None)
            if not bad:
                break
            want.remove(bad)
    return out


def stats(limit):
    acct = me()
    uid = acct['user_id']
    r = call('GET', f'{API}/{uid}/media', {'fields': 'id,caption,media_type,media_product_type,permalink,timestamp,like_count,comments_count', 'limit': min(limit, 100)})
    rows = []
    for m in r.get('data', [])[:limit]:
        kind = m.get('media_product_type') or m.get('media_type')
        ins = insights(m['id'], kind)
        rows.append({'date': m['timestamp'][:10], 'type': kind, 'hook': (m.get('caption') or '').split('\n')[0][:90],
                     'views': ins.get('views', ''), 'reach': ins.get('reach', ''), 'likes': ins.get('likes', m.get('like_count', '')),
                     'comments': ins.get('comments', m.get('comments_count', '')), 'shares': ins.get('shares', ''), 'saves': ins.get('saved', ''),
                     'follows': ins.get('follows', ''), 'avg_watch_s': round(ins['ig_reels_avg_watch_time'] / 1000, 1) if ins.get('ig_reels_avg_watch_time') else '',
                     'link': m.get('permalink', ''), 'id': m['id']})
        print(f"{rows[-1]['date']}  {str(rows[-1]['views']):>8} views  {rows[-1]['hook'][:60]}", flush=True)
    HOME.mkdir(parents=True, exist_ok=True)
    out = HOME / 'results.csv'
    with open(out, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ['date'])
        w.writeheader(); w.writerows(rows)
    print(f"\n@{acct.get('username')}: {acct.get('followers_count')} followers. Saved {len(rows)} posts to {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('whoami'); sub.add_parser('queue'); sub.add_parser('publish-due'); sub.add_parser('refresh')
    for name in ('post', 'schedule'):
        p = sub.add_parser(name); p.add_argument('video')
        if name == 'schedule':
            p.add_argument('when', help='local time, "YYYY-MM-DD HH:MM"')
        p.add_argument('--caption'); p.add_argument('--caption-file'); p.add_argument('--thumb', type=float, help='cover frame, seconds')
        p.add_argument('--reels-only', action='store_true', help='do not also show it on the profile grid')
    u = sub.add_parser('unschedule'); u.add_argument('n', type=int)
    s = sub.add_parser('stats'); s.add_argument('--limit', type=int, default=30)
    a = ap.parse_args()

    if a.cmd == 'whoami':
        m = me(); print(f"@{m.get('username')} ({m.get('account_type')}), {m.get('followers_count')} followers, {m.get('media_count')} posts")
    elif a.cmd == 'post':
        publish(a.video, read_caption(a), not a.reels_only, a.thumb * 1000 if a.thumb is not None else None)
    elif a.cmd == 'schedule':
        when = dt.datetime.strptime(a.when, '%Y-%m-%d %H:%M')
        q = qload()
        q.append({'video': str(pathlib.Path(a.video).resolve()), 'when': when.isoformat(timespec='minutes'), 'caption': read_caption(a),
                  'thumb_ms': a.thumb * 1000 if a.thumb is not None else None, 'feed': not a.reels_only, 'status': 'waiting'})
        q.sort(key=lambda x: x['when']); qsave(q)
        print(f'Scheduled for {when:%a %d %b %H:%M}. {sum(x["status"] == "waiting" for x in q)} waiting in {HOME / "queue.json"}')
    elif a.cmd == 'queue':
        for i, x in enumerate(qload(), 1):
            print(f"{i}. {x['when'].replace('T', ' ')}  {x['status']:8} {pathlib.Path(x['video']).name}  {x['caption'][:50]!r}")
    elif a.cmd == 'unschedule':
        q = qload(); x = q.pop(a.n - 1); qsave(q); print('Removed', pathlib.Path(x['video']).name)
    elif a.cmd == 'publish-due':
        q = qload(); now = dt.datetime.now(); n = 0
        for x in q:
            if x['status'] == 'waiting' and dt.datetime.fromisoformat(x['when']) <= now:
                try:
                    x['id'], x['link'] = publish(x['video'], x['caption'], x.get('feed', True), x.get('thumb_ms'))
                    x['status'] = 'posted'; x['posted_at'] = now.isoformat(timespec='minutes')
                except SystemExit as e:
                    x['status'] = 'failed'; x['error'] = str(e); print(e)
                qsave(q); n += 1
        print(f'{n} posted or tried. {sum(x["status"] == "waiting" for x in q)} still waiting.')
    elif a.cmd == 'refresh':
        r = call('GET', 'https://graph.instagram.com/refresh_access_token', {'grant_type': 'ig_refresh_token'})
        env = HOME / '.env'; lines = env.read_text(encoding='utf-8').splitlines() if env.exists() else []
        lines = [l for l in lines if not l.startswith('IG_ACCESS_TOKEN=')] + [f"IG_ACCESS_TOKEN={r['access_token']}"]
        HOME.mkdir(parents=True, exist_ok=True); env.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print(f"Token renewed for {int(r.get('expires_in', 0)) // 86400} days and saved to {env}")
    elif a.cmd == 'stats':
        stats(a.limit)


if __name__ == '__main__':
    main()
