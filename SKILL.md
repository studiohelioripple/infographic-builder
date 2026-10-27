---
name: infographic-builder
description: Creates infographics and explanatory diagrams (flow graphs, comparisons, charts) by combining hand-authored SVG layout with optional local image-generation models (Flux/Stable Diffusion via mflux, DiffusionKit, ComfyUI, Ollama-adjacent tools) for background art. Use when the user asks for an infographic, mechanism diagram, process graph, or explanatory image, especially when hosted image APIs are unavailable.
---

# Infographic Builder

Principle: **SVG owns structure and text; local models own only decorative imagery.** Diffusion models garble small text, so never ask them to render labels, numbers, or charts.

## Workflow

1. **Extract content first.** Read the source material (docs, notes). Pull out: the process steps (3-8), 2-4 hard numbers, one comparison (before/after, us/them), and one takeaway. Don't invent figures; cite only what the sources state.
2. **Pick a layout** from `templates/` (or adapt):
   - `flow_snake.svg`: numbered step flow, 4 across then snake back, + chart panel + comparison + footer strip (1920x1080).
   - Other patterns: vertical timeline, hub-and-spoke, funnel, 2x2 matrix, layered stack.
3. **Write SVG** (default canvas 1920x1080, 16:9). Rules below.
4. **Optional local-model assets**: see "Local models". Generate small transparent PNG assets (icons/illustrations) and place them in the SVG with `<image>`, or skip.
5. **Render to PNG** with `scripts/render.sh in.svg out.png [width] [height]`.
6. **Verify visually**: open the PNG with the image viewer; check for text overflow, overlap of icons and text, clipped edges. Fix and re-render. Do this at least once.
7. Deliver both `.svg` (editable) and `.png`, saved in the user's project folder (not tmp).

## SVG design rules

- Use `viewBox` + explicit `width/height`; grid-align on 40px multiples; margins 80px.
- Palette: max 1 accent + 1 neutral text + 1 muted text on a dark or light base. Default: bg `#0a1224`, accent `#7fe3ff`, text `#e8f6ff`, muted `#9fb8cc`.
- Fonts: `Helvetica, Arial, sans-serif` (always available to the renderer). Title 52, node heading 26, body 20, min 16.
- Estimate text width as about 0.55 x font-size x characters; keep each line inside its box with 30px padding. Keep lines under about 28 chars at size 20 in 380px boxes. Shorten text rather than shrinking fonts.
- Reserve a clear icon zone (top-right 80x80 of each box); text must not run into it.
- Arrows: define a `<marker>` and use `marker-end`. Number badges: circles on box corners.
- Charts: draw bars/lines directly as `<rect>`/`<path>` with labels; compute heights from data (scale linearly, label values).
- Escape `&` as `&amp;` and `<` as `&lt;` in text.
- **Icons must be strictly monocolor** (user global rule): single stroke color, line style, no multi-tone fills. Draw simple paths (document, cube, graph, truck, factory, gear, shield) or use a monochrome icon set (Material Symbols / Lucide / Tabler SVG paths, inlined and recolored to the accent).
- Apply the same monocolor rule to any generated raster art: request "single-color line art / monochrome duotone", and desaturate if needed.

## Rendering (macOS)

Preferred order (handled by `scripts/render.sh`):
1. `rsvg-convert` (if installed).
2. Headless Chrome: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --hide-scrollbars --window-size=W,H --screenshot=out.png file:///abs/in.svg`
3. `inkscape --export-type=png` or Python `cairosvg`.

Do NOT use `qlmanage -t`: it outputs a square, cropped thumbnail.

## Local models (optional background/illustration art)

First detect what is available, then pick:

```bash
which mflux-generate mflux-generate-flux2 diffusionkit-cli ollama comfy 2>/dev/null
python3 -c "import diffusers, torch; print('diffusers ok')" 2>&1 | tail -1
ls ~/ComfyUI ~/.cache/huggingface/hub 2>/dev/null | head
ollama list 2>/dev/null
```

| Tool | Example |
|---|---|
| mflux (Apple Silicon FLUX) | `mflux-generate --model schnell --prompt "..." --steps 4 --width 1920 --height 1080 --output bg.png` |
| DiffusionKit | `diffusionkit-cli --prompt "..." --model-version argmaxinc/mlx-stable-diffusion-3-medium --output-path bg.png` |
| diffusers (MPS) | `StableDiffusionXLPipeline.from_pretrained(...).to("mps")` |
| ComfyUI | POST a workflow JSON to `http://127.0.0.1:8188/prompt` |

Ollama text models can help draft/condense copy and even write SVG, but they don't generate images. If no local image model is installed, say so, offer to install one (`pip install mflux`, needs user approval), and otherwise produce a pure-SVG infographic. Don't silently fall back to a hosted API; if one fails (e.g. regional block), use SVG.

### Output format: small transparent PNG assets (not full-canvas images)

Local models generate **individual small assets** (icons, illustrations, textures, 128-512 px), each a **transparent-background PNG**, which are then composited into the SVG. Never generate the whole infographic as one image.

1. Generate one asset per image on a **plain flat background** (pure white or black), square, 512x512 (or 768) for quality. Prompt pattern:
   `"single isometric modular building block, monochrome cyan line art, centered, plain white background, no text, no shadow, no gradient, flat"`. Always include "no text" and "plain background".
2. Convert to a small transparent PNG:
   `python3 scripts/make_asset.py raw.png assets/block.png --size 256 --mono "#7fe3ff"`
   (removes background via `rembg` if installed, otherwise chroma-key from the corner color; `--mono` flattens to one color per the monocolor rule; trims, resizes, quantizes; also runs `pngquant` if present). Needs `pip install pillow` (optional `rembg`).
3. Keep each file small: target under 50 KB, `--size 128-256` for icons, up to 512 for hero art. Keep assets in an `assets/` folder next to the SVG.
4. Embed in the SVG at the intended display size:
   `<image href="assets/block.png" x="1760" y="230" width="72" height="72"/>`
   For a self-contained SVG, inline as base64: `href="data:image/png;base64,..."` (small files make this practical).
5. Because the assets are transparent, they can sit on any panel color, be layered, recolored, or used with low opacity (0.15-0.35) as texture behind text.

If no local image model is available, draw the assets as inline SVG paths instead (still transparent and monocolor).

## Quality checklist

- [ ] One title, one subtitle stating what the graphic explains
- [ ] Every number traceable to a source
- [ ] Reading order is obvious (numbered badges + arrows)
- [ ] No text overflow, no icon/text overlap, nothing cut at edges
- [ ] All icons monocolor; palette limited
- [ ] Raster assets are transparent PNGs, small (<50 KB typical), no baked-in text
- [ ] SVG and PNG both saved in the project folder
