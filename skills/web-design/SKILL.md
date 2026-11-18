---
name: web-design
description: Use for ANY website, landing page, web app, UI, component, portfolio or HTML page work - building, redesigning, restyling, animating, cloning a look, or fixing how something looks. Runs the full design stack every time - Refero research, a brand DESIGN.md (Apple, Stripe, Linear and 80 more), React Bits components, GSAP scroll animation, Anime.js micro-animation, Impeccable anti-AI-slop review, Context7 for current library docs, Firecrawl to copy a site's vibe, and Chrome DevTools to test it in a real browser.
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

If an MCP server is missing or "needs authentication", tell the user once (run `/mcp` to sign in) and carry on with the other steps. Never stop the work because one tool is unavailable.

## 1. Research before building

- **Refero**: search Refero for 3 to 5 real products in the same category (for example "fintech dashboards", "coffee shop landing pages"). Note layout, type, colour and motion choices worth borrowing. Follow the `refero-design` skill if loaded.
- **Firecrawl**: when the user gives a site to copy or "make it like", scrape it with Firecrawl (markdown plus screenshot / branding). Pull its colours, fonts, spacing and section order. Copy the feel, never the logo, text or images.
- **Context7**: before writing code for any library (React, Next.js, Tailwind, GSAP, Anime.js, shadcn, Vite and so on), fetch its current docs with Context7 (resolve the library id first, then query its docs for the exact topic). Do not rely on memory for APIs.

## 2. Pick a design language (DESIGN.md)

- If the project has no `DESIGN.md`, pick the closest brand from `design-md/` (for example `apple.md`, `stripe.md`, `linear.app.md`, `vercel.md`, `notion.md`, `airbnb.md`, `spotify.md`, `nike.md`). List the files to see all 84. Ask the user only if no style was given and none fits.
- Copy it into the project root as `DESIGN.md` and follow its colours, type scale, spacing, radius, shadows and component rules exactly. It is a starting point: adapt the name and content to the user's brand.
- If the user has their own brand, run `/impeccable document` instead to write `DESIGN.md` from their code, or `/impeccable init` for a new project (writes `PRODUCT.md`).

## 3. Build with real components and motion

**React Bits** (React projects): find and add components through the `shadcn` MCP server. The project's `components.json` needs the registry:

```json
{ "registries": { "@react-bits": "https://reactbits.dev/r/{name}.json" } }
```

Install a component: `npx shadcn@latest add @react-bits/<Name>-TS-TW` (suffix: `JS` or `TS`, then `CSS` or `TW`). Good picks: `SplitText`, `BlurText`, `ShinyText`, `GradientText`, `CountUp`, `Aurora`, `Particles`, `SpotlightCard`, `Magnet`, `Dock`, `ScrollReveal`. Use one or two hero effects, not ten.

**GSAP** (scroll and page-level motion): `npm i gsap`. Every plugin is free, including ScrollTrigger, SplitText and ScrollSmoother.

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

Motion rules: GSAP for scroll and big moves, Anime.js for small ones, never both on the same element. Keep durations 150 to 600 ms for UI. Always respect `prefers-reduced-motion`. Check Context7 for the current API before using anything not shown here.

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
4. Scroll through to confirm GSAP / Anime.js animations fire and nothing overlaps.

Fix what you find and test again. Only call the work done after a clean pass, and show the user the screenshots.
