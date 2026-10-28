#!/usr/bin/env bash
# Generates every raster asset used by showcase.svg with the local FLUX.2-klein model.
# Each asset: 512px raw -> transparent, monocolor (#7fe3ff) PNG via make_asset.py.
set -euo pipefail
cd "$(dirname "$0")"
GEN="python3 ../../scripts/generate_asset.py"
C="#7fe3ff"

gen() { # name size prompt
  echo "=== $1 ==="
  $GEN "$3" "assets/$1.png" --force-flux2 --mono "$C" --size "$2"
}

gen notes   192 "open spiral notebook with handwritten lines and a magnifying glass, simple icon"
gen layout  192 "wireframe of a page layout grid with rectangular panels and boxes, simple icon"
gen pen     192 "vector pen nib tool drawing a bezier curve with anchor points, simple icon"
gen chip    192 "AI microchip with neural network nodes on top, simple icon"
gen aperture 192 "camera lens aperture shutter blades, simple icon"
gen eye     192 "magnifying glass with a check mark inside, simple icon"
gen hero    512 "isometric designer workstation, large monitor showing charts and flow diagrams, desk with stylus tablet, detailed line drawing"
gen circuit 512 "abstract flowing circuit board traces and connection nodes, sparse line pattern"
echo "ALL DONE"
