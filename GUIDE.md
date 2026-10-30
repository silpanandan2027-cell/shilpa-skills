# Build your own AI video editor in Claude Code

A step-by-step guide. You will end up with a folder where you drop a raw video, say what you want, check a storyboard, and get a finished reel with effects and animated Malayalam text.

Everything here uses [Claude Code](https://claude.com/claude-code) and the two skills in this repo (`/malayalam-type` and `/reel-fx`).

## Step 1. Set up your folders

Make one folder, for example `AI-video-editor`. Inside it make three folders:

```
AI-video-editor/
  raw-footage/    your unedited videos go here
  references/     reels you like, for Claude to study
  exports/        finished videos come out here
```

Open a terminal in `AI-video-editor` and start Claude Code by typing `claude`.

## Step 2. Install the tools

You need these on your computer:

| Tool | What it is for |
|---|---|
| Claude Code | the editor you talk to |
| git | downloads the skills |
| ffmpeg | cuts and joins video |
| Python 3.9 or newer | runs the effects |
| Chrome or Edge | draws the animated text |

You do not have to install them by hand. Tell Claude:

> Install the skills from github.com/silpanandan2027-cell/shilpa-skills. Then check that ffmpeg and Python are installed, install anything missing, test each skill, and tell me when you are ready.

Restart Claude Code when it asks. Type `/` and you should see `/malayalam-type` and `/reel-fx`.

## Step 3. Teach it your style

Put 3 to 5 of your own reels, or reels you are inspired by, into `references/`. Then tell Claude:

> Study the videos in references. Write a brand.md with the fonts, colours, caption style and pacing I like. Use it for every edit from now on.

Claude writes `brand.md`. Read it and correct anything that is wrong. From then on, ask Claude to follow `brand.md`. The text skill lets you set your own colours and choose from several Malayalam fonts, so your reels look like yours.

## Step 4. Drop in your rough cut

Copy your raw video into `raw-footage/`. Then tell Claude what you want, in plain words:

> Take the video in raw-footage. Add a warm colour look, a slow zoom in on the first part, Malayalam titles for each point, and subtitles. Do not render yet. Show me a storyboard first.

## Step 5. Approve the storyboard

Before it renders, Claude writes a storyboard: a list of beats, each with its time, the effect, and the text on screen. It also saves a check frame for each beat so you can see what it will look like.

Go through the beats one by one. Reply "approved" or leave a note, for example "beat 3: make the zoom smaller" or "beat 5: change the title to ...". Claude updates it and shows the next draft.

When every beat is approved, say:

> Render it to exports.

Your finished video appears in `exports/` with your original audio. Always watch it before you post.

## What the skills can do

**`/reel-fx`: effects on your video**

| Effect | What it does |
|---|---|
| `zoom` | slow zoom in or out |
| `punch` | quick zoom in and back |
| `brightness` | brighten, darken or relight a moment |
| `rotate` | tilt the picture and back |
| `blur`, `mirror` | blur the picture, flip it |
| `shake`, `flash` | camera shake, white flash |
| `grade` | colour look: warm, cool, mono, film, moody, pop, fade |
| `vignette`, `bars`, `progress` | dark edges, cinema bars, a bar across the top that fills |
| `text` | any animated text below |

**`/malayalam-type`: animated Malayalam text**

`title`, `keyword`, `lower` (lower-third card), `quote`, `counter`, `list` (checklist), `cta` (a "comment ..." button), `captions` (subtitles that follow your speech).

## Good to know

- Text is drawn on top of your video. It does not go behind a person, and effects do not follow your face.
- Subtitles come from a speech model. Malayalam speech recognition is good but not perfect: read the words before you post.
- Rendering takes a few minutes for a 30 second reel when it has animated text.
- If something looks wrong, tell Claude what you see. It checks frames and fixes it.
