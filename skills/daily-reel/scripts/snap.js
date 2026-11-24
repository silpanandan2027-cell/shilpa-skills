// HTML -> PDF or PNG with the pre-installed Playwright Chromium.
//   node snap.js pdf guide.html guide.pdf            (each .page is one 1080x1350 page)
//   node snap.js png page.html out.png 1080 1920      (one screenshot)
//   node snap.js pages guide.html out-dir            (one PNG per .page, for the carousel/DM preview)
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const [mode, src, out, w = '1080', h = '1350'] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(src), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  if (mode === 'pdf') {
    await page.pdf({ path: out, width: w + 'px', height: h + 'px', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  } else if (mode === 'pages') {
    fs.mkdirSync(out, { recursive: true });
    const pages = await page.$$('.page');
    for (let i = 0; i < pages.length; i++) await pages[i].screenshot({ path: path.join(out, `page-${i + 1}.png`) });
  } else {
    await page.screenshot({ path: out, fullPage: false });
  }
  await browser.close();
  console.log(out);
})();
