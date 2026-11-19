---
name: stream-clipper
description: Cut a long video or live stream into short vertical 9:16 clips for TikTok, Reels and Shorts, with captions. Clips Kitty (with its MCP server and the GTA plugin for GTA 5 / GTA 6 streams) on Windows, and AI YouTube Shorts Generator in local mode on Mac and Linux. Use when the user wants clips, highlights, Shorts, Reels or TikToks from a YouTube, Twitch or Kick link, a stream or VOD, a podcast or a long video file, asks to clip a GTA 6 stream, or types /stream-clipper.
---

# Stream clipper

The user is usually not technical. Keep replies short, do the work for them, and never ask them to run commands.

| Tool | Runs on | What it does | Where the installer put it |
|---|---|---|---|
| [Clips Kitty](https://github.com/ColinGPT9/clips-studio) | Windows 10/11 app | finds the best moments, crops 9:16 keeping the speaker or facecam in frame, burns captions, writes titles. All local, no key. | the app (winget `ColinGPT9.ClipsKitty`); source in `~/.shilpa-clippers/clips-studio` |
| Clips Kitty MCP server | wherever Claude runs | lets you drive the app: `queue_video`, `queue_local_file`, `job_status`, `queue_status`, `list_videos`, `list_clips`, `export_clip`, `engine_status` | MCP server `clips-kitty` (user scope), started by `scripts/clips_kitty_mcp.py` |
| [GTA plugin](https://github.com/ColinGPT9/Grand-Theft-Auto-6-Clips-Kitty-Plugin) | inside Clips Kitty | teaches Clips Kitty GTA moments: chases, crashes, stunts, fights, reactions. Id `colingpt9/gta-vi-highlights`. Unofficial, MIT, made for GTA 5; GTA 6 accuracy is not tested yet. | `~/.shilpa-clippers/Grand-Theft-Auto-6-Clips-Kitty-Plugin` |
| [AI YouTube Shorts Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) | Mac, Linux, Windows | long video in, ranked 9:16 shorts out. Local mode: yt-dlp, faster-whisper, FFmpeg and OpenCV on this computer; only the step that picks the moments calls Gemini or OpenAI. | `~/.shilpa-clippers/AI-Youtube-Shorts-Generator` with its own `venv` |

On Windows `~` is `%USERPROFILE%`. The upstream `clips-kitty` skill is installed next to this one; read it for the finer points of the MCP tools.

## 1. Pick the tool

1. **Clips Kitty first** when the `clips-kitty` MCP tools exist and `engine_status` answers. If it says Clips Kitty is not answering, tell the user to open the Clips Kitty app (or, from a source checkout, `python main.py serve` in `~/.shilpa-clippers/clips-studio`) and stop there: starting it is their call.
2. **Shorts Generator** on a Mac, on Linux, in a Claude cloud session, or when the user has no Clips Kitty.
3. A **GTA stream** wants Clips Kitty with the GTA plugin. Without Windows, use the Shorts Generator and say it does not know GTA events; it picks moments from what is said.

Nothing installed yet? Run the shilpa-skills installer (`install.ps1` on Windows, `install.sh` on Mac and Linux) or the steps in section 5.

## 2. Clips Kitty

1. Check: `engine_status`, then `queue_status` (a paused queue looks like a broken app).
2. Queue: `queue_video` with the link (YouTube, Twitch, Kick) or `queue_local_file` with a path on the user's computer. For gaming set `gaming=true`. For GTA also pass `pipeline={"id":"colingpt9/gta-vi-highlights"}` once the plugin is installed and enabled.
3. "Not queued" means that video was processed before: offer `list_clips` on it, or `force=true` if they really want it redone.
4. A two-hour stream takes tens of minutes. Report the job id and check `job_status` when the user asks again or after a long wait. Never sit in a polling loop.
5. `list_clips` gives id, score (0 to 100, a ranking, not a promise) and title. `list_videos` first if a video seems to have no clips. `export_clip` to the folder the user names.
6. Posting: Clips Kitty can publish (YouTube, Upload-Post, WoopSocial). Only call a `*_publish` or `*_execute` tool after the user has seen the exact plan and said yes.

**GTA plugin, first time** (Clips Kitty 2.1.0 or newer must be open):

```
py -m pip install --user -e "%USERPROFILE%\.shilpa-clippers\clips-studio\sdk\python[yaml]"
cd %USERPROFILE%\.shilpa-clippers\Grand-Theft-Auto-6-Clips-Kitty-Plugin
py -m clipskitty_sdk install .
```

The installer already did the `pip install`. Clips Kitty then shows the plugin's permissions (it asks for no network access): the user approves them in the app, and picks **Gaming / Reaction → Gaming detector** there. By hand the whole thing is `python main.py process "<link>"` in the Clips Kitty source folder.

## 3. Shorts Generator (local mode)

Folder: `~/.shilpa-clippers/AI-Youtube-Shorts-Generator`. Python: its `venv` (`venv/bin/python`, on Windows `venv\Scripts\python.exe`).

1. **Key**: it needs a Gemini key (free at aistudio.google.com) or an OpenAI key, read from `.env` in that folder. The installer made `.env` with `LLM_PROVIDER=gemini` and an empty `GEMINI_API_KEY=`.
   - On the user's computer: open `.env` for them (Notepad, TextEdit) and ask them to paste the key after `GEMINI_API_KEY=` and save. Never ask for the key in the chat, never print `.env`, never commit it.
   - In a Claude cloud session: request the credential for host `generativelanguage.googleapis.com` with header `x-goog-api-key` (OpenAI: `api.openai.com`, Bearer), then put a dummy value in `.env` (`GEMINI_API_KEY=dummy`); the proxy swaps in the real key.
2. **Run** (from any folder; it finds its own `.env`):
   ```
   <venv python> ~/.shilpa-clippers/AI-Youtube-Shorts-Generator/main.py "<link or file>" --mode local --num-clips 5 --output-json clips/result.json
   ```
   Set `LOCAL_OUTPUT_DIR` to an absolute folder (for example the project's `clips/`) so the shorts land where the user can find them; otherwise they go to `./output/short_01.mp4`, `short_02.mp4`, ... `--language ml` forces Malayalam, `--aspect-ratio 1:1` for square, `--format 1080` for sharper source.
3. Never use `--mode api`: it needs a paid MuAPI key and uploads the video.
4. Downloads fail on cloud servers ("Sign in to confirm you're not a bot")? Follow the cookies advice in the `video-editor` skill, or ask for the video file and pass its path.

## 4. After the clips exist

- Show each clip's score, title and hook, and look at a frame or two (`ffmpeg -ss 5 -i short_01.mp4 -frames:v 1 f.png`) before calling it done.
- Finishing touches go to the other skills: `/reel-fx` for zooms, colour and captions, `/malayalam-type` for Malayalam text, `/video-editor` for trims and joins.
- Streams belong to their streamers. Remind the user once to post only clips they have the right to use (their own streams, or a streamer who allows clipping) and to credit the streamer.

## 5. Install by hand

**Windows (PowerShell)**

```powershell
winget install ColinGPT9.ClipsKitty        # or the Microsoft Store; the setup wizard downloads the AI model
$d = "$HOME\.shilpa-clippers"; mkdir $d -Force; cd $d
git clone --depth 1 https://github.com/ColinGPT9/clips-studio
git clone --depth 1 https://github.com/ColinGPT9/Grand-Theft-Auto-6-Clips-Kitty-Plugin
py -m pip install --user -e "$d\clips-studio\sdk\python[yaml]"
claude mcp add --scope user clips-kitty -- py "$HOME\.claude\skills\stream-clipper\scripts\clips_kitty_mcp.py"
```

Clips Kitty needs Windows 10 or 11 and 16 GB of RAM; a graphics card is optional and only makes it faster. Running Clips Kitty from source instead of the app also needs Python 3.10+, Node.js 18+, FFmpeg and Ollama with a model (`ollama pull gemma:7b`).

**Mac / Linux** (Python 3.10+ and FFmpeg)

```bash
d=~/.shilpa-clippers; mkdir -p $d && cd $d
git clone --depth 1 https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator.git
cd AI-Youtube-Shorts-Generator
python3 -m venv venv && venv/bin/pip install -r requirements.txt -r requirements-local.txt "av<16"
printf 'LLM_PROVIDER=gemini\nGEMINI_API_KEY=\n' > .env
```
