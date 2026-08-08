"""Reproducible logo processing pipeline for Cinqic Calculator.

Source of truth: the attached Cinqic Calculator logo PNG (calculator emblem
+ clover, plus the "CINQIC / Calculator" wordmark). This script does NOT
redraw, regenerate, or alter the artwork itself -- it only crops, pads,
centers, and re-exports the existing pixels at the sizes each platform
needs.

Usage:
    python scripts/process_logo.py [--source PATH] [--out-dir DIR]

Outputs (all under --out-dir, default: repo root):
    assets/branding/cinqic-calculator-horizontal.png   full logo, trimmed
    assets/branding/cinqic-calculator-emblem-master.png  square emblem, 1024px
    assets/icons/cinqic-calculator.ico                 Windows icon (multi-size)
    assets/icons/cinqic-calculator.png                 Windows/general 256px PNG
    android/assets/icon/icon_foreground.png            adaptive icon foreground
    android/assets/icon/icon_background.png            adaptive icon background
    android/assets/icon/icon_legacy_<density>.png       legacy launcher pngs
    android/assets/icon/presplash.png                  splash screen image
    android/assets/icon/contact_sheet.png               approval contact sheet

Also runs a verification pass (dimensions, alpha, centering, non-empty
pixels, aspect ratio) and prints PASS/FAIL for each generated asset.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

DEFAULT_SOURCE = r"C:\Users\Blessom\Pictures\Cinqic Calculator Logo.png"

# Background plate color behind the emblem on opaque surfaces (adaptive
# icon background, legacy launcher icon, presplash) -- matches the app's
# dark theme background (see src/cinqic_calculator/constants.py COLOR_BACKGROUND).
BACKGROUND_COLOR = (10, 10, 10, 255)  # #0A0A0A

# Alpha threshold used to find the true bounding box of drawn content.
# The source PNG carries a very faint (alpha 1-9) ambient gradient across
# almost the whole canvas; anything below this threshold is treated as
# "empty" so it doesn't inflate the crop.
CONTENT_ALPHA_THRESHOLD = 25

LEGACY_DENSITIES = {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}

CONTACT_SHEET_SIZES = [48, 72, 96, 144, 192]


def strip_unpremultiplied_color_noise(im: Image.Image) -> Image.Image:
    """Zero out RGB wherever alpha is 0.

    The source PNG has leftover (unpremultiplied) color data under fully
    transparent pixels -- harmless to compositing math, but some simple
    renderers show raw RGB regardless of alpha, which looks like a gray/
    green wash "ghost" of the design across the whole canvas. Forcing RGB
    to black under zero alpha makes every consumer see true transparency,
    with no visible effect on any actually-visible (alpha > 0) pixel.
    """
    arr = np.array(im.convert("RGBA"))
    transparent = arr[:, :, 3] == 0
    arr[transparent] = [0, 0, 0, 0]
    return Image.fromarray(arr, mode="RGBA")


def clean_ambient_wash(im: Image.Image, low: int = 12, high: int = 42) -> Image.Image:
    """Strip the faint (alpha ~1-40) ambient vignette/glow the source PNG
    carries across most of its canvas, leaving true transparency outside
    the actual logo artwork.

    Alpha below `low` is zeroed; alpha above `high` is kept as-is; the
    band between the two is smoothly ramped (not a hard cutoff) so real
    soft edges (e.g. the drop shadow under the emblem) don't get a visible
    ring where the cleanup kicks in.
    """
    arr = np.array(im.convert("RGBA")).astype(np.float64)
    alpha = arr[:, :, 3]
    ramp = np.clip((alpha - low) / (high - low), 0.0, 1.0)
    arr[:, :, 3] = alpha * ramp
    return Image.fromarray(arr.astype(np.uint8), mode="RGBA")


def content_bbox(im: Image.Image, threshold: int = CONTENT_ALPHA_THRESHOLD) -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) of pixels with alpha > threshold."""
    arr = np.array(im.convert("RGBA"))
    alpha = arr[:, :, 3]
    mask = alpha > threshold
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        raise ValueError("No non-transparent content found above threshold")
    return int(cols.min()), int(rows.min()), int(cols.max()) + 1, int(rows.max()) + 1


def find_emblem_bbox(im: Image.Image) -> tuple[int, int, int, int]:
    """Locate the square calculator+clover emblem at the left of the logo.

    The horizontal logo is [emblem] [gap] [CINQIC wordmark] [gap] [Calculator
    subtitle]. We find contiguous column runs of content and take the
    first (leftmost) run, which is the emblem -- verified below to be
    roughly square, as the calculator emblem is.
    """
    arr = np.array(im.convert("RGBA"))
    alpha = arr[:, :, 3]
    mask = alpha > CONTENT_ALPHA_THRESHOLD
    col_has = mask.any(axis=0)
    cols = np.where(col_has)[0]

    gap_threshold = 15
    segments = []
    run_start = cols[0]
    prev = cols[0]
    for c in cols[1:]:
        if c - prev > gap_threshold:
            segments.append((run_start, prev))
            run_start = c
        prev = c
    segments.append((run_start, prev))

    x0, x1 = segments[0]
    sub_mask = mask[:, x0 : x1 + 1]
    rows = np.where(sub_mask.any(axis=1))[0]
    y0, y1 = int(rows.min()), int(rows.max()) + 1
    x0, x1 = int(x0), int(x1) + 1

    width, height = x1 - x0, y1 - y0
    aspect = width / height
    if not (0.85 <= aspect <= 1.15):
        raise ValueError(
            f"Detected emblem segment is not square (w={width} h={height} "
            f"aspect={aspect:.2f}) -- logo layout may have changed, refusing "
            "to guess."
        )
    return x0, y0, x1, y1


def square_pad_bbox(bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Expand a bbox to be square, centered on the original content."""
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    side = max(w, h)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return (
        int(round(cx - side / 2)),
        int(round(cy - side / 2)),
        int(round(cx + side / 2)),
        int(round(cy + side / 2)),
    )


def crop_content(im: Image.Image, bbox: tuple[int, int, int, int], pad_fraction: float) -> Image.Image:
    """Crop to bbox, expanded by pad_fraction on every side, staying within
    the source canvas."""
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    pad_x, pad_y = int(w * pad_fraction), int(h * pad_fraction)
    left = max(0, x0 - pad_x)
    top = max(0, y0 - pad_y)
    right = min(im.width, x1 + pad_x)
    bottom = min(im.height, y1 + pad_y)
    return im.crop((left, top, right, bottom))


def place_on_square_canvas(
    content: Image.Image, canvas_size: int, content_fraction: float, background: tuple | None = None
) -> Image.Image:
    """Center `content` on a canvas_size x canvas_size square, scaled so its
    largest side equals canvas_size * content_fraction. background=None
    keeps the canvas transparent; otherwise it's an RGBA fill color."""
    canvas = Image.new("RGBA", (canvas_size, canvas_size), background or (0, 0, 0, 0))

    target = int(round(canvas_size * content_fraction))
    scale = target / max(content.width, content.height)
    new_w, new_h = max(1, round(content.width * scale)), max(1, round(content.height * scale))
    resized = content.resize((new_w, new_h), Image.LANCZOS)

    off_x = (canvas_size - new_w) // 2
    off_y = (canvas_size - new_h) // 2
    canvas.alpha_composite(resized, (off_x, off_y))
    return canvas


def squircle_mask(size: int, exponent: float = 4.0) -> Image.Image:
    """A true superellipse ("squircle") alpha mask: |x/a|^n + |y/a|^n <= 1."""
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float64)
    center = (size - 1) / 2
    a = size / 2
    nx = np.abs((xs - center) / a)
    ny = np.abs((ys - center) / a)
    inside = (nx**exponent + ny**exponent) <= 1.0
    mask = (inside * 255).astype(np.uint8)
    return Image.fromarray(mask, mode="L")


def apply_mask(icon: Image.Image, shape: str) -> Image.Image:
    size = icon.size[0]
    if shape == "square":
        mask = Image.new("L", (size, size), 255)
    elif shape == "circle":
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    elif shape == "rounded-square":
        mask = Image.new("L", (size, size), 0)
        radius = int(size * 0.22)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    elif shape == "squircle":
        mask = squircle_mask(size)
    else:
        raise ValueError(f"Unknown mask shape: {shape}")

    flat = Image.new("RGBA", (size, size), BACKGROUND_COLOR)
    flat.alpha_composite(icon)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(flat, (0, 0), mask)
    return out


def build_contact_sheet(foreground: Image.Image, out_path: Path) -> None:
    shapes = ["square", "circle", "rounded-square", "squircle"]
    cell_pad = 24
    label_h = 22
    col_w = max(CONTACT_SHEET_SIZES) + cell_pad
    row_h = max(CONTACT_SHEET_SIZES) + cell_pad + label_h

    sheet_w = col_w * len(CONTACT_SHEET_SIZES) + cell_pad
    sheet_h = row_h * len(shapes) + cell_pad + 40
    sheet = Image.new("RGB", (sheet_w, sheet_h), (235, 235, 235))
    draw = ImageDraw.Draw(sheet)
    draw.text((cell_pad, 10), "Cinqic Calculator - launcher icon contact sheet", fill=(20, 20, 20))

    for row, shape in enumerate(shapes):
        y = 40 + row * row_h
        draw.text((cell_pad, y), shape, fill=(20, 20, 20))
        for col, size in enumerate(CONTACT_SHEET_SIZES):
            resized_master = foreground.resize((size, size), Image.LANCZOS)
            masked = apply_mask(resized_master, shape)
            x = cell_pad + col * col_w
            cy = y + label_h
            sheet.paste(masked, (x, cy), masked)
            draw.text((x, cy + size + 2), f"{size}px", fill=(80, 80, 80))
    sheet.save(out_path)


def build_ico(master: Image.Image, out_path: Path) -> None:
    sizes = [16, 32, 48, 64, 128, 256]
    master.save(out_path, format="ICO", sizes=[(s, s) for s in sizes])


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
def verify_square_icon(path: Path, expected_size: int, require_alpha: bool, max_center_offset_frac: float = 0.06) -> list[str]:
    problems = []
    im = Image.open(path)
    if im.size != (expected_size, expected_size):
        problems.append(f"size {im.size} != expected ({expected_size}, {expected_size})")
    if require_alpha and im.mode != "RGBA":
        problems.append(f"mode {im.mode} has no alpha channel")

    im_rgba = im.convert("RGBA")
    arr = np.array(im_rgba)
    alpha = arr[:, :, 3]
    opaque = alpha > 40
    if not opaque.any():
        problems.append("no non-transparent pixels found (empty image)")
        return problems

    ys, xs = np.where(opaque)
    centroid_x, centroid_y = xs.mean(), ys.mean()
    center = (expected_size - 1) / 2
    offset_frac = math.hypot(centroid_x - center, centroid_y - center) / expected_size
    if offset_frac > max_center_offset_frac:
        problems.append(f"content centroid offset {offset_frac:.3f} exceeds {max_center_offset_frac}")

    return problems


def verify_horizontal_logo(path: Path) -> list[str]:
    problems = []
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    alpha = arr[:, :, 3]
    if not (alpha > 40).any():
        problems.append("horizontal logo has no non-transparent pixels")
    aspect = im.width / im.height
    if not (2.2 <= aspect <= 4.5):
        problems.append(f"unexpected aspect ratio {aspect:.2f} for a horizontal wordmark logo")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--out-dir", default=str(Path(__file__).resolve().parent.parent))
    args = parser.parse_args()

    source_path = Path(args.source)
    out_dir = Path(args.out_dir)
    if not source_path.exists():
        raise SystemExit(f"Source logo not found: {source_path}")

    src = strip_unpremultiplied_color_noise(Image.open(source_path).convert("RGBA"))
    src = clean_ambient_wash(src)

    branding_dir = out_dir / "assets" / "branding"
    icons_dir = out_dir / "assets" / "icons"
    android_icon_dir = out_dir / "android" / "assets" / "icon"
    for d in (branding_dir, icons_dir, android_icon_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 1. Full horizontal logo: trim ambient wash, keep everything (emblem +
    #    wordmark + subtitle), small padding so nothing touches the edge.
    full_bbox = content_bbox(src)
    horizontal = crop_content(src, full_bbox, pad_fraction=0.04)
    horizontal_path = branding_dir / "cinqic-calculator-horizontal.png"
    horizontal.save(horizontal_path)

    # 2. Locate and square-pad the emblem (calculator + clover) only.
    emblem_bbox_raw = find_emblem_bbox(src)
    emblem_bbox_sq = square_pad_bbox(emblem_bbox_raw)
    emblem_content = crop_content(src, emblem_bbox_sq, pad_fraction=0.0)

    # 3. Master square emblem (transparent, ~86% content fill) for general
    #    use: README, About screen, favicon source.
    emblem_master = place_on_square_canvas(emblem_content, canvas_size=1024, content_fraction=0.86)
    emblem_master_path = branding_dir / "cinqic-calculator-emblem-master.png"
    emblem_master.save(emblem_master_path)

    # 4. Windows .ico + a flat 256px PNG, from the master (transparent).
    ico_path = icons_dir / "cinqic-calculator.ico"
    build_ico(emblem_master, ico_path)
    png_path = icons_dir / "cinqic-calculator.png"
    emblem_master.resize((256, 256), Image.LANCZOS).save(png_path)

    # 5. Android adaptive icon layers. Foreground content must sit inside
    #    the ~66/108 safe zone so no launcher mask (circle, squircle, etc.)
    #    clips the calculator or clover -- content_fraction=0.60 leaves
    #    margin below that safe-zone ratio.
    adaptive_fg = place_on_square_canvas(emblem_content, canvas_size=432, content_fraction=0.60)
    adaptive_fg_path = android_icon_dir / "icon_foreground.png"
    adaptive_fg.save(adaptive_fg_path)

    adaptive_bg = Image.new("RGBA", (432, 432), BACKGROUND_COLOR)
    adaptive_bg_path = android_icon_dir / "icon_background.png"
    adaptive_bg.save(adaptive_bg_path)

    # 6. Legacy (pre-adaptive) launcher icons per density: emblem flattened
    #    onto the background plate, same safe-zone fraction so old and new
    #    launcher icons look consistent.
    legacy_paths = {}
    for density, size in LEGACY_DENSITIES.items():
        fg = place_on_square_canvas(emblem_content, canvas_size=size, content_fraction=0.60)
        flat = Image.new("RGBA", (size, size), BACKGROUND_COLOR)
        flat.alpha_composite(fg)
        p = android_icon_dir / f"icon_legacy_{density}.png"
        flat.save(p)
        legacy_paths[density] = p

    # 7. Presplash: emblem centered on the background plate, generous margin.
    presplash = place_on_square_canvas(emblem_content, canvas_size=1440, content_fraction=0.42, background=BACKGROUND_COLOR)
    presplash_path = android_icon_dir / "presplash.png"
    presplash.save(presplash_path)

    # 8. Contact sheet across masks for Blessom's approval.
    contact_sheet_path = android_icon_dir / "contact_sheet.png"
    build_contact_sheet(adaptive_fg, contact_sheet_path)

    # ---- Verification -----------------------------------------------------
    print("\n--- Verification ---")
    all_ok = True

    checks = [
        ("emblem_master (1024, transparent)", emblem_master_path, 1024, True),
        ("adaptive foreground (432, transparent)", adaptive_fg_path, 432, True),
        ("adaptive background (432, opaque)", adaptive_bg_path, 432, False),
    ]
    for density, size in LEGACY_DENSITIES.items():
        checks.append((f"legacy {density} ({size})", legacy_paths[density], size, False))

    for label, path, size, require_alpha in checks:
        problems = verify_square_icon(path, size, require_alpha)
        status = "PASS" if not problems else "FAIL"
        if problems:
            all_ok = False
        print(f"[{status}] {label}: {path.relative_to(out_dir)}" + (f" -- {'; '.join(problems)}" if problems else ""))

    horiz_problems = verify_horizontal_logo(horizontal_path)
    status = "PASS" if not horiz_problems else "FAIL"
    if horiz_problems:
        all_ok = False
    print(f"[{status}] horizontal logo: {horizontal_path.relative_to(out_dir)}" + (f" -- {'; '.join(horiz_problems)}" if horiz_problems else ""))

    ico_im = Image.open(ico_path)
    ico_status = "PASS" if ico_im.size == (256, 256) else "FAIL"
    if ico_status == "FAIL":
        all_ok = False
    print(f"[{ico_status}] windows .ico largest frame: {ico_path.relative_to(out_dir)} -> {ico_im.size}")

    print(f"\ncontact sheet: {contact_sheet_path.relative_to(out_dir)}")
    print("\nOVERALL:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
