// reel-studio engine. Everything is a pure function of time: studioSeek(t) puts the page in the state for time t,
// so frames can be captured one by one at any frame rate.
(function () {
  const ANIM = { bold: 'pop', clean: 'rise', editorial: 'fade', news: 'slide', neon: 'blur', brutalist: 'slam', retro: 'pop',
    ledger: 'rise', terminal: 'type', paper: 'rise', comic: 'slam', minimal: 'blur', over: 'pop' };
  const STYLES = Object.keys(ANIM);
  let spec, beats = [], duration = 0, stage, capEl, progEl;

  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const easeOut = x => 1 - Math.pow(1 - x, 3);
  const easeBack = x => { const c = 1.9; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  // "*word*" marks the accent. Words are split on spaces only, so Malayalam letter clusters are never broken.
  function words(text, cls = 'a') {
    let acc = false;
    return String(text ?? '').split('\n').map(line => line.split(/\s+/).filter(Boolean).map(tok => {
      let t = tok, on = acc;
      if (t.startsWith('*')) { on = true; t = t.slice(1); }
      const ends = t.endsWith('*') || t.endsWith('*,') || t.endsWith('*.') || t.endsWith('*!') || t.endsWith('*?');
      if (ends) t = t.replace(/\*(?=[,.!?]?$)/, '');
      acc = on && !ends;
      return `<span class="w ${cls}${on ? ' acc' : ''}">${esc(t)}</span>`;
    }).join(' ')).join('<br>');
  }
  const plain = s => String(s ?? '').replace(/\*/g, '');
  const fmtNum = (v, b) => {
    const big = Math.abs(b.value ?? b.to ?? v) >= 100000 && !b.full;   // 2900000 -> 2.9M (set "full": true for every digit)
    const n = big ? Number(v).toLocaleString('en', { notation: 'compact', maximumFractionDigits: 1 })
                  : Number(v).toLocaleString('en-IN', { minimumFractionDigits: b.decimals || 0, maximumFractionDigits: b.decimals || 0 });
    return (b.prefix || '') + n + (b.suffix || '');
  };

  function html(b) {
    const k = b.kicker ? `<div class="kicker a">${esc(b.kicker)}</div>` : '';
    switch (b.type) {
      case 'hook': return `${k}<h1 class="big hl fit">${words(b.text)}</h1>${b.sub ? `<div class="body a">${esc(b.sub)}</div>` : ''}`;
      case 'point': return `${b.n != null ? `<div><span class="num a">${esc(b.n)}</span></div>` : ''}${k}<h2 class="mid hl fit">${words(b.title || b.text)}</h2>${b.body ? `<div class="body a">${esc(b.body)}</div>` : ''}`;
      case 'stat': return `${k}<div class="value a fit" data-count>${fmtNum(b.from ?? 0, b)}</div><div class="label a">${words(b.label, '')}</div>`;
      case 'list': return `${b.title ? `<h2 class="mid hl fit">${words(b.title)}</h2>` : ''}<div class="items">${(b.items || []).map((it, i) =>
        `<div class="item a"><span class="tick">${b.numbered ? i + 1 : '✓'}</span><span>${esc(it)}</span></div>`).join('')}</div>`;
      case 'bars': {
        const items = (b.items || []).slice().sort((x, y) => y.value - x.value);
        return `${b.title ? `<h2 class="mid hl fit">${words(b.title)}</h2>` : ''}<div class="items">${items.map((it, i) =>
          `<div class="row a${i === 0 ? ' top' : ''}" data-v="${+it.value}"><span>${esc(it.label)}</span><div class="track"><div class="fill"></div></div><span class="val">0</span></div>`).join('')}</div>`;
      }
      case 'chat': return `${b.title ? `<div class="kicker a">${esc(b.title)}</div>` : k}<div class="chat">${(b.messages || []).map(m =>
        `<div class="msg a ${m.from === 'me' ? 'me' : 'them'}">${esc(m.text)}</div>`).join('')}</div>`;
      case 'quote': return `<div class="q a fit">${words(b.text, '')}</div>${b.by ? `<div class="by a">— ${esc(b.by)}</div>` : ''}`;
      case 'compare': return `${b.title ? `<h2 class="mid hl fit">${words(b.title)}</h2>` : ''}<div class="cols">${['left', 'right'].map((s, i) => {
        const c = b[s] || {}; return `<div class="col a ${i ? 'good' : 'bad'}"><h3>${esc(c.title || (i ? 'After' : 'Before'))}</h3>${(c.items || []).map(x => `<div>${esc(x)}</div>`).join('')}</div>`;
      }).join('')}</div>`;
      case 'terminal': return `${k}<div class="terminal-box a" data-type>${esc(b.text)}</div>`;
      case 'image': return `${k}<img class="shot a" src="${esc(b.src)}">${b.caption ? `<div class="cap a">${words(b.caption, '')}</div>` : ''}`;
      case 'cta': return `${k}<div><span class="pill a">${words(b.text, '')}</span></div>${b.sub ? `<div class="sub a">${esc(b.sub)}</div>` : ''}`;
      default: return `<h2 class="mid hl fit">${words(b.text || b.title || '')}</h2>`;
    }
  }

  function fit(el) {
    // Shrink the beat's text until nothing overflows the beat box or the line width.
    const box = el;
    const fits = () => box.scrollHeight <= box.clientHeight + 2 && [...box.querySelectorAll('.fit')].every(f => f.scrollWidth <= f.clientWidth + 2);
    for (let i = 0; i < 40 && !fits(); i++) {
      box.querySelectorAll('.fit,.body,.item,.msg,.q,.terminal-box').forEach(f => {
        const fs = parseFloat(getComputedStyle(f).fontSize); f.style.fontSize = (fs * 0.94) + 'px';
      });
    }
  }

  function captionGroups(ws) {
    const groups = []; let g = [];
    for (const w of ws) {
      const len = g.reduce((n, x) => n + x.w.length, 0) + w.w.length;
      if (g.length && (g.length >= 3 || len > 18 || w.t - g[g.length - 1].e > 0.6)) { groups.push(g); g = []; }
      g.push(w);
      if (/[.!?,]$/.test(w.w)) { groups.push(g); g = []; }
    }
    if (g.length) groups.push(g);
    return groups;
  }

  window.studioInit = async function (s, size) {
    spec = s;
    const style = STYLES.includes(spec.style) ? spec.style : 'bold';
    document.documentElement.className = (spec.over ? 'over ' : '') + 's-' + (spec.over ? 'over' : style) + ' fmt-' + (spec.format || 'reel');
    document.body.className = document.documentElement.className;
    const root = document.documentElement.style;
    for (const [k, v] of Object.entries(spec.colors || {})) root.setProperty('--' + k, v);
    stage = document.getElementById('stage');
    stage.innerHTML = '<div id="deco"></div>';
    let t = 0;
    beats = (spec.beats || []).map((b, i) => {
      const at = b.at ?? t, dur = b.dur ?? 3; t = at + dur;
      const el = document.createElement('section');
      el.className = 'beat ' + (b.type || 'point');
      el.innerHTML = html(b);
      // Malayalam must never get letter spacing: it pulls conjuncts and vowel signs apart
      el.querySelectorAll('.kicker,.big,.mid,.pill,.value,.label').forEach(x => { if (/[\u0D00-\u0D7F]/.test(x.textContent)) x.classList.add('ml'); });
      stage.appendChild(el);
      const anim = b.anim || ANIM[spec.over ? 'over' : style];
      const parts = [...el.querySelectorAll('.a')];
      // headline words come in quickly, then list items / bars / messages one after another
      const isItem = p => p.matches('.item,.row,.msg,.col');
      const head = parts.filter(p => !isItem(p)), items = parts.filter(isItem);
      head.forEach((p, j) => p._d = j * 0.07);
      const start = head.length ? Math.min(0.5, head.length * 0.07 + 0.15) : 0;
      const step = b.step ?? Math.min(0.55, (dur * 0.65 - start) / Math.max(1, items.length));
      items.forEach((p, j) => p._d = start + j * step);
      if (i === 0 && !spec.over) parts.forEach(p => p._d -= 0.45);   // the very first frame already shows the hook
      if (b.delays) parts.forEach((p, j) => { if (b.delays[j] != null) p._d = b.delays[j]; });
      return { b, el, at, dur, anim, parts, groups: b.words ? captionGroups(b.words) : [] };
    });
    duration = spec.duration || t;
    if (spec.brand && spec.brand.handle) stage.insertAdjacentHTML('beforeend', `<div id="brand">${esc(spec.brand.handle)}</div>`);
    if (spec.format === 'carousel') stage.insertAdjacentHTML('beforeend', '<div id="pager"></div>');
    capEl = document.createElement('div'); capEl.id = 'cap'; stage.appendChild(capEl);
    if (spec.progress !== false && spec.format !== 'carousel') { progEl = document.createElement('div'); progEl.id = 'prog'; stage.appendChild(progEl); }

    await document.fonts.ready;
    await Promise.all([...document.images].map(im => im.complete ? 0 : new Promise(r => { im.onload = im.onerror = r; })));
    for (const B of beats) {
      B.el.style.display = 'flex';
      const c = B.el.querySelector('[data-count]'); if (c) c.textContent = fmtNum(B.b.value ?? B.b.to ?? 0, B.b);
      fit(B.el); B.el.style.display = 'none';
    }
    studioSeek(0);
    return { duration, beats: beats.map(B => ({ at: B.at, dur: B.dur, type: B.b.type })) };
  };

  function enter(p, anim, x) {
    const e = anim === 'pop' || anim === 'slam' ? easeBack(x) : easeOut(x);
    switch (anim) {
      case 'pop': return [x > 0 ? 1 : 0, `scale(${0.6 + 0.4 * e})`, ''];
      case 'slam': return [x > 0 ? 1 : 0, `scale(${1.5 - 0.5 * e}) rotate(${(1 - e) * -4}deg)`, ''];
      case 'slide': return [clamp(x * 3), `translateX(${(1 - e) * -40}vw)`, ''];
      case 'blur': return [e, `translateY(${(1 - e) * 3}vw)`, `blur(${(1 - e) * 2}vw)`];
      case 'fade': return [e, '', ''];
      case 'type': return [x > 0 ? 1 : 0, '', ''];
      default: return [e, `translateY(${(1 - e) * 8}vw)`, ''];
    }
  }

  window.studioSeek = function (t) {
    let active = null;
    for (const B of beats) {
      const lt = t - B.at, on = lt >= 0 && lt < B.dur;
      B.el.style.display = on ? 'flex' : 'none';
      if (!on) continue;
      active = B;
      const speed = B.anim === 'type' ? 0.05 : 0.42;
      const out = spec.format === 'carousel' ? 1 : clamp((B.dur - lt) / 0.22);
      for (const p of B.parts) {
        const x = clamp((lt - p._d) / speed);
        const [o, tr, f] = enter(p, B.anim, x);
        p.style.opacity = o * out; p.style.transform = tr; p.style.filter = f;
      }
      const b = B.b;
      const grow = easeOut(clamp((lt - 0.15) / Math.min(1.6, B.dur * 0.6)));
      const cnt = B.el.querySelector('[data-count]');
      if (cnt) cnt.textContent = fmtNum((b.from ?? 0) + ((b.value ?? b.to ?? 0) - (b.from ?? 0)) * grow, b);
      const rows = B.el.querySelectorAll('.bars .row');
      if (rows.length) {
        const max = Math.max(...[...rows].map(r => +r.dataset.v)) || 1;
        rows.forEach((r, i) => {
          const g = easeOut(clamp((lt - r._d - 0.1) / 1.2));
          r.querySelector('.fill').style.width = (100 * g * (+r.dataset.v) / max) + '%';
          r.querySelector('.val').textContent = fmtNum(+r.dataset.v * g, b);
        });
      }
      const ty = B.el.querySelector('[data-type]');
      if (ty) { const full = b.text || ''; const n = Math.floor(clamp((lt - 0.2) / Math.max(0.6, Math.min(B.dur * 0.7, full.length * 0.04))) * full.length);
        ty.textContent = [...full].slice(0, n).join('') + (n < full.length && Math.floor(lt * 3) % 2 ? '▋' : ''); }
      const pill = B.el.querySelector('.pill');
      if (pill && lt > 0.5) pill.style.transform = `scale(${1 + 0.04 * Math.sin((lt - 0.5) * 6)})`;
      const shot = B.el.querySelector('.shot');
      if (shot && spec.format !== 'carousel') shot.style.transform = `scale(${1 + 0.06 * (lt / B.dur)})`;
      if (spec.format === 'carousel') {
        const pg = document.getElementById('pager'); const i = beats.indexOf(B);
        if (pg) pg.textContent = i === 0 && beats.length > 1 ? '' : `${i + 1} / ${beats.length}`;
        stage.querySelectorAll('.swipe').forEach(x => x.remove());
        if (i === 0 && beats.length > 1) stage.insertAdjacentHTML('beforeend', '<div class="swipe">Swipe →</div>');
      }
    }
    // captions follow the voice, three words at a time, the spoken word lit
    let capHtml = '';
    if (active && spec.captions !== false && active.b.cap !== false && active.groups.length) {
      let g = null;
      for (const grp of active.groups) if (t >= grp[0].t - 0.05) g = grp;
      if (g && t <= g[g.length - 1].e + 0.8) capHtml = g.map((w, i) => `<span class="w${t >= w.t && t < (g[i + 1] ? g[i + 1].t : w.e + 0.3) ? ' on' : ''}">${esc(plain(w.w))}</span>`).join(' ');
    }
    capEl.innerHTML = capHtml;
    capEl.classList.toggle('ml', /[\u0D00-\u0D7F]/.test(capHtml));
    if (progEl) progEl.style.width = (100 * clamp(t / duration)) + '%';
  };
})();
