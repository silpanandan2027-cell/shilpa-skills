---
name: free-apps
description: Use the user's nine free, self-hosted apps instead of paid tools - Open Higgsfield (AI images and video, replaces Higgsfield), VoiceStudio (voiceovers and voice cloning, replaces ElevenLabs), OpenSEO (keywords, rank tracking, backlinks, site audits, replaces Semrush), WeKnora (ask questions across documents, replaces Notion AI), OpenWhispr (voice dictation, replaces Wispr Flow), OpenProject (tasks, boards, timelines, replaces Asana), Cal.diy (booking links, replaces Calendly), Chatwoot (one inbox for website chat, email and social messages, replaces Intercom) and Cap (screen recordings shared by link, replaces Loom). Use whenever the user wants a voiceover, voice clone, AI image or video, SEO research or audit, answers from their documents, dictation, a task or project board, a booking link, a customer or lead inbox, or a screen recording, or types /free-apps.
---

# Free apps

The user swapped nine paid apps for free ones. Whenever a chat needs one of these jobs, reach for the free app first,
and do not suggest the paid one. The user is usually not technical: do the work, keep replies short.

All of it is managed by one script in this repo: `apps/free-apps.sh` (on Windows, `apps/free-apps.ps1`).

```
apps/free-apps.sh status              # what is installed and running
apps/free-apps.sh install [app ...]   # install (all nine if none named)
apps/free-apps.sh start   [app ...]   # start the self-hosted ones
apps/free-apps.sh stop    [app ...]
```

If the repo is not on this computer, clone it: `git clone https://github.com/silpanandan2027-cell/shilpa-skills`.
Before using an app, run `status`. If it is installed but stopped, `start` it. If it is not installed, install just that app.

## Which app for which job

| Job | App (name in the script) | Where it runs | How Claude uses it |
|---|---|---|---|
| AI image or video | Open Higgsfield (`higgsfield`) | http://localhost:3100 (or openhiggsfield.ai) | Open the studio; the user pastes their own generation key once with **Add key** (`id:secret`). If the Higgsfield MCP tools are connected in this chat, those generate directly. |
| Voiceover, voice clone, dub, transcribe | VoiceStudio (`voicestudio`) | desktop app; backend http://localhost:3900 | MCP server `voicestudio` (added by the installer): `generate_speech`, `clone_voice`, `design_voice`, `transcribe`, `list_voices`. VoiceStudio must be open. Only clone a voice the user has the right to use. |
| SEO: keywords, rank tracking, backlinks, site audit | OpenSEO (`openseo`) | http://localhost:3001 | Needs a DataForSEO key (`DATAFORSEO_API_KEY` in `~/free-apps/open-seo/deploy/standalone/.env`, base64 of `login:password`). OpenSEO has an MCP server: make an API key in OpenSEO, then follow openseo.so/docs/mcp to add it with `claude mcp add`. |
| Ask questions across documents | WeKnora (`weknora`) | http://localhost:3200 (API http://localhost:8180) | Upload the documents to a knowledge base and ask there. For local models, install Ollama and choose it in WeKnora's model settings. WeKnora also has a built-in MCP server (see its docs). |
| Voice dictation into any app | OpenWhispr (`openwhispr`) | desktop app (Mac, Windows, Linux) | The user holds the hotkey and speaks; it works offline with local Whisper. Nothing for Claude to run. |
| Tasks, boards, timelines | OpenProject (`openproject`) | http://localhost:8090 | First login `admin` / `admin` (it asks for a new password). Use its REST API (`/api/v3`, API token from **My account > Access tokens**) to create work packages when the user asks Claude to add tasks. |
| Booking links with calendar sync | Cal.diy (`caldiy`) | http://localhost:3000 | Personal, non-production use only (its README says so; team features are removed). For a business, point the user to Cal.com's hosted plan, free for one person. Google / Outlook sync needs app keys in `~/free-apps/cal.diy/.env`. |
| One inbox for website chat, email, social | Chatwoot (`chatwoot`) | http://localhost:3400 | First visit creates the admin account. Add a **Website** inbox to get the chat widget snippet for the user's site. |
| Screen recording shared by link | Cap (`cap`) | desktop app | Free for personal use; business use needs the $29-a-year desktop licence - say so if the recording is for work. |

## Ports

higgsfield 3100 · voicestudio 3900 · openseo 3001 · weknora 3200 (API 8180) · openproject 8090 · caldiy 3000 (Redis 6380, API 3003) · chatwoot 3400.
Everything is bound to this computer only. Before putting any of them on the internet, set up HTTPS and real passwords.

## Notes

- The six self-hosted apps need Docker Desktop running (Open Higgsfield needs Node.js 22+ instead).
- Files live in `~/free-apps/<app>`; secrets the installer made are in each app's `.env` there. Never paste them into a chat or commit them.
- WeKnora is a big download (several GB) and Cal.diy is built from source on install (slow, about 8 GB of RAM). Install them only when first needed.
- In a Claude cloud session these apps are not on the user's computer. Say so, and do the job there only if the user asks.
