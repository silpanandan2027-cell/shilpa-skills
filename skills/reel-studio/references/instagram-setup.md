# Instagram auto-posting: one-time setup (about 15 minutes)

This uses Instagram's own official API ("Instagram API with Instagram Login"). It is free. You need a computer browser.

## 1. Make the account Professional
In the Instagram app: Profile → ☰ → Account type and tools → Switch to professional account → Creator (or Business). Free, and you can switch back.

## 2. Make a Meta developer app
1. Go to developers.facebook.com, log in, and click **My Apps → Create app**.
2. Use case: **Manage messaging & content on Instagram**. Give it any name (e.g. "My reel poster"). Business portfolio: skip if asked.
3. In the app's left menu open **Instagram → API setup with Instagram login**.
4. Under **App roles → Roles**, add your Instagram account as an **Instagram Tester**, then accept the invite in Instagram (Settings → Website permissions → Apps and websites → Tester invites). Needed while the app is in development mode, which is fine for posting to your own account.

## 3. Get the token
1. Back on **API setup with Instagram login**, at **Generate access tokens**, click **Add account**, log in to Instagram and allow the permissions (basic, content publish, insights).
2. Click **Generate token** next to your account and copy it. It lasts 60 days.

## 4. Give it to Claude safely
Do **not** paste the token in chat. Open (or create) the file `.env` in your `reel-studio` folder (`C:\Users\<you>\reel-studio\.env` on Windows, `~/reel-studio/.env` on Mac) and put one line in it:
```
IG_ACCESS_TOKEN=paste-it-here
```
Then ask Claude to run `ig.py whoami`. Renew monthly with `ig.py refresh` (Claude can do it), or it expires after 60 days.

## 5. Make scheduled posts go out on time
Instagram's API cannot schedule by itself, so the computer runs `ig.py publish-due` every 15 minutes. It has to be switched on at the time of the post.

- **Mac / Linux (cron):** `crontab -e`, then add
  `*/15 * * * * cd ~/reel-studio && python3 /path/to/skills/reel-studio/scripts/ig.py publish-due >> ~/reel-studio/post.log 2>&1`
- **Windows (Task Scheduler)**, in PowerShell:
  `schtasks /Create /SC MINUTE /MO 15 /TN "reel-studio post" /TR "python %USERPROFILE%\.claude\skills\reel-studio\scripts\ig.py publish-due"`
- **Claude scheduled task:** works only where the video files are reachable from that session (your own computer).

Limits: Instagram caps API posts per day (dozens, more than enough), videos up to 15 minutes and 300 MB, Reels must be 9:16 to show full-screen. Carousels need images on a public web address, so post carousels from the app.
