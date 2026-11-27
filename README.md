# Shilpa's Claude Skills

Skills for [Claude Code](https://claude.com/claude-code): an Instagram growth studio, three skills that edit your videos for you, and a web design stack so the websites Claude builds stop looking AI-made.

| Skill | What it does |
|---|---|
| `/reel-studio` | Your Instagram growth studio: finds reels that are winning in your niche, writes hooks and scripts, makes the reel (free voiceover in Malayalam or English, word-by-word captions, 12 styles, or text over your own footage), scores it before you post, posts or schedules it to Instagram, pulls your stats, and turns winners into carousels. See [reel-studio](#reel-studio). |
| `/malayalam-type` | Animated Malayalam text that never breaks the letters: titles, one-word pops, lower thirds, quotes, counters, checklists, call-to-action buttons and word-timed subtitles. Makes a video or a transparent overlay. |
| `/reel-fx` | Effects for your own video: zoom in and out, punch-in, brightness and lighting, rotation, blur, mirror, camera shake, 7 colour looks, vignette, flash, cinema bars, progress bar, plus any `/malayalam-type` text laid on top. Keeps your audio. |
| `/video-editor` | Claude as your video editor: download (yt-dlp), cut and join (FFmpeg), subtitles (Whisper), and animated videos in HTML (HyperFrames) or React (Remotion). |
| `/web-design` | Used automatically for any website or UI work. Runs the 9 tools below every time. |
| `/watch` | Claude watches a video for you: give it a YouTube link or a video file and ask what happens in it. From [bradautomates/claude-video](https://github.com/bradautomates/claude-video), installed as a plugin (in Claude Code it shows as `/watch:watch`). |

## reel-studio

The full loop, run by Claude: **find winners → hook → script → make the reel → score it → post or schedule → read the numbers → repurpose**.

```
/reel-studio set me up: I sell a billing app for small shops in Kerala
/reel-studio find what's going viral in my niche and give me 10 reel ideas
/reel-studio make a reel about "why shops lose money on credit", Malayalam voice, paper style
/reel-studio score this reel before I post it
/reel-studio schedule it for tomorrow 7:30 pm
/reel-studio how did my last 30 posts do? what should I make more of?
/reel-studio turn my best reel into a carousel
```

| Step | How |
|---|---|
| Find winners | ranks videos by how far they beat their own account's usual views (YouTube Shorts and TikTok links, or Instagram numbers you paste) |
| Hooks and scripts | 20 hook formulas, a scoring pass, scripts written as timed beats |
| Make the reel | 12 styles (bold, clean, editorial, news, neon, brutalist, retro, ledger, terminal, paper, comic, minimal); 11 beat types (hook, point, counting stat, list, bar chart, DM chat, before/after, quote, terminal, product screenshot, call to action); free neural voice (Malayalam: Sobhana, Midhun) with captions synced to it, or your own talking-head clip with text on top; music under the voice; loudness set for Instagram; cover image |
| Score before posting | measures shape, sharpness, length, loudness, silent opening, first frame and pace, then Claude scores hook, clarity, retention, value, payoff, ask and shareability out of 100 |
| Post and schedule | Instagram's official API, to your own Professional account. One-time setup: [instagram-setup.md](skills/reel-studio/references/instagram-setup.md) |
| Stats | views, reach, saves, shares, follows and watch time per post into `results.csv`, then what to make more of |
| Repurpose | carousel slides at 1080x1350 from any script |

Your brand, reels, plan and stats live in a `reel-studio` folder in your home folder. Auto-posting is optional: without it you get the video, cover and caption to post from the app.

## Video tools

The installer puts these on your computer (and Claude cloud sessions install them on startup):

| Tool | What it does |
|---|---|
| [Remotion](https://github.com/remotion-dev/remotion) | videos written in React (plus the Remotion agent skills) |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | videos written in HTML (plus the HyperFrames plugin) |
| [FFmpeg](https://github.com/FFmpeg/FFmpeg) | cut, join, resize, convert, audio |
| [Whisper](https://github.com/ggml-org/whisper.cpp) | speech to text and subtitles (whisper.cpp, `base` model) |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | download a video from a link |

Remotion is free for individuals and small teams; a company of 4 or more people needs a Remotion licence.

## Web design stack

The installer switches all of these on for every project:

| Tool | What it does | Installed as |
|---|---|---|
| [Impeccable](https://impeccable.style) | stops your site looking AI-made (`/impeccable critique`, `polish`, `audit` ...) | plugin |
| [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) | 84 DESIGN.md files: Apple, Stripe, Linear, Vercel, Notion and more | inside `/web-design` |
| [React Bits](https://reactbits.dev) | animated React components | shadcn MCP server |
| [GSAP](https://gsap.com) | scroll animation | npm, added per project |
| [Anime.js](https://animejs.com) | micro-animations | npm, added per project |
| [Refero](https://refero.design) | Claude studies real top designs before it builds | plugin with MCP server |
| [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp) | Claude tests and fixes its own site in real Chrome | MCP server |
| [Firecrawl](https://firecrawl.dev) | copy any website's vibe | MCP server |
| [Context7](https://context7.com) | stops Claude writing outdated code | MCP server |

An example page built with this stack is in [`examples/landing-page`](examples/landing-page).

After installing, open Claude Code and run `/mcp` to sign in to **Refero** (needs a paid Refero plan) and **Firecrawl** (free account). Context7 works without an account for light use; for more, get a free key at context7.com. The rest work without an account. Chrome DevTools needs Chrome installed.

## Install

You need Claude Code. The skills help install ffmpeg and Python the first time you use them.

**Windows (PowerShell)**
```powershell
git clone https://github.com/silpanandan2027-cell/shilpa-skills
cd shilpa-skills
powershell -ExecutionPolicy Bypass -File install.ps1
```

**Mac / Linux**
```bash
git clone https://github.com/silpanandan2027-cell/shilpa-skills
cd shilpa-skills && ./install.sh
```

Then restart Claude Code. Type `/` and the skills appear. The installer also adds the plugins and MCP servers above for every project, and adds a short note to `~/.claude/CLAUDE.md` so Claude always uses the web design stack.

> Easier: open Claude Code and say **"Install the skills from github.com/silpanandan2027-cell/shilpa-skills"**.

## Full guide

New to this? Follow [GUIDE.md](GUIDE.md): set up your folders, teach Claude your style, drop in a raw video, approve a storyboard, and export.

## Use

1. Open Claude Code.
2. Drag your video into the chat.
3. Say what you want:

```
/reel-fx warm colour, a zoom when I say "ശ്രദ്ധ", and a title at the start
/reel-fx add subtitles to this reel
/malayalam-type make a title card: "ഇനി എല്ലാം ഓട്ടോമാറ്റിക്"
```

Claude checks a few frames first, fixes anything that looks wrong, then renders. The first time, it sets itself up (about 2 minutes).

## What you need

- Windows, Mac or Linux
- Chrome or Edge (already on most computers)
- ffmpeg and Python 3.9 or newer (Claude installs them if missing)

## Good to know

- Text is drawn on top of your video. It does not go behind a person.
- Subtitles come from a speech model. Malayalam speech recognition is good but not perfect, so read the words before you post.
- Always watch the result before posting.

## Licence

MIT, see `LICENSE`. Fonts in `skills/malayalam-type/fonts` are free under the SIL Open Font Licence (licence files next to them).
