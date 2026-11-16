const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
(async () => { const b = await chromium.launch({ args: ['--allow-file-access-from-files'] }); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + path.join(__dirname, 'engine.html'));
  await p.evaluate(t => window.setup(t), JSON.parse(fs.readFileSync(path.join(__dirname, 'out/timing.json'))));
  fs.writeFileSync(path.join(__dirname, 'out/thumb_full.jpg'), Buffer.from((await p.evaluate(() => window.thumb())).split(',')[1], 'base64')); await b.close(); })();
