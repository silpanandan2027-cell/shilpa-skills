---
name: web-design
description: Use for ANY website, landing page, web app, UI, component, portfolio or HTML page work - building, redesigning, restyling, animating, cloning a look, or fixing how something looks. Runs the full design stack every time - Refero research, the frontend-design taste skill, a brand DESIGN.md (Apple, Stripe, Linear and 80 more), 21st.dev and React Bits components, Motion (Framer Motion) React animation, GSAP scroll animation, Anime.js micro-animation, Impeccable anti-AI-slop review, Context7 for current library docs, Firecrawl to copy a site's vibe, and Chrome DevTools to test it in a real browser.
---

# Web design stack

Use every step below for any website or UI work, unless the user says to skip one. The goal: a site that does not look AI-made.

| # | Tool | What it is | Where it comes from |
|---|---|---|---|
| 1 | Impeccable | anti-AI-slop design commands and detector | plugin `impeccable@impeccable` (`/impeccable ...`) |
| 2 | awesome-design-md | DESIGN.md files of 84 real brands | `design-md/` next to this file |
| 3 | React Bits | animated React components | `shadcn` MCP server, registry `@react-bits` |
| 4 | GSAP | scroll and timeline animation | npm `gsap` |
| 5 | Anime.js | micro-animations | npm `animejs` |
| 6 | Refero | real product designs to study | plugin `refero@refero` (MCP + skill) |
| 7 | Chrome DevTools | test the site in real Chrome | `chrome-devtools` MCP server |
| 8 | Firecrawl | read and copy another site's look | `firecrawl` MCP server |
| 9 | Context7 | up-to-date library docs | `context7` MCP server |
| 10 | Frontend Design | Anthropic's design-taste skill: aesthetic direction, type, colour, layout | plugin `frontend-design@claude-plugins-official` |
| 11 | 21st.dev | 10,000+ ready React/Tailwind blocks: heroes, pricing, testimonials, navbars, footers | plugin `21st@21st-dev` (MCP + `21st-ui` skill) |
| 12 | Motion (Framer Motion) | React animation: scroll reveals, stagger, hover, page transitions | npm `motion` |

If an MCP server is missing or "needs authentication", tell the user once (run `/mcp` to sign in; 21st.dev needs a free key from https://21st.dev/mcp in the `API_KEY_21ST` environment variable) and carry on with the other steps. Never stop the work because one tool is unavailable.

## 1. Research before building

- **Refero**: search Refero for 3 to 5 real products in the same category (for example "fintech dashboards", "coffee shop landing pages"). Note layout, type, colour and motion choices worth borrowing. Follow the `refero-design` skill if loaded.
- **Firecrawl**: when the user gives a site to copy or "make it like", scrape it with Firecrawl (markdown plus screenshot / branding). Pull its colours, fonts, spacing and section order. Copy the feel, never the logo, text or images.
- **Context7**: before writing code for any library (React, Next.js, Tailwind, GSAP, Anime.js, shadcn, Vite and so on), fetch its current docs with Context7 (resolve the library id first, then query its docs for the exact topic). Do not rely on memory for APIs.

- **Frontend Design**: read the `frontend-design` skill (from the plugin) before designing. Settle on the subject, the audience and one clear aesthetic direction first, then pick type, colour and layout that belong to that subject, not to a template.

## 2. Pick a design language (DESIGN.md)

- If the project has no `DESIGN.md`, pick the closest brand from `design-md/` (for example `apple.md`, `stripe.md`, `linear.app.md`, `vercel.md`, `notion.md`, `airbnb.md`, `spotify.md`, `nike.md`). List the files to see all 84. Ask the user only if no style was given and none fits.
- Copy it into the project root as `DESIGN.md` and follow its colours, type scale, spacing, radius, shadows and component rules exactly. It is a starting point: adapt the name and content to the user's brand.
- Whatever the source, the DESIGN.md must pin down a real system, and every component must use it:
  - **Type scale**: 5 to 7 fixed sizes from one ratio (for example 12, 14, 16, 20, 25, 31, 39, 49 px). No one-off font sizes.
  - **Spacing**: an 8 px grid (4, 8, 16, 24, 32, 48, 64, 96, 128). Every margin, padding and gap comes from it.
  - **Colour tokens**: primary, neutral (a full ramp), accent, plus success / warning / danger, as CSS variables or Tailwind theme tokens. No raw hex codes inside components.
  - **Component patterns**: buttons with default, hover, focus-visible, active, disabled and loading states; one card structure; form fields with label, hint and error states.
- If the user has their own brand, run `/impeccable document` instead to write `DESIGN.md` from their code, or `/impeccable init` for a new project (writes `PRODUCT.md`).

## 3. Build with real components and motion

**21st.dev** (React projects, the first place to look for whole sections: hero, features, pricing, testimonials, social proof, FAQ, navbar, footer): follow the `21st-ui` skill. Use the 21st MCP `search` tool, show the user the best 1 to 3 matches when the choice is not obvious, fetch the chosen one with `get_component`, and install it the way the result says (usually a shadcn registry add). Then make it yours: swap its colours, fonts, spacing and radius for the DESIGN.md tokens, replace the placeholder copy with the real copy, and add Motion entrance animations. The free plan allows 2 component installs a day, so pick carefully. Without a 21st key, browse https://21st.dev, and the user can paste a component's code for you to integrate.

**React Bits** (React projects): find and add components through the `shadcn` MCP server. The project's `components.json` needs the registry:

```json
{ "registries": { "@react-bits": "https://reactbits.dev/r/{name}.json" } }
```

Install a component: `npx shadcn@latest add @react-bits/<Name>-TS-TW` (suffix: `JS` or `TS`, then `CSS` or `TW`). Good picks: `SplitText`, `BlurText`, `ShinyText`, `GradientText`, `CountUp`, `Aurora`, `Particles`, `SpotlightCard`, `Magnet`, `Dock`, `ScrollReveal`. Use one or two hero effects, not ten.

**Motion (formerly Framer Motion)** (the default for React: scroll-triggered fades, staggered reveals, hover and tap feedback, layout and page transitions): `npm i motion`. The old `framer-motion` package is the same library and still works in projects that already use it.

```jsx
import { motion } from "motion/react";
const list = { show: { transition: { staggerChildren: 0.08 } } };
const item = { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0 } };

<motion.ul variants={list} initial="hidden" whileInView="show" viewport={{ once: true, amount: 0.3 }}>
  {features.map(f => <motion.li key={f.id} variants={item}>{f.title}</motion.li>)}
</motion.ul>
<motion.button whileHover={{ y: -2 }} whileTap={{ scale: 0.97 }} transition={{ type: "spring", stiffness: 400, damping: 30 }} />
```

Wrap the app in `<MotionConfig reducedMotion="user">` so people who turn motion off get none. In the Next.js App Router, Motion components go in `"use client"` files. For a smaller bundle use `LazyMotion` with `m` components.

**GSAP** (scroll-scrubbed timelines, pinning and big page-level moves): `npm i gsap`. Every plugin is free, including ScrollTrigger, SplitText and ScrollSmoother.

```js
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
gsap.registerPlugin(ScrollTrigger);
gsap.from(".section", { y: 60, opacity: 0, stagger: 0.15,
  scrollTrigger: { trigger: ".section", start: "top 80%" } });
```

In React use `@gsap/react` and `useGSAP()` so animations clean up. Plain HTML: `https://cdn.jsdelivr.net/npm/gsap@3.15.1/dist/gsap.min.js` and `.../dist/ScrollTrigger.min.js`.

**Anime.js** (small UI motion: buttons, icons, hovers, counters, loaders): `npm i animejs` (v4 API).

```js
import { animate, stagger } from "animejs";
animate(".card", { y: [20, 0], opacity: [0, 1], delay: stagger(80), ease: "outExpo" });
```

Plain HTML: `https://cdn.jsdelivr.net/npm/animejs@4.5.0/dist/bundles/anime.umd.min.js` (global `anime`).

Motion rules: in React, Motion for entrances, reveals, hover and page transitions; GSAP only for scroll-scrubbed or pinned timelines; Anime.js for small motion in plain HTML or non-React parts. Never two libraries on the same element. Keep durations 150 to 600 ms for UI. Always respect `prefers-reduced-motion`. Check Context7 for the current API before using anything not shown here.

## 4. Remove the AI look (Impeccable)

After building each page or section, run Impeccable on it:

- `/impeccable critique <target>` for a scored UX review, then fix the top items.
- `/impeccable audit <target>` for accessibility, performance, theming and responsiveness.
- `/impeccable polish <target>` as the final pass.
- Steer with `bolder`, `quieter`, `typeset`, `layout`, `colorize`, `animate`, `delight` when something feels generic.

Avoid the classic tells: Inter everywhere, purple-to-blue gradients, cards inside cards, grey text on colour, an icon tile above every heading, everything centred.

## 5. Test in real Chrome (Chrome DevTools)

Start the dev server, then with the Chrome DevTools MCP:

1. Open the page, take screenshots at phone (390 px) and desktop (1440 px) width.
2. Read the console and network: fix every error and failed request.
3. Run a performance trace and fix slow LCP or layout shift.
4. Scroll through to confirm Motion / GSAP / Anime.js animations fire and nothing overlaps.
5. Run a Lighthouse audit (performance, accessibility, best practices, SEO) and aim for 90+ on performance: lazy-load images below the fold, self-host or `font-display: swap` fonts, and keep JavaScript small.

Fix what you find and test again. Only call the work done after a clean pass, and show the user the screenshots.
