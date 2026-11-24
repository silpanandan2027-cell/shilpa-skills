---
name: daily-reel
description: Make today's Instagram reel end to end - topic from the content plan, a 30-35 s script, ElevenLabs voiceover in the user's cloned voice with word timings, a HyperFrames 9:16 animation with synced captions, a cover and a 4-page guide, a Metricool Trial Reel draft (auto-share off), then wait for the user's "post", set up the comment-"AI" DM and log the topic. Use when the user types /daily-reel, when the morning scheduled task fires, or when the user says "post" on a reel this skill drafted.
---

# Daily reel

Runs every morning from a scheduled task, or by hand with `/daily-reel`. Work from the repo root
(`REEL_HOME` defaults to the working folder). Settings: `content/reel-config.json`. Style: `content/style.md`.
Today's files go in `content/reels/<YYYY-MM-DD>/`.

**Never post without the user's "post".** Steps 1-5 run on their own. Step 5 stops and waits.
If any step fails, stop, send the user the error in one line and what you need. Never fake a step
(no stand-in voice, no fake screenshot, no "posted" without a public URL).

## 0. Preflight (10 seconds)

- Read `content/reel-config.json`. Any value still starting with `YOUR_` is unset: stop and ask for it.
- `cd` to the repo root and `export REEL_HOME=$PWD`.
- Keys: ElevenLabs (`api.elevenlabs.io`, header `xi-api-key`) and Metricool (`app.metricool.com`, header `X-Mc-Auth`)
  are network secrets the proxy adds. If a call returns 401/403, call `request_credential` for that host. Never ask for a key in chat.

## 1. Topic

- Content plan = `content_plan` in the config. A repo path: read it. A claude.ai doc link: read it with the Claude Docs tools.
  A Google Doc shared by link: fetch `https://docs.google.com/document/d/<id>/export?format=txt`. Save the text to `content/reels/<date>/plan.txt`.
- If the plan has a dated row for today, use it. Otherwise: `python3 skills/daily-reel/scripts/topics.py next content/reels/<date>/plan.txt`.
- `topics.py seen "<topic>"` must exit 0, or pick the next one.

## 2. Script (30-35 s, about 80-95 spoken words)

Write it in `language` from the config, in the user's voice (short, spoken, no jargon). Use `/ig-reel` for the hook
options and `/ig-human` to strip AI tells.

| Beat | Time | What |
|---|---|---|
| Hook | 0-2 s | one line, max 8 words, a promise or a surprise. No "In this video" |
| Setup | 2-6 s | why it matters, one sentence |
| Step 1, 2, 3 | 6-28 s | one action each, ~7 s, start with a verb |
| CTA | 28-35 s | exactly: "Comment AI and I'll send you the free guide." (keep "comment AI" word for word) |

Save `script.txt` (spoken words only), `onscreen.md` (the text on screen per beat) and `caption.txt`
(`/ig-caption`: first line survives the "... more" cut, the CTA "Comment AI for the free guide", 3 hashtags).
Count words: under 75 or over 100 → rewrite.

## 3. Voice + word timings

```
python3 skills/daily-reel/scripts/voice.py content/reels/<date>/script.txt content/reels/<date> --voice <voice_id> --model <model>
```

Gives `voice.mp3` and `words.json`. Length must be 29-36 s (`ffprobe`); else trim or extend the script and redo.
Check `words.json` against the script; if the words drift, rerun with `--scribe` (ElevenLabs Scribe re-times from the audio).

## 4. Reel, cover, guide (HyperFrames)

Load `/hyperframes` and follow it, with `references/types/vertical.md` and `references/captions.md`. Then:

- Project: `content/reels/<date>/reel`, `npx hyperframes init content/reels/<date>/reel --skip-skills --skill=hyperframes`,
  set 1080x1920, 30 fps, root `data-duration` = voice length + 0.4 s.
- Copy `voice.mp3` into `assets/` as `<audio id="voice">`. Build the captions from `words.json` (word-synced, the
  spoken word highlighted), from the registry's caption blocks (`/hyperframes-registry`). Captions inside the 80% title-safe box.
- Scenes follow the beats in step 2, in `content/style.md`. If `content/style-refs/` has reels, match their look (`references/look.md`).
- No stops: skip the storyline choice; `npx hyperframes check --json`, fix all errors, `snapshot --review`, then
  `npx hyperframes render -o content/reels/<date>/reel.mp4`. Check with `ffprobe`: 1080x1920, 30 fps, 29-36 s, audio present.
- Cover: a still with the hook in 3-5 words, title kept inside the 1080x1350 centre so the grid crop reads.
  `node skills/daily-reel/scripts/snap.js png cover.html content/reels/<date>/cover.jpg 1080 1920`.
- Guide: `guide.html` with 4 `.page` sections, 1080x1350 each, same style. Page 1 title + promise,
  pages 2-3 the three steps in detail (one example or prompt each), page 4 a recap and `handle`.
  `node skills/daily-reel/scripts/snap.js pdf guide.html content/reels/<date>/guide.pdf 1080 1350` and
  `node skills/daily-reel/scripts/snap.js pages guide.html content/reels/<date>/guide-pages`.

## 5. Metricool Trial Reel draft, then STOP

```
python3 skills/daily-reel/scripts/metricool.py draft --video content/reels/<date>/reel.mp4 \
  --cover content/reels/<date>/cover.jpg --caption content/reels/<date>/caption.txt --when <date>T<post_time>:00
```

This uploads both files to Metricool and saves a draft with `draft=true`, `autoPublish=false`,
`instagramData.type=TRIAL_REEL`, `shareTrialAutomatically=false` (auto-share OFF). Then
`metricool.py get <id>` and confirm those four values came back. If `type` came back as something else, stop and tell the user.

Make the check image: write `review.html` (cover on the left; caption, post time, Trial Reel = yes, auto-share = OFF,
draft id on the right, all read from the `get` response), snap it to `review.png` (1600x1000), and send the user with `SendUserFile`
(status proactive): `review.png`, `reel.mp4`, `guide.pdf`. Say it is a summary of the saved draft, not Metricool's own page,
and that they can open it in Metricool Planner. Then:

> Today's reel: "<topic>". Draft is in Metricool as a Trial Reel, auto-share off. Say **post** to publish, or tell me what to change.

Push a notification (`PushNotification`) with the same line. Commit `content/reels/<date>/` (without `reel/node_modules`
or render cache) and push. **End the turn and wait.** Changes the user asks for: redo the step, update the same draft (`PUT`), re-send.

## 6. After "post"

Only on the user's own "post" (or "yes post it") in this session:

1. `metricool.py publish <id>`: schedules it 3 minutes out with autoPublish on, still auto-share off.
2. Watch `metricool.py status <id>` with `Monitor` (every 60 s, up to 20 min) until Instagram shows `PUBLISHED` with a `publicUrl`. `ERROR` → tell the user the `detailedStatus`.
3. The comment DM (SuperProfile AutoDM has no public API, so the user sets it in the app; make it a 30-second copy-paste):
   send them this block filled in:
   - Post: `<publicUrl>`  ·  Trigger keyword: `AI` (any case)  ·  Follow check: ON
   - Public reply to the comment: "Sent! Check your DMs 📩"
   - DM: "Here's your free guide on <topic> 👇" + button "Get the guide" → `<guide link>`
   - Guide link: `guide.link` in the config. If that is a SuperProfile page, tell them to add today's `guide.pdf` to it.
   If the user has made a reusable "any post" automation for keyword AI, skip this and just remind them to swap the PDF.

## 7. Log

```
python3 skills/daily-reel/scripts/topics.py log "<topic>" --date <date> --post <publicUrl> --guide <guide link>
```

Commit `content/topic-log.md` and push. Reply in one line: posted, the link, the topic logged.
