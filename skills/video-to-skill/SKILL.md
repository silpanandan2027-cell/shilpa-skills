---
name: video-to-skill
description: Turn a video link into a new Claude skill. Downloads the video, grabs frames at intervals and scene changes, makes a timestamped transcript (from the video's captions, or by speech-to-text), then writes a SKILL.md that teaches what the video shows, and saves it. Use when the user types /video-to-skill with a link, or asks to make a skill, or a how-to, from a video.
---

# video-to-skill

Takes a video link and makes a new skill from it. The script does the mechanical work (download, frames, transcript). You do the thinking: you read the transcript, look at the frames, and write the skill in your own words.

The user is usually not technical. Keep replies short. Do the work, and do not ask them to run commands.

All paths are relative to this skill's folder. Use its absolute path in commands. After setup, run `python ...` commands with this skill's own Python: `.venv/bin/python` on Mac and Linux, `.venv\Scripts\python.exe` on Windows. (Setup itself runs with any Python.)

## 1. Check the link and set up

- The link is the argument after `/video-to-skill`. If there is none, ask for it, once.
- Only work on videos the user made, has permission to use, or that are openly licensed for this. If it is unclear, ask one short question before downloading.
- Run `python scripts/setup.py` once. It prints `READY` (about a minute the first time).
  - `NEED_FFMPEG`: install ffmpeg (Windows: `winget install ffmpeg`, Mac: `brew install ffmpeg`), then run setup again.
  - `NEED_PYTHON`: install Python 3.12 (Windows: `winget install Python.Python.3.12`), then run setup again.

## 2. Run the pipeline

```
<skill python> scripts/video_to_skill.py run "<link>" --work ./video-to-skill-work --lang en
```

- `--lang`: the language spoken in the video (`en`, `ml`, `hi`, ...), or `auto` to detect it.
- `--every 10`: seconds between frames. Use `5` for fast demos, `20` for long talks.
- `--max-frames 60`: upper limit on frames.
- `--model base`: speech model. Use `small` for better accuracy on hard audio (slower, bigger download).

It prints the work folder when it finishes. It takes a few minutes for a 10-minute video. Run it in the background if your tool times out, then wait for the output.

If it fails:
- Download errors (for YouTube, "Sign in", "403", "n challenge", "Requested format"): run `<skill python> -m pip install -U yt-dlp`, then run the pipeline again. Do not guess other fixes.
- `Could not load Whisper model`: the speech model download was blocked. Tell the user that transcription needs internet access to huggingface.co. The frames are still in the work folder, so you can continue with the frames and the video description.
- `NEED_...` or `not installed`: run setup again.

## 3. Read what it made

Inside the work folder:
- `notes.md`: title, uploader, length, transcript source, and what to read first. Read this first.
- `transcript.txt`: what is said, with timestamps. Long videos can be big, so read it in parts if needed.
- `frames/sheet_01.jpg`, `sheet_02.jpg`, ...: contact sheets, 12 frames each, labelled with time. Open each one with the Read tool to see the on-screen content (screens, code, diagrams, slides). These are cheaper than opening every frame.
- `frames/frames.json`: frame file names and times, for when you need one frame at full size.

If the transcript comes from captions, say so in your reply. Captions can be machine-made and get names and technical words wrong.

## 4. Decide what the skill does

Work out what the video teaches: a procedure, a workflow, a set of rules, or a tool's usage. Good skills do one job. If the video covers several unrelated things, make the skill about the one the user asked for, or ask which one.

Write the skill as a short procedure, not a summary of the video. A future Claude should be able to follow it without watching the video.

## 5. Write SKILL.md in the work folder

Save it as `<work folder>/SKILL.md`. Required format:

```markdown
---
name: <lowercase-words-with-hyphens, must match the folder name>
description: <one or two sentences: what it does and when to use it, written so Claude knows when to pick it>
---

# <Title>

<One paragraph: what this skill does and when to use it.>

## Steps

1. ...
2. ...

## Notes and gotchas

- ...

## Source

The steps come from a video by <uploader>: <link>. Frames that show the screens are in `references/frames/`, listed in `references/frames/frames.json`.
```

Rules:
- Write in your own words. Do not copy transcript sentences. A short quote of a few words is fine when it helps, but never a long passage.
- Describe steps the user can follow. Name the tools, menus, commands and settings the video shows.
- Mention the timestamp of any step that depends on a picture (for example "at 02:10 the settings panel shows ..."), so the reader can find it.
- If the video is unclear, or you are not sure of a step, say so in Notes. Do not invent details.
- Keep it under about 300 lines. Put long material in `references/` only if you save it there.
- `name` must be lowercase letters, digits and hyphens, at most 64 characters. Make it short and specific, for example `resize-photos-batch`.

## 6. Keep only the useful frames

Look at the contact sheets again and delete from `frames/` any frame that does not help a reader (talking heads, blank screens, duplicates). Keep the frames your SKILL.md points to. Leave `sheet_*.jpg` alone; they are skipped when saving.

## 7. Save it

```
<skill python> scripts/video_to_skill.py save "<work folder>" --dest ~/.claude/skills
```

- This copies SKILL.md, the frames you kept, and a `references/source.md` with the link. It does not copy the video.
- Add `--transcript` only if the user wants the full transcript saved with the skill.
- If the name already exists, it stops. Ask the user whether to replace it, then add `--force`.
- If the user is working inside the `shilpa-skills` repo and wants it added there, use `--dest skills` instead, and tell them to commit it.

## 8. Finish

Reply with:
- the new skill's name and where it was saved,
- how to use it (`/<name>`, after restarting Claude Code or opening a new session),
- one line on what it covers,
- a reminder to check the steps against the video before relying on them, especially when the transcript came from machine captions.

## Rules

- Do not publish or upload the video or the transcript anywhere. Everything stays on the user's machine.
- Do not copy the video's frames or transcript into a skill unless the user asks. The saved skill should be the user's own write-up.
- Never put the user's name or personal details into requests to outside services.
