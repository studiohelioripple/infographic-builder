#!/usr/bin/env bash
# Render an SVG to PNG at exact size. Usage: render.sh in.svg out.png [width=1920] [height=1080]
set -euo pipefail
IN="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="$2"; W="${3:-1920}"; H="${4:-1080}"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

if command -v rsvg-convert >/dev/null; then
  rsvg-convert -w "$W" -h "$H" "$IN" -o "$OUT"
elif [ -x "$CHROME" ]; then
  "$CHROME" --headless --disable-gpu --hide-scrollbars --window-size="$W,$H" \
    --screenshot="$OUT" "file://$IN" >/dev/null 2>&1
elif command -v inkscape >/dev/null; then
  inkscape "$IN" --export-type=png --export-filename="$OUT" -w "$W" -h "$H"
elif python3 -c "import cairosvg" 2>/dev/null; then
  python3 -c "import cairosvg,sys; cairosvg.svg2png(url=sys.argv[1], write_to=sys.argv[2], output_width=int(sys.argv[3]), output_height=int(sys.argv[4]))" "$IN" "$OUT" "$W" "$H"
else
  echo "No SVG renderer found (rsvg-convert, Chrome, inkscape, cairosvg)." >&2; exit 1
fi
echo "Wrote $OUT"
