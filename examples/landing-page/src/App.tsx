import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';
import { animate } from 'animejs';
import BlurText from '@/components/BlurText';
import CountUp from '@/components/CountUp';

gsap.registerPlugin(ScrollTrigger, useGSAP);

const REPO = 'https://github.com/silpanandan2027-cell/shilpa-skills';
const CLIP = 15; // seconds in the demo reel

const reduced = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ---------- the demo reel: a canvas backwater at dusk ---------- */

function Backwater() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const draw = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      const c = canvas.getContext('2d');
      if (!c) return;
      c.scale(dpr, dpr);
      const horizon = h * 0.58;

      const sky = c.createLinearGradient(0, 0, 0, horizon);
      sky.addColorStop(0, '#1d3340');
      sky.addColorStop(0.55, '#c9774a');
      sky.addColorStop(1, '#f2c57c');
      c.fillStyle = sky;
      c.fillRect(0, 0, w, horizon);

      const sunX = w * 0.62;
      const sun = c.createRadialGradient(sunX, horizon - 6, 2, sunX, horizon - 6, w * 0.5);
      sun.addColorStop(0, 'rgba(255,236,190,0.95)');
      sun.addColorStop(0.12, 'rgba(255,214,140,0.55)');
      sun.addColorStop(1, 'rgba(255,214,140,0)');
      c.fillStyle = sun;
      c.fillRect(0, 0, w, horizon);

      const water = c.createLinearGradient(0, horizon, 0, h);
      water.addColorStop(0, '#b8714c');
      water.addColorStop(1, '#14232b');
      c.fillStyle = water;
      c.fillRect(0, horizon, w, h - horizon);

      // sun reflection: broken horizontal strokes
      for (let i = 0; i < 26; i++) {
        const y = horizon + 4 + i * ((h - horizon) / 28);
        const spread = 6 + i * 2.2;
        const len = spread * (0.6 + ((i * 37) % 10) / 12);
        c.fillStyle = `rgba(255,220,160,${0.55 - i * 0.02})`;
        c.fillRect(sunX - len / 2 + Math.sin(i * 1.7) * spread * 0.4, y, len, 1.6);
      }

      // far bank
      c.fillStyle = '#20262a';
      c.fillRect(0, horizon - 3, w, 4);

      const ink = '#0e1417';
      const palm = (x: number, base: number, height: number, lean: number) => {
        const topX = x + lean;
        const topY = base - height;
        c.strokeStyle = ink;
        c.lineCap = 'round';
        c.lineWidth = Math.max(2, height * 0.035);
        c.beginPath();
        c.moveTo(x, base);
        c.quadraticCurveTo(x + lean * 0.2, base - height * 0.5, topX, topY);
        c.stroke();
        c.lineWidth = Math.max(1.5, height * 0.02);
        for (let f = 0; f < 9; f++) {
          const a = (f / 9) * Math.PI * 2 + 0.3;
          const reach = height * (0.28 + (f % 3) * 0.04);
          const ex = topX + Math.cos(a) * reach;
          const ey = topY + Math.sin(a) * reach * 0.45 + reach * 0.35;
          c.beginPath();
          c.moveTo(topX, topY);
          c.quadraticCurveTo(topX + Math.cos(a) * reach * 0.6, topY - reach * 0.15, ex, ey);
          c.stroke();
        }
      };
      palm(w * 0.08, horizon + 2, h * 0.36, w * 0.06);
      palm(w * 0.2, horizon + 2, h * 0.26, -w * 0.03);
      palm(w * 0.9, horizon + 2, h * 0.4, -w * 0.08);

      // a vallam (country boat) with a figure, on the water
      const bx = w * 0.4;
      const by = horizon + (h - horizon) * 0.32;
      c.fillStyle = ink;
      c.beginPath();
      c.moveTo(bx - w * 0.17, by - 6);
      c.quadraticCurveTo(bx, by + 10, bx + w * 0.17, by - 6);
      c.quadraticCurveTo(bx, by + 2, bx - w * 0.17, by - 6);
      c.fill();
      c.fillRect(bx - 2, by - 26, 4, 22);
      c.beginPath();
      c.arc(bx, by - 30, 4.5, 0, Math.PI * 2);
      c.fill();
      c.strokeStyle = ink;
      c.lineWidth = 1.6;
      c.beginPath();
      c.moveTo(bx + 1, by - 20);
      c.lineTo(bx + w * 0.12, by + 14);
      c.stroke();
    };
    draw();
    const ro = new ResizeObserver(draw);
    ro.observe(canvas);
    return () => ro.disconnect();
  }, []);

  return <canvas ref={ref} className="reel-canvas" aria-hidden="true" />;
}

/* ---------- caption timing, as the skill would write it ---------- */

type Word = { t: number; w: string };
const LINES: Word[][] = [
  [
    { t: 3.0, w: 'ഈ' },
    { t: 3.4, w: 'റീൽ' },
    { t: 3.9, w: 'ഞാൻ' },
    { t: 4.4, w: 'എഡിറ്റ്' },
    { t: 5.0, w: 'ചെയ്തിട്ടില്ല' }
  ],
  [
    { t: 6.4, w: 'ശ്രദ്ധ' },
    { t: 7.1, w: 'കൊടുത്ത്' },
    { t: 7.7, w: 'കേൾക്കൂ' }
  ],
  [
    { t: 9.2, w: 'Claude' },
    { t: 9.8, w: 'ആണ്' },
    { t: 10.3, w: 'എല്ലാം' },
    { t: 11.0, w: 'ചെയ്തത്' }
  ],
  [
    { t: 12.4, w: 'കമന്റ്' },
    { t: 13.0, w: 'ചെയ്യൂ' }
  ]
];

const LOOKS = {
  warm: 'sepia(0.28) saturate(1.25) hue-rotate(-8deg)',
  cool: 'saturate(0.85) hue-rotate(18deg) brightness(1.03)',
  mono: 'grayscale(1) contrast(1.12)',
  film: 'sepia(0.22) contrast(0.92) saturate(0.82) brightness(1.04)',
  moody: 'brightness(0.78) contrast(1.22) saturate(0.78)',
  pop: 'saturate(1.55) contrast(1.12)',
  fade: 'contrast(0.78) brightness(1.12) saturate(0.8)'
} as const;
type Look = keyof typeof LOOKS;

const fmt = (s: number) => {
  const m = Math.floor(s / 60);
  const sec = (s % 60).toFixed(2).padStart(5, '0');
  return `${String(m).padStart(2, '0')}:${sec}`;
};

function Reel() {
  const [time, setTime] = useState(4.4);
  const [look, setLook] = useState<Look>('warm');
  const [bars, setBars] = useState(false);
  const [vignette, setVignette] = useState(true);
  const stageRef = useRef<HTMLDivElement>(null);
  const flashRef = useRef<HTMLDivElement>(null);
  const capRef = useRef<HTMLDivElement>(null);

  // the reel's clock: loops every 15 s, and holds still for reduced motion
  useEffect(() => {
    if (reduced()) return;
    let raf = 0;
    let last = performance.now();
    const tick = (now: number) => {
      setTime(t => (t + (now - last) / 1000) % CLIP);
      last = now;
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  const line = LINES.find(l => time >= l[0].t - 0.2 && time < l[l.length - 1].t + 1.1);
  const lit = line ? line.reduce((idx, word, i) => (time >= word.t ? i : idx), -1) : -1;
  const litKey = line && lit >= 0 ? line[lit].t : -1;

  // Anime.js: pop the spoken word as it lights up
  useEffect(() => {
    if (litKey < 0 || reduced()) return;
    const el = capRef.current?.querySelector('.is-lit');
    if (el) animate(el, { scale: [1.18, 1], duration: 380, ease: 'outBack(2)' });
  }, [litKey]);

  const showTitle = time < 2.6;
  const zooming = time >= 6.4 && time < 8.2;

  const fire = (fx: 'punch' | 'flash' | 'shake' | 'tilt') => {
    const stage = stageRef.current;
    if (!stage) return;
    if (fx === 'punch') animate(stage, { scale: [1, 1.3, 1], duration: 900, ease: 'inOutQuad' });
    if (fx === 'shake') animate(stage, { x: [0, -7, 6, -5, 4, -2, 0], y: [0, 3, -4, 2, -1, 0], duration: 480, ease: 'linear' });
    if (fx === 'tilt') animate(stage, { rotate: [0, 6, 0], scale: [1, 1.08, 1], duration: 1000, ease: 'inOutSine' });
    if (fx === 'flash' && flashRef.current) animate(flashRef.current, { opacity: [0.95, 0], duration: 420, ease: 'outQuad' });
  };

  return (
    <div className="monitor">
      <div className="phone" aria-label="Demo reel with Malayalam captions">
        <div className="phone-screen">
          <div className={`zoomer${zooming ? ' is-zooming' : ''}`}>
            <div className="stage" ref={stageRef} style={{ filter: LOOKS[look] }}>
              <Backwater />
            </div>
          </div>
          {vignette && <div className="vignette" />}
          <div className="flash" ref={flashRef} />
          <div className={`bars${bars ? ' is-on' : ''}`} aria-hidden="true">
            <span />
            <span />
          </div>
          <div className="progress" aria-hidden="true">
            <span style={{ transform: `scaleX(${time / CLIP})` }} />
          </div>

          <div className={`reel-title${showTitle ? ' is-on' : ''}`} lang="ml">
            <span className="reel-kicker">ടിപ്</span>
            <span className="reel-title-line">ഇനി എല്ലാം</span>
            <span className="reel-title-line accent">ഓട്ടോമാറ്റിക്</span>
          </div>

          <div className="captions" ref={capRef} lang="ml" aria-live="off">
            {line?.map((word, i) => (
              <span key={word.t} className={i === lit ? 'is-lit' : i < lit ? 'is-said' : ''}>
                {word.w}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="console">
        <div className="timecode" aria-label="Playhead time">
          <span>{fmt(time)}</span>
          <span className="muted"> / {fmt(CLIP)}</span>
          {zooming && <span className="fx-tag">zoom on “ശ്രദ്ധ”</span>}
        </div>

        <fieldset className="control">
          <legend>grade</legend>
          <div className="chips">
            {(Object.keys(LOOKS) as Look[]).map(l => (
              <button
                key={l}
                type="button"
                id={`look-${l}`}
                className="chip"
                aria-pressed={look === l}
                onClick={() => setLook(l)}
              >
                {l}
              </button>
            ))}
          </div>
        </fieldset>

        <fieldset className="control">
          <legend>try an effect</legend>
          <div className="chips">
            {(['punch', 'flash', 'shake', 'tilt'] as const).map(fx => (
              <button key={fx} type="button" id={`fx-${fx}`} className="chip" onClick={() => fire(fx)}>
                {fx === 'tilt' ? 'rotate' : fx}
              </button>
            ))}
            <button type="button" id="fx-bars" className="chip" aria-pressed={bars} onClick={() => setBars(b => !b)}>
              bars
            </button>
            <button
              type="button"
              id="fx-vignette"
              className="chip"
              aria-pressed={vignette}
              onClick={() => setVignette(v => !v)}
            >
              vignette
            </button>
          </div>
        </fieldset>
        <p className="note">A browser preview. The real skill renders each effect with ffmpeg and keeps your audio.</p>
      </div>
    </div>
  );
}

/* ---------- the plan, as a scrubbing timeline ---------- */

type Beat = { fx: string; start: number; end: number; label: string; ml?: boolean };
const BEATS: Beat[] = [
  { fx: 'grade', start: 0, end: 15, label: 'look: warm' },
  { fx: 'text', start: 0, end: 2.6, label: 'ഇനി എല്ലാം ഓട്ടോമാറ്റിക്', ml: true },
  { fx: 'captions', start: 3, end: 14, label: 'words timed to your voice' },
  { fx: 'zoom', start: 6.4, end: 8.2, label: '1.0 → 1.3 on “ശ്രദ്ധ”' }
];

function Timeline() {
  const root = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState<string[]>(['grade', 'text']);

  useGSAP(
    () => {
      if (reduced()) return;
      gsap.fromTo(
        '.playhead',
        { left: '0%' },
        {
          left: '100%',
          ease: 'none',
          scrollTrigger: {
            trigger: '.tracks',
            start: 'top 85%',
            end: 'bottom 25%',
            scrub: 0.6,
            onUpdate: self => {
              const t = self.progress * CLIP;
              setActive(BEATS.filter(b => t >= b.start && t <= b.end).map(b => b.fx));
            }
          }
        }
      );
    },
    { scope: root }
  );

  return (
    <div className="timeline" ref={root}>
      <div className="ruler" aria-hidden="true">
        {Array.from({ length: 6 }, (_, i) => (
          <span key={i} style={{ left: `${(i * 3 * 100) / CLIP}%` }}>
            0:{String(i * 3).padStart(2, '0')}
          </span>
        ))}
      </div>
      <div className="tracks">
        <div className="playhead-rail" aria-hidden="true">
          <div className="playhead" />
        </div>
        {BEATS.map(b => (
          <div className="lane" key={b.fx}>
            <span className="lane-name">{b.fx}</span>
            <div className="lane-track">
              <span
                className={`beat beat-${b.fx}${b.end - b.start < 4 ? ' is-short' : ''}${active.includes(b.fx) ? ' is-active' : ''}`}
                style={{ left: `${(b.start / CLIP) * 100}%`, width: `${((b.end - b.start) / CLIP) * 100}%` }}
                lang={b.ml ? 'ml' : undefined}
              >
                {b.end - b.start >= 4 && <span className="beat-label">{b.label}</span>}
              </span>
              {b.end - b.start < 4 && (
                <span
                  className="beat-outside"
                  style={{ left: `calc(${(b.end / CLIP) * 100}% + 8px)` }}
                  lang={b.ml ? 'ml' : undefined}
                >
                  {b.label}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------- install ---------- */

const INSTALL = {
  windows: `git clone ${REPO}\ncd shilpa-skills\npowershell -ExecutionPolicy Bypass -File install.ps1`,
  mac: `git clone ${REPO}\ncd shilpa-skills && ./install.sh`
};

function Install() {
  const [os, setOs] = useState<keyof typeof INSTALL>('windows');
  const [copied, setCopied] = useState(false);
  const codeRef = useRef<HTMLPreElement>(null);

  const copy = () => {
    const done = () => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    };
    navigator.clipboard?.writeText(INSTALL[os]).then(done, () => {
      const sel = window.getSelection();
      if (codeRef.current && sel) {
        const range = document.createRange();
        range.selectNodeContents(codeRef.current);
        sel.removeAllRanges();
        sel.addRange(range);
      }
    });
  };

  return (
    <div className="install-box">
      <div className="install-head">
        <div className="tabs" role="tablist" aria-label="Your computer">
          {(['windows', 'mac'] as const).map(k => (
            <button
              key={k}
              type="button"
              role="tab"
              id={`os-${k}`}
              aria-selected={os === k}
              className="tab"
              onClick={() => setOs(k)}
            >
              {k === 'windows' ? 'Windows' : 'Mac / Linux'}
            </button>
          ))}
        </div>
        <button type="button" id="copy-install" className="copy" onClick={copy}>
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre ref={codeRef}>
        <code>{INSTALL[os]}</code>
      </pre>
    </div>
  );
}

/* ---------- page ---------- */

const STEPS = [
  { title: 'Drop in your video', body: 'Drag a raw phone video into Claude Code. Vertical works best.' },
  { title: 'Say what you want', body: 'Plain words are enough: a warm look, a zoom on one word, a title at the start.' },
  { title: 'Approve the storyboard', body: 'Claude lists each beat with its time and saves a check frame, so you see it before it renders.' },
  { title: 'Render to exports', body: 'The finished reel comes back at 1080 wide with your original audio.' }
];

export default function App() {
  const page = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      if (reduced()) return;
      gsap.utils.toArray<HTMLElement>('.step').forEach((el, i) => {
        gsap.from(el, {
          y: 28,
          duration: 0.7,
          delay: i * 0.08,
          ease: 'power3.out',
          scrollTrigger: { trigger: el, start: 'top 92%' }
        });
      });
    },
    { scope: page }
  );

  return (
    <div className="page" ref={page}>
      <header className="nav wrap">
        <a className="wordmark" href={REPO} target="_blank" rel="noreferrer">
          shilpa-skills
        </a>
        <a className="nav-link" href={REPO} target="_blank" rel="noreferrer">
          GitHub
        </a>
      </header>

      <section className="hero wrap">
        <div className="hero-copy">
          <h1 className="hero-ml" lang="ml">
            <BlurText text="ഇനി എല്ലാം ഓട്ടോമാറ്റിക്" animateBy="words" trigger="load" delay={160} className="blur-line" />
          </h1>
          <p className="hero-en">Two Claude Code skills. You talk, Claude edits the reel, and the Malayalam letters stay whole.</p>
          <p className="hero-body">
            Effects, colour looks, titles and word-timed subtitles for your own videos. Conjuncts like ക്ഷ and സ്റ്റ
            animate as one shape, so nothing breaks apart on screen.
          </p>
          <div className="hero-actions">
            <a className="btn" href="#install">
              Install the skills
            </a>
            <a className="btn-quiet" href={REPO} target="_blank" rel="noreferrer">
              Read the guide
            </a>
          </div>
        </div>
        <Reel />
      </section>

      <section className="stats wrap" aria-label="What is inside">
        <div className="stat">
          <CountUp to={13} trigger="load" duration={1.4} className="stat-n" />
          <span>video effects</span>
        </div>
        <div className="stat">
          <CountUp to={8} trigger="load" duration={1.4} className="stat-n" />
          <span>kinds of animated text</span>
        </div>
        <div className="stat">
          <CountUp to={7} trigger="load" duration={1.4} className="stat-n" />
          <span>colour looks</span>
        </div>
        <div className="stat">
          <CountUp to={6} trigger="load" duration={1.4} className="stat-n" />
          <span>Malayalam font styles</span>
        </div>
      </section>

      <section className="skills wrap">
        <article className="skill">
          <code className="cmd">/malayalam-type</code>
          <h2>Animated Malayalam text</h2>
          <p>
            Titles, one-word pops, lower thirds, quotes, counters, checklists, call-to-action pills and subtitles that
            follow your speech. Makes a video or a transparent overlay.
          </p>
          <ul className="kinds" aria-label="Text kinds">
            {['title', 'keyword', 'lower', 'quote', 'counter', 'list', 'cta', 'captions'].map(k => (
              <li key={k}>{k}</li>
            ))}
          </ul>
        </article>
        <article className="skill">
          <code className="cmd">/reel-fx</code>
          <h2>Effects on your own video</h2>
          <p>
            Zoom, punch-in, brightness, rotation, blur, mirror, camera shake, colour looks, vignette, flash, cinema
            bars and a progress bar, with any Malayalam text laid on top. Your audio stays.
          </p>
          <ul className="kinds" aria-label="Effects">
            {['punch', 'zoom', 'brightness', 'rotate', 'blur', 'mirror', 'shake', 'grade', 'vignette', 'flash', 'bars', 'progress', 'text'].map(k => (
              <li key={k}>{k}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="plan wrap">
        <div className="plan-copy">
          <h2>One sentence becomes a plan</h2>
          <p className="prompt">
            <span className="prompt-mark">&gt;</span> /reel-fx warm colour, a zoom when I say “
            <span lang="ml">ശ്രദ്ധ</span>”, and a title at the start
          </p>
          <p className="plan-note">
            Claude listens for the word, times every beat to it, and lays them out like this. Scroll to move the
            playhead.
          </p>
        </div>
        <Timeline />
      </section>

      <section className="storyboard">
        <div className="wrap">
          <h2>From raw clip to posted reel</h2>
          <ol className="steps">
            {STEPS.map((s, i) => (
              <li className="step" key={s.title}>
                <span className="step-n">{String(i + 1).padStart(2, '0')}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="install wrap" id="install">
        <div className="install-copy">
          <h2>Install</h2>
          <p>
            You need Claude Code. The skills install ffmpeg and Python for you the first time, about two minutes.
            Restart Claude Code after, then type <code>/</code> and the skills appear.
          </p>
          <p className="muted">
            Easier: open Claude Code and say “Install the skills from github.com/silpanandan2027-cell/shilpa-skills”.
          </p>
        </div>
        <Install />
      </section>

      <footer className="foot wrap">
        <span>MIT licence. Fonts under the SIL Open Font Licence.</span>
        <span>Watch every reel before you post it.</span>
      </footer>
    </div>
  );
}
