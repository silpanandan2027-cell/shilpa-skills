// Render engine.html to frames.
//   node render.js stills OUTDIR t1 t2 ...         -> PNG/JPG stills
//   node render.js video OUT.mp4 START END [fps]    -> silent H.264 segment
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');

(async () => {
  const [mode, out, ...rest] = process.argv.slice(2);
  const timing = JSON.parse(fs.readFileSync(path.join(__dirname, 'out/timing.json')));
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file://' + path.join(__dirname, 'engine.html'));
  const info = await page.evaluate(t => window.setup(t), timing);
  if (info.missing && info.missing.length) console.error("MISSING IMAGES:", info.missing);
  const grab = async t => Buffer.from((await page.evaluate(t => window.frame(t), t)).split(',')[1], 'base64');

  if (mode === 'stills') {
    fs.mkdirSync(out, { recursive: true });
    for (const t of rest.map(Number)) fs.writeFileSync(path.join(out, `t${t.toFixed(1).padStart(6, '0')}.jpg`), await grab(t));
  } else if (mode === 'info') {
    console.log(JSON.stringify(info));
  } else {
    const start = Number(rest[0]), end = Math.min(Number(rest[1]), info.end), fps = Number(rest[2] || 30);
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const n = Math.round((end - start) * fps);
    for (let i = 0; i < n; i++) {
      const buf = await grab(start + i / fps);
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 300 === 0) console.error(`${out}: ${i}/${n}`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
