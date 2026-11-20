"""Writes the two "look" scenes (girl cut out over her bedroom plate, alive with sway, breath,
parallax, handheld camera and flash pose-switches). Both scenes share one template so they stay
consistent; edit the generated HTML in compositions/ or change this file and run it again.

Usage: python3 build_scenes.py
"""
from pathlib import Path

W, H = 2160, 3840


def look_scene(sid, duration, sequence, title, title_in, room, scale, lift):
    """sequence: list of (pose, start_sec) — the pose shown from that time on.
    room: background plate in assets/img; scale/lift place her feet on its floor (lift in px, 4K)."""
    first = sequence[0][0]
    title_tween = (f'    tl.fromTo("#{sid}-title", {{ opacity: 0, filter: "blur(18px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.35, ease: "power4.out" }}, {title_in});' if title else "    // no title in this scene: the outfit is the subject")
    title_html = (f'          <div id="{sid}-title" class="clip" data-start="{title_in}" data-duration="{duration - title_in:.2f}" data-layout-allow-overlap>{title}</div>\n' if title else "")
    poses = ["pose1", "pose2"]
    plates = f'          <img id="{sid}-plate" class="{sid}-plate" src="assets/img/{room}.jpg" alt="" />'
    girls = "\n".join(
        f'              <img id="{sid}-girl-{p}" class="{sid}-girl" src="assets/cut/{p}-{room}.webp" alt="" style="opacity:{1 if p == first else 0}" />'
        for p in poses
    )
    switches = []
    for pose, at in sequence[1:]:
        other = [p for p in poses if p != pose][0]
        switches.append(f"""
    // pose switch on the beat: white flash, swap at its peak, small punch-in that settles
    tl.fromTo("#{sid}-flash", {{ opacity: 0 }}, {{ opacity: 0.85, duration: 0.07, ease: "power2.in" }}, {at - 0.07:.2f});
    tl.fromTo("#{sid}-flash", {{ opacity: 0.85 }}, {{ opacity: 0, duration: 0.22, ease: "power2.out", immediateRender: false }}, {at:.2f});
    tl.set("#{sid}-girl-{pose}", {{ opacity: 1 }}, {at:.2f});
    tl.set("#{sid}-girl-{other}", {{ opacity: 0 }}, {at:.2f});
    tl.fromTo("#{sid}-punch", {{ scale: 1.045 }}, {{ scale: 1, duration: 0.45, ease: "expo.out", immediateRender: false }}, {at:.2f});""")
    sway_n = max(1, int(duration / 1.3))
    breath_n = max(1, int(duration / 1.7))
    hand_x = max(1, int(duration / 1.9))
    hand_y = max(1, int(duration / 2.6))
    return f"""<template>
  <style>
    @font-face {{ font-family: "Great Vibes"; src: url("assets/fonts/GreatVibes-Regular.ttf") format("truetype"); font-display: block; }}
    #root {{ position: absolute; inset: 0; overflow: hidden; background: #f4ece6; }}
    #{sid}-cam, #{sid}-punch, #{sid}-push, #{sid}-rig, #{sid}-sway, #{sid}-breath {{ position: absolute; inset: 0; }}
    #{sid}-cam {{ inset: -3%; }}
    .{sid}-plate, .{sid}-girl {{ position: absolute; left: 0; top: 0; width: 100%; height: 100%; object-fit: cover; }}
    #{sid}-place {{ position: absolute; inset: 0; transform-origin: 50% 100%; transform: translateY(-{lift}px) scale({scale}); }}
    #{sid}-shadow {{ position: absolute; left: 30%; right: 30%; bottom: -40px; height: 170px; border-radius: 50%;
      background: radial-gradient(ellipse at center, rgba(40, 22, 14, 0.42), rgba(40, 22, 14, 0) 70%); }}
    #{sid}-sway {{ transform-origin: 50% 96%; }}
    #{sid}-breath {{ transform-origin: 50% 96%; }}
    #{sid}-title {{
      position: absolute; left: 0; right: 0; top: 900px; text-align: center;
      font-family: "Great Vibes", cursive; font-size: 340px; line-height: 1; color: #d6246e;
      -webkit-text-stroke: 6px #ffffff; paint-order: stroke fill;
      text-shadow: 0 0 60px rgba(255, 255, 255, 0.9), 0 0 120px rgba(255, 140, 190, 0.6);
      white-space: nowrap;
    }}
    #{sid}-flash {{ position: absolute; inset: 0; background: #fff8fb; opacity: 0; }}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="{W}" data-height="{H}" data-layout-allow-overflow>
    <div id="{sid}-cam">
      <div id="{sid}-punch">
        <div id="{sid}-push">
{plates}
{title_html}          <div id="{sid}-rig" data-layout-allow-occlusion>
            <div id="{sid}-place">
            <div id="{sid}-shadow"></div>
            <div id="{sid}-sway">
              <div id="{sid}-breath">
{girls}
              </div>
            </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div id="{sid}-flash"></div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.to({{}}, {{ duration: {duration} }}, 0);
    tl.set("#{sid}-flash", {{ opacity: 0 }}, 0);
    // depth parallax: the room pushes in slowly while she drifts the other way, so she separates from it
    tl.fromTo("#{sid}-push", {{ scale: 1.03, x: 0 }}, {{ scale: 1.1, x: -26, duration: {duration}, ease: "power1.inOut" }}, 0);
    tl.fromTo("#{sid}-rig", {{ x: -18, y: 6 }}, {{ x: 34, y: -8, duration: {duration}, ease: "power1.inOut" }}, 0);
    // idle acting: weight shifting hip to hip, and breathing
    tl.fromTo("#{sid}-sway", {{ rotation: -0.9 }}, {{ rotation: 0.9, duration: 1.3, ease: "sine.inOut", repeat: {sway_n}, yoyo: true }}, 0);
    tl.fromTo("#{sid}-breath", {{ scaleY: 1, scaleX: 1 }}, {{ scaleY: 1.007, scaleX: 0.998, duration: 0.85, ease: "sine.inOut", repeat: {breath_n * 2}, yoyo: true }}, 0);
    // handheld phone camera
    tl.fromTo("#{sid}-cam", {{ x: -12 }}, {{ x: 12, duration: 1.9, ease: "sine.inOut", repeat: {hand_x}, yoyo: true }}, 0);
    tl.fromTo("#{sid}-cam", {{ y: -9, rotation: -0.25 }}, {{ y: 9, rotation: 0.25, duration: 2.6, ease: "sine.inOut", repeat: {hand_y}, yoyo: true }}, 0);
    // title behind her: blurs in as one line, then holds still
{title_tween}
    // she arrives slightly large and settles (match from the previous scene's push)
    tl.fromTo("#{sid}-punch", {{ scale: 1.06 }}, {{ scale: 1, duration: 0.6, ease: "expo.out" }}, 0);
{"".join(switches)}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""


out = Path(__file__).parent / "compositions"
(out / "look.html").write_text(look_scene("look", 5.0, [("pose1", 0), ("pose2", 1.6), ("pose1", 3.25)], None, 0, "room1", 0.86, 190))
(out / "finale.html").write_text(look_scene("finale", 3.4, [("pose2", 0), ("pose1", 1.5)], None, 0, "room2", 0.93, 80))
print("wrote look.html, finale.html")
