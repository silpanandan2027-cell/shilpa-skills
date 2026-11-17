#!/usr/bin/env bash
# Cuts the 3 Shorts from the full episode as vertical 9:16 (1080x1920) videos
# with burned-in captions.
#
# Usage:  ./make_clips.sh /path/to/full-episode.mp4
# Needs:  ffmpeg (with libass) and python3
set -euo pipefail

SRC="${1:?Give the path to the downloaded full episode video}"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/output"
mkdir -p "$OUT"

# Caption look: big bold white text, thick black outline, lower-middle of the frame.
STYLE="FontName=DejaVu Sans,Bold=1,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,Alignment=2,MarginV=70"

python3 - "$HERE/clips.json" <<'PY' > "$OUT/.list"
import json,sys
for c in json.load(open(sys.argv[1])):
    print(c["name"], c["start"], c["end"] - c["start"])
PY

while read -r NAME START DUR; do
  echo ">> $NAME  (start ${START}s, ${DUR}s)"
  # Blurred, zoomed copy fills the 9:16 frame; the full 16:9 picture sits in the middle;
  # captions are burned on top.
  ffmpeg -hide_banner -loglevel error -y \
    -ss "$START" -t "$DUR" -i "$SRC" \
    -filter_complex "\
[0:v]split=2[bg][fg]; \
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness=-0.15[bgb]; \
[fg]scale=1080:-2[fgs]; \
[bgb][fgs]overlay=(W-w)/2:(H-h)/2-120,subtitles='$HERE/captions/$NAME.srt':force_style='$STYLE'[v]" \
    -map "[v]" -map 0:a? -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
    -c:a aac -b:a 160k -movflags +faststart "$OUT/$NAME.mp4" </dev/null
done < "$OUT/.list"
rm -f "$OUT/.list"
echo "Done. Shorts are in: $OUT"
