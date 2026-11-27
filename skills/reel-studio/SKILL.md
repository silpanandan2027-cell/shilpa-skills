---
name: reel-studio
description: An Instagram content studio for a product, service or personal brand - find reels that are winning in the niche, pick topics and hooks, write the script, make the reel (voiceover, captions, 12 visual styles, or text over your own footage), score it before posting, post or schedule it to Instagram, pull the stats, and turn winners into carousels. Use when the user types /reel-studio, or asks to grow on Instagram, make reels for their product or business, plan a content calendar, find viral ideas, schedule or post a reel, read their Instagram numbers, or repurpose a reel into a carousel.
---

# reel-studio

The whole loop for growing a product or business on Instagram, run by Claude:

**Find winners → Topic + hook → Script → Make the reel → Score it → Post or schedule → Read the numbers → Repurpose the winners**

The user is usually not technical. Keep replies short and friendly, do the work for them, and never ask them to run commands. Paths below are relative to this skill's folder; use its absolute path in commands.

After setup, run Python scripts with this skill's own Python: `.venv\Scripts\python.exe` on Windows, `.venv/bin/python` on Mac and Linux. `check.py`, `ig.py` and `outliers.py` also run with any Python 3.9+.

## 0. First run

1. `python scripts/setup.py` (any Python). Prints `READY` when done, about a minute the first time.
   - `NEED_FFMPEG`: install it for them (Windows: `winget install ffmpeg`, Mac: `brew install ffmpeg`), then run again.
   - `NEED_MALAYALAM_TYPE`: this skill borrows the fonts from the `malayalam-type` skill next to it; install the skills from this repo again.
2. The studio folder holds their brand, reels and stats: `~/reel-studio` (or the folder in `REEL_STUDIO`). Create it with:
   ```
   reel-studio/
     brand.md          who they are (below)
     reels/            one folder per reel: reel.json, reel.mp4, cover, caption.txt
     swipe/            winning reels from the niche
     calendar.md       the plan
     .env              IG_ACCESS_TOKEN=... (only if they want auto-posting)
   ```
3. If `brand.md` is missing, interview them in one message, then write it from `references/brand-template.md`: what they sell, who buys it, the one problem it solves, proof (numbers, customers), the offer and link, the language (Malayalam, English, Manglish), tone, their handle, and 3 to 5 accounts in their niche they admire. Read `brand.md` at the start of every session.

## 1. Find winners (swipe file)

Goal: 10 to 20 reels from the niche that beat their own account's usual views. Copy the idea and structure, never the words or footage.

- If the session has the `ig-viral` skill, use it.
- YouTube Shorts and TikTok accounts: `python scripts/outliers.py <channel or profile links> --last 40` writes `swipe.md` and `swipe.csv` ranked by outlier score (views ÷ the account's median). Run it inside `swipe/`.
- Instagram does not let tools list a profile's reels reliably. Ask the user to paste views and captions of recent reels from the accounts in `brand.md` (or screenshots; read the numbers off them) into a CSV with `account,url,views,caption`, then `python scripts/outliers.py --csv reels.csv`. For one reel link, the `watch` skill or `yt-dlp` (see the `video-editor` skill for cookies) can download it so you can study it.
- For each top outlier write one line in `swipe.md`: the hook formula it used (`references/hooks.md`), the format (talking head, faceless text, list, story, before/after), and why it worked.

## 2. Topics and hooks

- Turn the swipe file and `brand.md` into topics: every topic is one buyer problem, one belief to change, or one result to show. Mix: 50% teach (useful tips), 30% proof (results, behind the scenes, customer stories), 20% sell (offer, demo, objection handling).
- For each topic write 5 hooks with different formulas from `references/hooks.md`, score them (curiosity, clarity, specificity, 1 to 5 each) and pick the top one. Show the user the top 3 to choose from.
- When asked for a plan, write `calendar.md`: a table of date, topic, hook, format, style, status. A sensible pace is one reel a day, or 3 to 5 a week if they make them by hand.

## 3. Script

If the session has the `ig-reel` skill, use it for the words, then convert to beats. Otherwise:

- 15 to 40 seconds. Hook in the first 1.5 seconds, a payoff that keeps the promise, one call to action.
- Write it as **beats**: one idea each, 2 to 4 seconds when spoken. The spoken line is `say`; the screen text is short (under 8 words) and is not the same sentence, except on the hook.
- Write in the language from `brand.md`, the way people speak (ഓട്ടോമാറ്റിക്, റീൽ). Keep brand names in English. Read the script to the user before rendering.
- Run the `ig-human` skill (if present) over the spoken lines so they do not sound like AI.

## 4. Make the reel

Write `reels/<date>-<slug>/reel.json`:

```json
{"style": "bold", "voice": "ml-IN-SobhanaNeural", "rate": "+5%", "brand": {"handle": "@theirhandle"},
 "music": "../../music/calm.mp3", "music_volume": 0.12,
 "beats": [
  {"type": "hook", "kicker": "SaaS growth", "text": "Your product is *invisible*", "say": "Your product is invisible."},
  {"type": "point", "n": 1, "title": "One *reel* a day", "body": "About one buyer problem", "say": "Post one reel a day about one problem your buyer has."},
  {"type": "stat", "value": 2900000, "label": "views in 30 days", "say": "That got one founder three million views."},
  {"type": "cta", "text": "Comment GROW", "sub": "I'll DM you the plan", "say": "Comment grow and I'll send you the plan."}
 ]}
```

`*word*` colours a word with the accent. Every beat can have `say` (spoken, sets the length), `dur` (seconds, when there is no voice), `kicker`, `anim` (`pop`, `rise`, `slide`, `blur`, `slam`, `fade`, `type`), `cap: false` (no captions on this beat).

| `type` | Shows | Fields |
|---|---|---|
| `hook` | Big headline | `text`, `sub` |
| `point` | Numbered point | `n`, `title`, `body` |
| `stat` | Number that counts up (2900000 shows as 2.9M; `full: true` for every digit) | `value`, `from`, `prefix`, `suffix`, `decimals`, `label` |
| `list` | Cards ticking in | `title`, `items`, `numbered` |
| `bars` | Bar chart that grows, biggest first | `title`, `items` (`label`, `value`), `suffix` |
| `chat` | DM bubbles one by one | `title`, `messages` (`from`: `me` or `them`, `text`) |
| `compare` | Before and after columns | `title`, `left`/`right` (`title`, `items`) |
| `quote` | Quote | `text`, `by` |
| `terminal` | Typing in a terminal | `text` |
| `image` | Screenshot of their product, slow zoom | `src` (path next to reel.json), `caption` |
| `cta` | Pulsing button | `text`, `sub` |

**Styles** (`python scripts/make.py --styles`): `bold` (black and yellow, default), `clean` (light SaaS), `editorial` (cream serif), `news` (news desk), `neon` (glow), `brutalist` (thick borders), `retro` (80s sunset), `ledger` (money green), `terminal` (dev), `paper` (warm, Malayalam-first), `comic` (halftone), `minimal` (soft lavender). Pick one that fits the brand and keep it for a series so the grid looks like one account. Override colours with `"colors": {"accent": "#FF5A1F", "bg": "#111", "bg2": "#222", "ink": "#fff"}`.

**Voices** (free, from Microsoft Edge's read-aloud; needs internet): Malayalam `ml-IN-SobhanaNeural` (woman), `ml-IN-MidhunNeural` (man); Indian English `en-IN-NeerjaNeural`, `en-IN-PrabhatNeural`; US English `en-US-AndrewNeural`, `en-US-AvaNeural`. `rate` like `+5%` speeds it up. `"voice": "none"` for music-only reels. The captions follow the voice word by word automatically.

**Their own face** (talking head, best for trust): they record the clip on their phone; set `"over": "clip.mp4"` and `"voice": "none"`, give each beat `at` and `dur` in seconds, and for captions run the `malayalam-type` word timer (`python ../malayalam-type/scripts/words.py clip.mp4 --lang ml` with that skill's Python) and set `"words_file": "clip.words.json"`. Text sits in the top third, clear of the face. For zooms, colour and punch-ins on the footage, run `reel-fx` on the result.

**AI presenter**: if the user wants a face but will not film, the Higgsfield, Kling or Everygen connectors (if connected) can make an avatar clip from the script; that costs their credits there, so ask first. Then use it as `over`.

Then:
1. Check frames (fast, no voice): `python scripts/make.py reel.json --still 0.5,3,6` and look at the PNGs yourself. Fix text that is cut off, too small or covered.
2. Render: `python scripts/make.py reel.json` → `reel.mp4`, `reel_cover.jpg` (the hook frame, for the cover) and `reel.timed.json`. About 1 minute per 10 seconds of reel. Run it in the background if your tool times out.
3. Music: royalty-free tracks they own or from a free library. Trending Instagram audio cannot be added by a tool; tell them to add it in the Instagram app when posting if they want it (keep `music` out then).

## 5. Score it before posting (virality coach)

1. `python scripts/check.py reel.mp4` measures shape, sharpness, length, loudness, silent opening, black first frame and pace.
2. Then score the content yourself with `references/score.md` (hook, retention, value, payoff, ask, shareability, each out of 10). Watch frames at the start, middle and end.
3. Report in this shape: total out of 100, the three biggest fixes in plain words, and a rewritten hook if the hook scored under 8. Fix and re-render if the score is under 70. Be honest: a score predicts nothing for sure; it catches the usual mistakes.

## 6. Caption, post, schedule

- Caption: use the `ig-caption` skill if present. Otherwise: line one is a second hook (it shows before "... more"), 2 to 4 short lines of value, one ask (comment a keyword, save, share, follow), 3 to 5 search words written naturally, and 3 hashtags at most. Save it as `caption.txt` next to the reel.
- **Auto-posting** needs a Professional (Creator or Business) Instagram account and a token, set up once with `references/instagram-setup.md`. The token goes in `~/reel-studio/.env`; never print it, never put it in a repo or a chat message.
  - `python scripts/ig.py whoami` - test it
  - `python scripts/ig.py post reel.mp4 --caption-file caption.txt --thumb 1.0` - post now (`--thumb` picks the cover frame in seconds)
  - `python scripts/ig.py schedule reel.mp4 "2026-12-01 19:30" --caption-file caption.txt` - add to the queue; `queue` and `unschedule <n>` manage it
  - `python scripts/ig.py publish-due` posts what is due. Instagram's API has no scheduling of its own, so something must run this every 15 minutes: offer a Claude scheduled task, or set up Windows Task Scheduler / cron for them (`references/instagram-setup.md` has both).
- Without a token: give them the MP4, cover and caption, and tell them to post from the app (good when they want trending audio).
- Always ask before posting or scheduling. Posting is public.

## 7. Read the numbers

- `python scripts/ig.py stats --limit 30` writes `~/reel-studio/results.csv`: views, reach, likes, comments, shares, saves, follows and average watch time per post.
- Without a token: ask them to paste or screenshot the numbers from Instagram's Insights.
- If the session has the `ig-audit` skill, use it. Otherwise: rank by views and by shares+saves per 1,000 views, compare the hooks, formats, styles and lengths of the top 20% against the bottom 20%, and write 3 findings and 3 actions into `calendar.md` (make more of X, stop Y, test Z). Use outliers against their own median, as in step 1.

## 8. Repurpose winners

- Any reel at 2x their median or better: make a carousel from it. If the session has the `ig-carousel` skill use it for the copy. Write 5 to 8 beats (no `say`), the first is the hook, the last a `cta` ("Save this", "Follow for more"), and render `python scripts/make.py carousel.json --carousel` → `carousel_slide01.png` ... at 1080x1350.
- Also: a remake with a new hook (same body), a part 2, a talking-head version of a faceless winner, or the reverse. `ig-repurpose` (if present) turns long videos into reels.
- Instagram's API needs carousel images at a public web address, so carousels are posted from the app: send the PNGs to their phone.

## Limits to be honest about

- Instagram does not allow tools to read other people's reel lists reliably; competitor research uses pasted numbers, YouTube Shorts or TikTok.
- The free voice is good but not human. A real voice or their own face usually performs better; offer both.
- Trending audio can only be added in the Instagram app.
- No tool can promise views. The loop works by posting often and making more of what the numbers say works.
