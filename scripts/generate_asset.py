#!/usr/bin/env python3
"""Asset Generator with Intelligent Router: Apple Intelligence -> FLUX-2.

Rules & Logic:
1. Evaluates prompt precision requirements:
   - If the subject requires high precision (domain-specific diagrams, technical
     mechanisms, exact architecture, intricate parts) or --precision high:
     Routes directly to FLUX-2 (via `flux2` / `mflux-generate-flux2`).
   - For general conceptual icons, stylistic motifs, or standard symbols:
     First attempts Apple Intelligence (via macOS Image Playground / Shortcuts).
     If Apple Intelligence is unavailable, fails, or cannot meet precision needs:
     Falls back to FLUX-2.
2. Post-processing:
   - Automatically runs `make_asset.py` to remove background, enforce the
     strict MONOCOLOR rule (--mono <color>), trim, resize, and optimize PNG.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HIGH_PRECISION_KEYWORDS = [
    "precise", "schematic", "mechanism", "internal", "blueprint", "diagram",
    "architecture", "hardware", "circuit", "cross-section", "technical",
    "engine", "processor", "pipeline", "distributed", "topology", "detailed",
    "isometric specification", "component-level"
]

def determine_precision(prompt: str, user_precision: str = "auto") -> bool:
    """Return True if high precision is required (needs FLUX-2)."""
    if user_precision == "high":
        return True
    if user_precision in ("low", "standard"):
        return False
    
    prompt_lower = prompt.lower()
    for kw in HIGH_PRECISION_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", prompt_lower):
            return True
    return False

def try_apple_intelligence(prompt: str, raw_out: str) -> bool:
    """Attempt generation via Apple Intelligence (Shortcuts / Image Playground)."""
    # Check if a dedicated Shortcuts action or workflow exists
    if not shutil.which("shortcuts"):
        return False

    candidate_shortcuts = [
        "Generate Image",
        "Image Playground",
        "Apple Intelligence Image",
        "Create Image"
    ]
    
    available_shortcuts = []
    try:
        res = subprocess.run(["shortcuts", "list"], capture_output=True, text=True, check=True)
        available_shortcuts = [s.strip() for s in res.stdout.splitlines() if s.strip()]
    except Exception:
        pass

    matching_shortcut = next((s for s in candidate_shortcuts if s in available_shortcuts), None)
    if not matching_shortcut:
        return False

    print(f"[*] Trying Apple Intelligence via Shortcut '{matching_shortcut}'...")
    try:
        # Run shortcut with prompt as input
        p_res = subprocess.run(
            ["shortcuts", "run", matching_shortcut, "-i", prompt, "-o", raw_out],
            capture_output=True,
            text=True,
            timeout=45
        )
        if p_res.returncode == 0 and os.path.exists(raw_out) and os.path.getsize(raw_out) > 1000:
            print("[+] Successfully generated asset with Apple Intelligence.")
            return True
    except Exception as e:
        print(f"[-] Apple Intelligence failed or timed out: {e}")

    return False

def generate_flux2(prompt: str, raw_out: str, size: int = 512) -> bool:
    """Generate image using local FLUX-2 Klein model via flux2 CLI or mflux."""
    flux2_bin = shutil.which("flux2") or shutil.which("f2") or os.path.expanduser("~/bin/flux2")
    mflux_bin = shutil.which("mflux-generate-flux2") or shutil.which("mflux-generate")

    # Enforce flat background and monocolor-friendly output
    enriched_prompt = f"{prompt}, centered, clean flat plain white background, high contrast, monochrome line art, no text, no frame"

    if flux2_bin and os.path.exists(flux2_bin) and os.access(flux2_bin, os.X_OK):
        print(f"[*] Generating with FLUX-2 ({flux2_bin})...")
        cmd = [
            flux2_bin,
            enriched_prompt,
            "--icon",
            "--no-open",
            "-o", raw_out,
            "-w", str(size),
            "-h", str(size),
            "-s", "4"
        ]
        res = subprocess.run(cmd)
        if res.returncode == 0 and os.path.exists(raw_out):
            return True

    if mflux_bin:
        print(f"[*] Generating with mflux ({mflux_bin})...")
        cmd = [
            mflux_bin,
            "--model", "flux2-klein-4b" if "flux2" in mflux_bin else "schnell",
            "--prompt", enriched_prompt,
            "--width", str(size),
            "--height", str(size),
            "--steps", "4",
            "--output", raw_out
        ]
        res = subprocess.run(cmd)
        if res.returncode == 0 and os.path.exists(raw_out):
            return True

    return False

def main():
    parser = argparse.ArgumentParser(description="Generate transparent monocolor SVG assets with Apple Intelligence / FLUX-2")
    parser.add_argument("prompt", help="Visual concept description")
    parser.add_argument("output", help="Final destination PNG path")
    parser.add_argument("--precision", choices=["auto", "high", "standard"], default="auto",
                        help="auto: detect if high precision needed; high: route to FLUX-2; standard: try Apple Intelligence first")
    parser.add_argument("--mono", default="#00A389", help="Monocolor hex code to enforce (default: Gemini notebook teal #00A389)")
    parser.add_argument("--size", type=int, default=256, help="Target asset dimension in px (default 256)")
    parser.add_argument("--force-flux2", action="store_true", help="Bypass Apple Intelligence and use FLUX-2 directly")
    args = parser.parse_args()

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_png = os.path.join(tmpdir, "raw.png")
        is_high_precision = determine_precision(args.prompt, args.precision)
        generated = False

        if args.force_flux2 or is_high_precision:
            print(f"[i] High precision requirement determined for prompt: '{args.prompt}' -> Selecting FLUX-2.")
            generated = generate_flux2(args.prompt, raw_png, size=512)
        else:
            print(f"[i] Standard precision concept: '{args.prompt}' -> Trying Apple Intelligence first...")
            generated = try_apple_intelligence(args.prompt, raw_png)
            if not generated:
                print("[i] Apple Intelligence unavailable or insufficient -> Falling back to FLUX-2.")
                generated = generate_flux2(args.prompt, raw_png, size=512)

        if not generated or not os.path.exists(raw_png):
            print(f"[-] Error: Image generation failed for prompt: {args.prompt}", file=sys.stderr)
            sys.exit(1)

        # Post-process into monocolor transparent asset via make_asset.py
        script_dir = Path(__file__).resolve().parent
        make_asset_py = script_dir / "make_asset.py"
        
        print(f"[*] Post-processing into monocolor ({args.mono}) transparent asset...")
        post_cmd = [
            sys.executable,
            str(make_asset_py),
            raw_png,
            str(out_path),
            "--size", str(args.size),
            "--mono", args.mono,
            "--bg", "auto"
        ]
        res = subprocess.run(post_cmd)
        if res.returncode != 0:
            print("[-] Error running make_asset.py", file=sys.stderr)
            sys.exit(res.returncode)

    print(f"[✓] Asset successfully created: {out_path} ({args.size}x{args.size}, monocolor: {args.mono})")

if __name__ == "__main__":
    main()
