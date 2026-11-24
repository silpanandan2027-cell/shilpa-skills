#!/usr/bin/env python3
"""Steps 1 and 7: pick today's topic and log it so it never repeats.

    python3 topics.py next PLAN.txt          # first topic in the plan that is not in the log
    python3 topics.py seen "Topic"           # exit 1 if the topic was already used
    python3 topics.py log "Topic" --date 2026-11-25 --post URL --guide URL

The plan is plain text: one topic per line, or a markdown list / table whose first cell is
the topic. Lines starting with # are headings and are skipped. The log is
content/topic-log.md, one row per reel.
"""
import argparse, datetime as dt, os, pathlib, re, sys

ROOT = pathlib.Path(os.environ.get("REEL_HOME", ".")).resolve()  # the shilpa-skills repo
LOG = ROOT / "content" / "topic-log.md"
HEAD = "| Date | Topic | Post | Guide |\n|---|---|---|---|\n"


def norm(s):
    return re.sub(r"[^\wഀ-ൿ]+", " ", s.lower()).strip()


def used():
    if not LOG.exists():
        return set()
    rows = [l.split("|") for l in LOG.read_text(encoding="utf-8").splitlines() if l.startswith("| 2")]
    return {norm(r[2]) for r in rows if len(r) > 2}


def plan_topics(path):
    out = []
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or set(s) <= set("|-: "):
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if any(c.lower() in ("topic", "title", "idea", "topics") for c in cells):
                continue  # header row
            s = next((c for c in cells if c and not re.fullmatch(r"[\d/.\- ]+|(day|week) ?\d*|done|✅", c, re.I)), "")
        s = re.sub(r"^([-*+]|\d+[.)]|\[[ x]\])\s*", "", s).strip()
        if s:
            out.append(s)
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("next"); n.add_argument("plan")
    s = sub.add_parser("seen"); s.add_argument("topic")
    l = sub.add_parser("log"); l.add_argument("topic")
    l.add_argument("--date", default=dt.date.today().isoformat()); l.add_argument("--post", default="")
    l.add_argument("--guide", default="")
    a = ap.parse_args()
    if a.cmd == "next":
        u = used()
        for t in plan_topics(a.plan):
            if norm(t) not in u:
                print(t); return
        sys.exit("Every topic in the plan has been used. Add new topics to the content plan.")
    if a.cmd == "seen":
        sys.exit(1 if norm(a.topic) in used() else 0)
    if norm(a.topic) in used():
        sys.exit(f"Already logged: {a.topic}")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    text = LOG.read_text(encoding="utf-8") if LOG.exists() else "# Topic log\n\nEvery reel made, so no topic repeats.\n\n" + HEAD
    LOG.write_text(text.rstrip("\n") + f"\n| {a.date} | {a.topic.replace('|', '/')} | {a.post} | {a.guide} |\n", encoding="utf-8")
    print("logged", a.topic)


if __name__ == "__main__":
    main()
