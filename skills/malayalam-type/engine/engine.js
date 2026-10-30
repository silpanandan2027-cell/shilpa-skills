/* malayalam-type engine
 * Deterministic: the renderer calls mlSeek(t) and takes a screenshot, so any frame can be drawn on its own.
 * No third-party libraries. Written for Shilpa's skills.
 */
(function () {
  const THEMES = {
    paper: { bg: '#FBF6EE', ink: '#1B1B1F', mute: '#6B6B76', accent: '#C2410C', card: '#FFFFFF', onAccent: '#FFFFFF' },
    night: { bg: '#0E1116', ink: '#F4F4F5', mute: '#9AA0AB', accent: '#FBBF24', card: '#1B2029', onAccent: '#111111' },
    sky:   { bg: '#EAF2FF', ink: '#0F172A', mute: '#5B6B88', accent: '#2563EB', card: '#FFFFFF', onAccent: '#FFFFFF' },
    clear: { bg: 'transparent', ink: '#FFFFFF', mute: 'rgba(255,255,255,.82)', accent: '#FFD23F', card: 'rgba(18,18,22,.86)', onAccent: '#111111' }
  };
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const ease = {
    out: t => 1 - Math.pow(1 - t, 3),
    back: t => { const c = 1.6; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); },
    io: t => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2)
  };

  // Malayalam letter clusters. A virama (്), ZWJ or ZWNJ glues the next letter on; vowel signs,
  // anusvara and visarga stay with the letter before them. Never split with [...str].
  const MARK = /[ഀ-ഃ഻഼ാ-്ൗൢൣ‌‍]|\p{M}/u;
  function clusters(str) {
    const out = [], glue = [];
    let g = false;
    for (const ch of str) {
      if (out.length && !/\s/.test(ch) && (g || MARK.test(ch))) out[out.length - 1] += ch;
      else out.push(ch);
      g = ch === '്' || ch === '‍';
    }
    return out;
  }

  const stage = document.getElementById('stage');
  let U = 1, W = 1080, H = 1920, scenes = [], spec = null;

  const el = (tag, cls, parent, css) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (css) e.style.cssText = css;
    if (parent) parent.appendChild(e);
    return e;
  };
  const px = n => (n * U) + 'px';

  // Put text into `parent` as one animatable span per cluster. Returns the spans.
  function words(parent, text, hlText) {
    const spans = [];
    let hlFrom = -1, hlTo = -1;
    if (hlText) { hlFrom = text.indexOf(hlText); hlTo = hlFrom + hlText.length; }
    let off = 0, word = null;
    for (const c of clusters(text)) {
      if (c === '\n') { parent.appendChild(document.createElement('br')); word = null; }
      else if (/^\s+$/.test(c)) { parent.appendChild(document.createTextNode(c)); word = null; }
      else {
        // clusters of one word live in a no-wrap box, so a line can only break between words
        if (!word) word = el('span', '', parent, 'display:inline-block;white-space:nowrap');
        const s = el('span', 'g', word);
        s.textContent = c;
        if (hlFrom >= 0 && off >= hlFrom && off < hlTo) s.classList.add('hl');
        spans.push(s);
      }
      off += c.length;
    }
    return spans;
  }

  // Shrink a text block so its widest line fits inside maxW px.
  function fit(node, maxW) {
    const w = node.scrollWidth;
    if (w > maxW) node.style.fontSize = (parseFloat(getComputedStyle(node).fontSize) * maxW / w) + 'px';
  }

  // Per-cluster entrance. kind: rise | blur | fade | pop
  function enter(spans, lt, start, o = {}) {
    const stagger = o.stagger ?? 0.04, dur = o.dur ?? 0.55, kind = o.anim || 'rise';
    spans.forEach((s, i) => {
      const p = clamp((lt - start - i * stagger) / dur);
      const e = ease.out(p), b = ease.back(p);
      let tr = '', fl = '';
      if (kind === 'rise') tr = `translateY(${(1 - b) * 0.4}em)`;
      else if (kind === 'blur') { tr = `translateY(${(1 - e) * 0.25}em)`; fl = `blur(${(1 - e) * 14}px)`; }
      else if (kind === 'pop') tr = `scale(${0.55 + 0.45 * b})`;
      s.style.opacity = e;
      s.style.transform = tr;
      s.style.filter = fl;
    });
  }

  const fontClass = (name, dflt) => 'f-' + (name || dflt);

  // ---------- scene kinds ----------
  const kinds = {
    title(sc, root) {
      const lines = sc.lines || [{ ml: sc.ml, en: sc.en, accent: sc.accent }];
      const box = el('div', 'abs ctr', root, `top:${sc.y ?? 34}%`);
      const all = [];
      if (sc.kicker) { const k = el('div', 'kick', box, `font-size:${px(26)}`); k.textContent = sc.kicker; all.push({ spans: [k], plain: true }); }
      lines.forEach(l => {
        const d = el('div', 'ml ' + fontClass(sc.font, 'display'), box, `font-size:${px(sc.size ?? 150)}`);
        const sp = words(d, l.ml, l.accent);
        fit(d, W * 0.9);
        all.push({ spans: sp });
        if (l.en) {
          const e = el('div', 'en', box, `font-size:${px(52)};color:var(--mute);margin-top:${px(6)}`);
          e.textContent = l.en; all.push({ spans: [e], plain: true });
        }
      });
      return lt => {
        let t0 = 0.05;
        all.forEach(g => { enter(g.spans, lt, t0, { anim: g.plain ? 'blur' : sc.anim, stagger: g.plain ? 0 : 0.045 }); t0 += 0.18; });
      };
    },

    keyword(sc, root) {
      const box = el('div', 'abs ctr', root, `top:${sc.y ?? 38}%`);
      if (sc.kicker) { const k = el('div', 'kick', box, `font-size:${px(26)}`); k.textContent = sc.kicker; }
      const d = el('div', 'ml ' + fontClass(sc.font, 'round'), box, `font-size:${px(sc.size ?? 230)}`);
      const sp = words(d, sc.ml);
      fit(d, W * 0.88);
      const bar = el('div', '', box, `height:${px(18)};width:${px(sc.bar ?? 520)};margin:${px(-6)} auto 0;border-radius:${px(9)};background:var(--accent);transform-origin:0 50%`);
      let en;
      if (sc.en) { en = el('div', 'en', box, `font-size:${px(54)};color:var(--mute);margin-top:${px(26)}`); en.textContent = sc.en; }
      return lt => {
        enter(sp, lt, 0.05, { anim: sc.anim || 'pop', stagger: 0.05 });
        bar.style.transform = `scaleX(${ease.io(clamp((lt - 0.45) / 0.5))})`;
        if (en) enter([en], lt, 0.7, { anim: 'blur', stagger: 0 });
      };
    },

    lower(sc, root) {
      const card = el('div', 'abs card', root, `left:${px(56)};right:${px(56)};top:${sc.y ?? 70}%;border-radius:${px(34)};padding:${px(36)} ${px(46)} ${px(30)} ${px(58)};overflow:visible`);
      el('div', '', card, `position:absolute;left:${px(20)};top:${px(30)};bottom:${px(30)};width:${px(8)};border-radius:${px(4)};background:var(--accent)`);
      let k;
      if (sc.kicker) { k = el('div', 'kick', card, `font-size:${px(24)}`); k.textContent = sc.kicker; }
      const t = el('div', 'ml ' + fontClass(sc.font, 'sans'), card, `font-size:${px(sc.size ?? 88)};margin-top:${px(4)}`);
      const sp = words(t, sc.ml, sc.accent);
      fit(t, W - 216 * U);
      let e;
      if (sc.en) { e = el('div', 'en', card, `font-size:${px(40)};color:var(--mute)`); e.textContent = sc.en; }
      return lt => {
        const p = ease.back(clamp(lt / 0.7));
        card.style.transform = `translateX(${(1 - p) * -90 * U}px)`;
        card.style.opacity = ease.out(clamp(lt / 0.4));
        enter(sp, lt, 0.25, { anim: sc.anim || 'rise', stagger: 0.035 });
        if (k) enter([k], lt, 0.2, { anim: 'fade', stagger: 0 });
        if (e) enter([e], lt, 0.5, { anim: 'blur', stagger: 0 });
      };
    },

    quote(sc, root) {
      const box = el('div', 'abs ctr', root, `top:${sc.y ?? 30}%;padding:0 ${px(70)};box-sizing:border-box`);
      const q = el('div', 'f-serif', box, `font-size:${px(260)};line-height:.7;color:var(--accent);height:${px(150)}`);
      q.textContent = '“';
      const d = el('div', 'ml ' + fontClass(sc.font, 'serif'), box, `font-size:${px(sc.size ?? 84)};line-height:1.5;white-space:pre-wrap`);
      const sp = words(d, sc.ml, sc.accent);
      let a;
      if (sc.by) { a = el('div', 'en', box, `font-size:${px(44)};color:var(--mute);margin-top:${px(40)}`); a.textContent = '— ' + sc.by; }
      return lt => {
        enter([q], lt, 0, { anim: 'pop', stagger: 0 });
        enter(sp, lt, 0.25, { anim: sc.anim || 'blur', stagger: 0.03 });
        if (a) enter([a], lt, 0.25 + sp.length * 0.03 + 0.2, { anim: 'fade', stagger: 0 });
      };
    },

    counter(sc, root) {
      const box = el('div', 'abs ctr', root, `top:${sc.y ?? 30}%`);
      const n = el('div', 'en', box, `font-size:${px(sc.size ?? 320)};font-weight:800;letter-spacing:-.04em;color:var(--accent);line-height:1.05`);
      let lab;
      if (sc.ml) { lab = el('div', 'ml ' + fontClass(sc.font, 'display'), box, `font-size:${px(96)};margin-top:${px(10)}`); var sp = words(lab, sc.ml); fit(lab, W * 0.9); }
      const from = sc.from ?? 0, to = sc.to ?? 100, dec = sc.decimals ?? 0;
      const pre = sc.prefix || '', suf = sc.suffix || '';
      const fmt = v => pre + v.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suf;
      n.textContent = fmt(to); n.style.display = 'inline-block'; fit(n, W * 0.9); n.style.display = '';
      return lt => {
        const p = ease.out(clamp((lt - 0.1) / (sc.count ?? 1.4)));
        const v = from + (to - from) * p;
        n.textContent = fmt(v);
        enter([n], lt, 0, { anim: 'pop', stagger: 0, dur: 0.5 });
        if (sp) enter(sp, lt, 0.5, { anim: 'rise', stagger: 0.04 });
      };
    },

    list(sc, root) {
      const box = el('div', 'abs', root, `left:${px(70)};right:${px(70)};top:${sc.y ?? 26}%`);
      let head, hs = [];
      if (sc.title) { head = el('div', 'ml ' + fontClass(sc.font, 'display'), box, `font-size:${px(110)};margin-bottom:${px(30)}`); hs = words(head, sc.title); fit(head, W - 140 * U); }
      const rows = (sc.items || []).map(txt => {
        const r = el('div', 'card', box, `display:flex;align-items:center;gap:${px(28)};border-radius:${px(28)};padding:${px(22)} ${px(34)};margin-bottom:${px(22)}`);
        const dot = el('div', '', r, `flex:none;width:${px(62)};height:${px(62)};border-radius:50%;background:var(--accent);color:var(--onAccent,#fff);display:grid;place-items:center;font:700 ${px(36)} EN`);
        dot.textContent = '✓';
        const t = el('div', 'ml ' + fontClass(sc.itemFont, 'sans'), r, `font-size:${px(sc.itemSize ?? 66)};flex:1`);
        const sp = words(t, txt); fit(t, W - 140 * U - 62 * U - 28 * U - 68 * U);
        return { r, dot, sp };
      });
      const step = sc.step ?? 0.7;
      return lt => {
        enter(hs, lt, 0, { anim: 'rise', stagger: 0.04 });
        rows.forEach((row, i) => {
          const s = 0.5 + i * step, p = ease.back(clamp((lt - s) / 0.5));
          row.r.style.opacity = ease.out(clamp((lt - s) / 0.3));
          row.r.style.transform = `translateX(${(1 - p) * 60 * U}px)`;
          row.dot.style.transform = `scale(${ease.back(clamp((lt - s - 0.25) / 0.35))})`;
          enter(row.sp, lt, s + 0.1, { anim: 'fade', stagger: 0.02, dur: 0.3 });
        });
      };
    },

    cta(sc, root) {
      const box = el('div', 'abs ctr', root, `top:${sc.y ?? 42}%`);
      const pill = el('div', 'pill ' + fontClass(sc.font, 'round'), box, `font-size:${px(sc.size ?? 92)};padding:${px(26)} ${px(70)} ${px(36)};line-height:1.35`);
      const sp = words(pill, sc.ml);
      fit(pill, W * 0.9);
      let e;
      if (sc.en) { e = el('div', 'en', box, `font-size:${px(48)};color:var(--mute);margin-top:${px(34)}`); e.textContent = sc.en; }
      return lt => {
        const p = ease.back(clamp(lt / 0.6));
        const pulse = 1 + 0.025 * Math.sin(Math.max(0, lt - 0.6) * 6);
        pill.style.transform = `scale(${(0.5 + 0.5 * p) * pulse})`;
        pill.style.opacity = ease.out(clamp(lt / 0.3));
        if (e) enter([e], lt, 0.5, { anim: 'blur', stagger: 0 });
      };
    },

    // Word-timed subtitles: words = [{t, e?, w}] in seconds (from words.py or by hand).
    captions(sc, root) {
      const ws = sc.words || [], max = sc.max ?? 4, gap = sc.gap ?? 0.7;
      const chunks = []; let cur = [];
      ws.forEach((w, i) => {
        const prev = ws[i - 1];
        if (cur.length && (cur.length >= max || (prev && w.t - (prev.e ?? prev.t + 0.4) > gap))) { chunks.push(cur); cur = []; }
        cur.push(w);
      });
      if (cur.length) chunks.push(cur);
      const shadow = spec.theme === 'clear' || spec.transparent || sc.shadow ? `text-shadow:0 ${px(4)} ${px(20)} rgba(0,0,0,.55),0 0 ${px(3)} rgba(0,0,0,.6)` : '';
      const items = chunks.map(ch => {
        const d = el('div', 'abs ctr ml ' + fontClass(sc.font, 'display'), root, `top:${sc.y ?? 68}%;font-size:${px(sc.size ?? 96)};display:none;${shadow}`);
        const sp = ch.map((w, i) => { if (i) d.appendChild(document.createTextNode(' ')); const s = el('span', 'g', d); s.textContent = w.w; s.style.margin = '0 .12em'; return s; });
        d.style.display = 'block'; fit(d, W * 0.92); d.style.display = 'none';
        const start = ch[0].t, last = ch[ch.length - 1];
        return { d, sp, ch, start, end: (last.e ?? last.t + 0.5) + 0.12 };
      });
      return lt => {
        const t = lt + sc.at;
        items.forEach(it => {
          const on = t >= it.start - 0.04 && t < it.end;
          it.d.style.display = on ? 'block' : 'none';
          if (!on) return;
          const p = ease.back(clamp((t - it.start) / 0.22));
          it.d.style.opacity = ease.out(clamp((t - it.start + 0.04) / 0.12));
          it.d.style.transform = `translateY(${(1 - p) * 0.25 * 1}em) scale(${0.92 + 0.08 * p})`;
          it.sp.forEach((s, i) => {
            const cur = t >= it.ch[i].t && (i === it.ch.length - 1 || t < it.ch[i + 1].t);
            s.style.color = cur ? 'var(--accent)' : '';
            s.style.transform = cur ? 'scale(1.08)' : '';
          });
        });
      };
    }
  };

  // ---------- public api ----------
  window.mlInit = async function (s, size) {
    spec = s; W = size[0]; H = size[1]; U = W / 1080;
    const th = Object.assign({}, THEMES[s.theme || 'paper'] || THEMES.paper, s.colors || {});
    const r = document.documentElement.style;
    r.setProperty('--bg', th.bg); r.setProperty('--ink', th.ink); r.setProperty('--mute', th.mute);
    r.setProperty('--accent', th.accent); r.setProperty('--card', th.card); r.setProperty('--onAccent', th.onAccent);
    r.setProperty('--on-accent', th.onAccent); r.setProperty('--u', U + 'px');
    if (s.theme === 'clear' || s.transparent) document.body.classList.add('clear');
    stage.style.textShadow = (s.theme === 'clear' || s.transparent) ? `0 ${px(3)} ${px(14)} rgba(0,0,0,.45)` : '';

    await document.fonts.ready;
    await Promise.all(['800 40px "ML Display"', '600 40px "ML Sans"', '600 40px "ML Serif"', '700 40px "ML Round"',
      '700 40px "ML Soft"', '400 40px "ML Hand"', '500 40px "EN"'].map(f => document.fonts.load(f, 'അആക്ഷ Aa').catch(() => 0)));

    scenes = (s.scenes || []).map(sc => {
      if (sc.kind === 'captions' && sc.words && sc.words.length) {
        const last = sc.words[sc.words.length - 1];
        sc.at = sc.at ?? sc.words[0].t;
        sc.dur = sc.dur ?? ((last.e ?? last.t + 0.5) - sc.at + 0.3);
      }
      const root = el('div', 'scene', stage);
      root.style.display = 'block'; root.style.opacity = 0;
      if (!kinds[sc.kind]) throw new Error('Unknown scene kind: ' + sc.kind);
      const update = kinds[sc.kind](sc, root);
      root.style.display = 'none'; root.style.opacity = 1;
      return { sc, root, update };
    });
    return { duration: Math.max(0, ...scenes.map(o => o.sc.at + o.sc.dur)), windows: scenes.map(o => [o.sc.at, o.sc.at + o.sc.dur]) };
  };

  window.mlSeek = function (t) {
    for (const o of scenes) {
      const lt = t - o.sc.at, on = lt >= 0 && lt <= o.sc.dur;
      o.root.style.display = on ? 'block' : 'none';
      if (!on) continue;
      const out = clamp((o.sc.dur - lt) / (o.sc.fade ?? 0.3));
      o.root.style.opacity = out;
      o.root.style.transform = `scale(${1 + (1 - out) * 0.03})`;
      o.update(lt);
    }
  };
})();
