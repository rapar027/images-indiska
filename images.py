"""
image_compressor.py
-------------------
All-in-one image compressor with three independent filter layers.
Flip any toggle in the CONFIG section — nothing else needs to change.

Dependencies: pip install Pillow
"""

from pathlib import Path
from PIL import Image
import shutil

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG — edit only this section
# ══════════════════════════════════════════════════════════════════════════════

ENABLED               = True        # ← master switch; False = do absolutely nothing

INPUT_DIR             = "input"     # source folder (sub-folders are included)
OUTPUT_DIR            = "output"    # destination folder
OVERWRITE_OUTPUT      = False       # True = re-compress files that already exist in output

# ── Filter 1 · Hard-coded quality / resize ────────────────────────────────────
COMPRESS_ENABLED      = True        # True = apply quality + resize to every passing image
QUALITY               = 78          # JPEG / WebP quality 1–95  (lower = smaller file)
PNG_COMPRESS_LEVEL    = 9           # PNG compression 0–9
TARGET_MAX_WIDTH      = 720        # resize image down if wider  than this (px)
TARGET_MAX_HEIGHT     = 1080        # resize image down if taller than this (px)

# ── Filter 2 · Width guard ────────────────────────────────────────────────────
WIDTH_FILTER_ENABLED  = True        # True = skip images narrower than MIN_WIDTH
MIN_WIDTH             = 1080        # only compress images WIDER than this (px)
COPY_NARROW_IMAGES    = False       # True = copy narrow images unchanged; False = skip them

# ── Filter 3 · File-size guard ────────────────────────────────────────────────
SIZE_FILTER_ENABLED   = True        # True = skip images smaller than MIN_FILE_SIZE_KB
MIN_FILE_SIZE_KB      = 200         # only compress files LARGER than this (KB)
COPY_SMALL_FILES      = False       # True = copy small files unchanged; False = skip them

SUPPORTED_FORMATS     = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

# ══════════════════════════════════════════════════════════════════════════════


def decide(src: Path, width: int) -> tuple[str, str]:
    """
    Run all enabled filters and return (action, reason).
    action is one of: "COMPRESS" | "COPY" | "SKIP"
    """
    file_kb = src.stat().st_size / 1024

    # Filter 2 — width guard
    if WIDTH_FILTER_ENABLED and width <= MIN_WIDTH:
        reason = f"width {width}px ≤ {MIN_WIDTH}px"
        return ("COPY" if COPY_NARROW_IMAGES else "SKIP"), reason

    # Filter 3 — file-size guard
    if SIZE_FILTER_ENABLED and file_kb <= MIN_FILE_SIZE_KB:
        reason = f"file {file_kb:.1f} KB ≤ {MIN_FILE_SIZE_KB} KB"
        return ("COPY" if COPY_SMALL_FILES else "SKIP"), reason

    # Filter 1 — compression enabled?
    if not COMPRESS_ENABLED:
        return "COPY", "COMPRESS_ENABLED is False"

    return "COMPRESS", "passes all filters"


def compress_image(src: Path, dst: Path) -> dict:
    """Compress + resize one image, return before/after stats."""
    original_kb = src.stat().st_size / 1024

    with Image.open(src) as img:
        original_dims = img.size

        if img.mode in ("P", "RGBA"):
            img = img.convert("RGB")

        img.thumbnail((TARGET_MAX_WIDTH, TARGET_MAX_HEIGHT), Image.LANCZOS)

        dst.parent.mkdir(parents=True, exist_ok=True)
        fmt = dst.suffix.lower()
        save_kwargs = {"optimize": True}
        if fmt in (".jpg", ".jpeg"):
            save_kwargs["quality"] = QUALITY
        elif fmt == ".png":
            save_kwargs["compress_level"] = PNG_COMPRESS_LEVEL
        elif fmt == ".webp":
            save_kwargs["quality"] = QUALITY

        img.save(dst, **save_kwargs)
        new_dims = img.size

    compressed_kb = dst.stat().st_size / 1024
    saved_pct = (1 - compressed_kb / original_kb) * 100 if original_kb else 0

    return {
        "original_kb":   original_kb,
        "compressed_kb": compressed_kb,
        "saved_pct":     saved_pct,
        "original_dims": original_dims,
        "new_dims":      new_dims,
    }


def run():
    if not ENABLED:
        print("DISABLED — set ENABLED = True to run.")
        return

    input_path  = Path(INPUT_DIR)
    output_path = Path(OUTPUT_DIR)

    if not input_path.exists():
        print(f"Input folder '{INPUT_DIR}' not found. Create it and add images.")
        return

    images = [f for f in input_path.rglob("*") if f.suffix.lower() in SUPPORTED_FORMATS]
    if not images:
        print(f"No supported images found in '{INPUT_DIR}'.")
        return

    # ── Print active settings ─────────────────────────────────────────────────
    print("─" * 62)
    print(f"  Input       : {INPUT_DIR}   →   Output: {OUTPUT_DIR}")
    print(f"  Filter 1    : compress={COMPRESS_ENABLED}  quality={QUALITY}  "
          f"max={TARGET_MAX_WIDTH}x{TARGET_MAX_HEIGHT}px")
    print(f"  Filter 2    : width_filter={WIDTH_FILTER_ENABLED}  "
          f"min_width={MIN_WIDTH}px  copy_narrow={COPY_NARROW_IMAGES}")
    print(f"  Filter 3    : size_filter={SIZE_FILTER_ENABLED}  "
          f"min_size={MIN_FILE_SIZE_KB}KB  copy_small={COPY_SMALL_FILES}")
    print(f"  Images found: {len(images)}")
    print("─" * 62)

    counters = {"compressed": 0, "copied": 0, "skipped": 0, "error": 0}
    total_original = total_compressed = 0.0

    for src in images:
        relative = src.relative_to(input_path)
        dst      = output_path / relative

        if dst.exists() and not OVERWRITE_OUTPUT:
            print(f"  SKIP  {src.name} (already in output)")
            counters["skipped"] += 1
            continue

        try:
            with Image.open(src) as probe:
                img_width = probe.size[0]

            action, reason = decide(src, img_width)
            file_kb = src.stat().st_size / 1024

            if action == "COMPRESS":
                s = compress_image(src, dst)
                total_original   += s["original_kb"]
                total_compressed += s["compressed_kb"]
                counters["compressed"] += 1
                print(
                    f"  ✓  {src.name:<34} "
                    f"{s['original_dims'][0]}x{s['original_dims'][1]} → "
                    f"{s['new_dims'][0]}x{s['new_dims'][1]}  "
                    f"{s['original_kb']:.0f}KB → {s['compressed_kb']:.0f}KB  "
                    f"({s['saved_pct']:.1f}% saved)"
                )

            elif action == "COPY":
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                total_original   += file_kb
                total_compressed += file_kb
                counters["copied"] += 1
                print(f"  →  {src.name:<34} {file_kb:.0f}KB  COPIED  [{reason}]")

            else:  # SKIP
                counters["skipped"] += 1
                print(f"  -  {src.name:<34} {file_kb:.0f}KB  SKIPPED [{reason}]")

        except Exception as e:
            counters["error"] += 1
            print(f"  ✗  {src.name}: {e}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("─" * 62)
    print(f"  Compressed : {counters['compressed']}  |  "
          f"Copied : {counters['copied']}  |  "
          f"Skipped : {counters['skipped']}  |  "
          f"Errors : {counters['error']}")
    if total_original:
        overall = (1 - total_compressed / total_original) * 100
        print(f"  Volume     : {total_original:.1f} KB → {total_compressed:.1f} KB  "
              f"({overall:.1f}% saved on processed files)")
    print("─" * 62)


if __name__ == "__main__":
    run()