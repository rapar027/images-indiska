#!/usr/bin/env python3
"""
Image Optimizer — converts images to WebP with mobile (300px) and desktop (720px) variants.
Detects images by content (magic bytes), not extension.
"""

import os
import sys
import struct
import zlib
from pathlib import Path

# ── dependency check ────────────────────────────────────────────────────────
try:
    from PIL import Image
except ImportError:
    print("Pillow is not installed. Run:  pip install Pillow")
    sys.exit(1)

# ── magic-byte image detection ───────────────────────────────────────────────
MAGIC = {
    b"\x89PNG":               "PNG",
    b"\xff\xd8\xff":          "JPEG",
    b"GIF8":                  "GIF",
    b"RIFF":                  "WEBP",   # needs extra check at offset 8
    b"BM":                    "BMP",
    b"\x00\x00\x01\x00":     "ICO",
    b"II\x2a\x00":            "TIFF",
    b"MM\x00\x2a":            "TIFF",
    b"\x00\x00\x00\x0cjP":   "JPEG2000",
    b"\xff\x4f\xff\x51":     "JPEG2000",
}

def is_image_file(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            header = f.read(12)
        for magic, fmt in MAGIC.items():
            if header.startswith(magic):
                if fmt == "WEBP":
                    return header[8:12] == b"WEBP"
                return True
        return False
    except (OSError, PermissionError):
        return False

# ── helpers ──────────────────────────────────────────────────────────────────
def human_size(n_bytes: int) -> str:
    if n_bytes < 1024:
        return f"{n_bytes} B"
    kb = n_bytes / 1024
    if kb < 1024:
        return f"{kb:.1f} KB"
    return f"{kb/1024:.2f} MB"

def resize_to_width(img: Image.Image, target_w: int):
    w, h = img.size
    new_h = round(h * target_w / w)
    return img.resize((target_w, new_h), Image.LANCZOS)

def resize_to_height(img: Image.Image, target_h: int):
    w, h = img.size
    new_w = round(w * target_h / h)
    return img.resize((new_w, target_h), Image.LANCZOS)

def save_webp(img: Image.Image, dest: Path, quality: int = 82) -> int:
    """Save as WebP, returning file size in bytes."""
    img.save(dest, "WEBP", quality=quality, method=6)
    return dest.stat().st_size

def save_webp_under_limit(img: Image.Image, dest: Path,
                          limit_bytes: int = 200 * 1024) -> int:
    """Try progressively lower quality until file fits under limit_bytes."""
    for q in (82, 75, 65, 55, 45, 35):
        img.save(dest, "WEBP", quality=q, method=6)
        size = dest.stat().st_size
        if size <= limit_bytes:
            return size
    return dest.stat().st_size  # best we could do

# ── configuration prompt ─────────────────────────────────────────────────────
def ask_config() -> dict:
    print("\n" + "═" * 60)
    print("  Image Optimizer — Configuration")
    print("═" * 60)

    # Root folder
    root_input = input("\nRoot folder to scan [.]: ").strip() or "."
    root = Path(root_input).expanduser().resolve()
    if not root.is_dir():
        print(f"✗  '{root}' is not a directory. Exiting.")
        sys.exit(1)

    # Output folder
    out_input = input("Output folder (leave blank = alongside originals): ").strip()
    out_root = Path(out_input).expanduser().resolve() if out_input else None

    # Resize axis
    print("\nResize by:")
    print("  1 — width  (height auto-scales)")
    print("  2 — height (width auto-scales)")
    axis_choice = input("Choice [1]: ").strip() or "1"
    axis = "width" if axis_choice != "2" else "height"

    # Sizes
    default_sizes = "300,720"
    sizes_raw = input(
        f"\nComma-separated {axis} targets in px [{default_sizes}]: "
    ).strip() or default_sizes

    sizes = []
    for s in sizes_raw.split(","):
        s = s.strip()
        if s.isdigit():
            sizes.append(int(s))
        else:
            print(f"  ⚠ Ignoring non-numeric value: '{s}'")
    if not sizes:
        print("No valid sizes provided. Using defaults: 300, 720")
        sizes = [300, 720]
    sizes = sorted(set(sizes))

    # Desktop size limit
    desktop_px = max(sizes)
    limit_raw = input(
        f"\nMax file size for largest variant ({desktop_px}px) in KB [200]: "
    ).strip() or "200"
    try:
        limit_kb = int(limit_raw)
    except ValueError:
        limit_kb = 200
    limit_bytes = limit_kb * 1024

    # Keep originals?
    keep = input("\nKeep original files? [Y/n]: ").strip().lower()
    keep_originals = keep != "n"

    # Dry run?
    dry = input("Dry run (preview only, no files written)? [y/N]: ").strip().lower()
    dry_run = dry == "y"

    print("\n" + "─" * 60)
    print(f"  Root      : {root}")
    print(f"  Output    : {'alongside originals' if out_root is None else out_root}")
    print(f"  Axis      : {axis}")
    print(f"  Sizes     : {sizes} px")
    print(f"  Max size  : {limit_kb} KB (applied to {desktop_px}px variant)")
    print(f"  Keep orig : {keep_originals}")
    print(f"  Dry run   : {dry_run}")
    print("─" * 60)
    confirm = input("\nProceed? [Y/n]: ").strip().lower()
    if confirm == "n":
        print("Aborted.")
        sys.exit(0)

    return {
        "root": root,
        "out_root": out_root,
        "axis": axis,
        "sizes": sizes,
        "limit_bytes": limit_bytes,
        "keep_originals": keep_originals,
        "dry_run": dry_run,
    }

# ── main processing ──────────────────────────────────────────────────────────
def collect_images(root: Path) -> list[Path]:
    images = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and is_image_file(path):
            images.append(path)
    return images

def process_images(cfg: dict) -> list[dict]:
    root      = cfg["root"]
    out_root  = cfg["out_root"]
    axis      = cfg["axis"]
    sizes     = cfg["sizes"]
    limit     = cfg["limit_bytes"]
    dry_run   = cfg["dry_run"]
    desktop_px = max(sizes)

    images = collect_images(root)
    if not images:
        print("\nNo image files found.")
        return []

    print(f"\nFound {len(images)} image(s). Processing…\n")
    rows = []

    for img_path in images:
        try:
            with Image.open(img_path) as img:
                img.load()          # force decode so we detect true format
                orig_w, orig_h = img.size
                orig_dim = f"{orig_w}×{orig_h}"

                # Convert to RGB(A) so WebP encoder is happy
                if img.mode in ("RGBA", "LA", "P"):
                    work = img.convert("RGBA")
                else:
                    work = img.convert("RGB")

        except Exception as e:
            print(f"  ✗ Skipping {img_path.name}: {e}")
            continue

        # Determine output directory
        rel = img_path.parent.relative_to(root)
        if out_root:
            dest_dir = out_root / rel
        else:
            dest_dir = img_path.parent

        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)

        stem = img_path.stem
        row = {
            "name":     img_path.name,
            "orig_dim": orig_dim,
        }

        variant_info = {}   # size_px → (dim_str, bytes_int or None, status)

        for target_px in sizes:
            # Output filename: originalname-300.webp
            dest = dest_dir / f"{stem}-{target_px}.webp"

            # Check if image is already smaller — skip if so
            ref = orig_w if axis == "width" else orig_h
            if ref <= target_px:
                variant_info[target_px] = (orig_dim, None, "skipped (already smaller)")
                print(f"  ⏭ {dest.name}  already ≤ {target_px}px — skipped")
                continue

            # Resize
            if axis == "width":
                resized = resize_to_width(work, target_px)
            else:
                resized = resize_to_height(work, target_px)

            rdim = f"{resized.width}×{resized.height}"

            if dry_run:
                variant_info[target_px] = (rdim, None, "dry-run")
                print(f"  [DRY] {dest.name}  {rdim}")
            else:
                if target_px == desktop_px:
                    size_b = save_webp_under_limit(resized, dest, limit)
                else:
                    size_b = save_webp(resized, dest)
                variant_info[target_px] = (rdim, size_b, "ok")
                print(f"  ✓ {dest.name}  {rdim}  {human_size(size_b)}")

        # Original-size WebP: originalname.webp (no dimension suffix)
        orig_dest = dest_dir / f"{stem}.webp"
        if dry_run:
            orig_size_b = None
            print(f"  [DRY] {orig_dest.name}  {orig_dim}")
        else:
            orig_size_b = save_webp(work, orig_dest)
            print(f"  ✓ {orig_dest.name}  {orig_dim}  {human_size(orig_size_b)}")

        row["variant_info"] = variant_info
        row["orig_size_b"]  = img_path.stat().st_size
        row["orig_dest"]    = (orig_dim, orig_size_b)
        rows.append(row)

        # Remove original if requested
        if not cfg["keep_originals"] and not dry_run:
            img_path.unlink()

    return rows

# ── summary table ─────────────────────────────────────────────────────────────
def print_summary(rows: list[dict], cfg: dict):
    sizes      = cfg["sizes"]
    mobile_px  = min(sizes)
    desktop_px = max(sizes)

    print("\n" + "═" * 100)
    print("  SUMMARY")
    print("═" * 100)

    col_w = [30, 15, 20, 14, 20, 14, 20, 14]
    headers = [
        "Image", "Orig Dim",
        f"Mobile Dim ({mobile_px}px)", "Mobile Size",
        f"Desktop Dim ({desktop_px}px)", "Desktop Size",
        "Original WebP Dim", "Original WebP Size",
    ]

    def row_fmt(cells):
        return "  ".join(str(c).ljust(w) for c, w in zip(cells, col_w))

    print(row_fmt(headers))
    print("─" * 100)

    total_mob  = 0
    total_dsk  = 0
    total_orig = 0

    for row in rows:
        vi = row["variant_info"]

        mob = vi.get(mobile_px)
        mob_dim  = mob[0] if mob else "—"
        mob_size = human_size(mob[1]) if mob and mob[1] else (mob[2] if mob else "—")
        if mob and mob[1]:
            total_mob += mob[1]

        dsk = vi.get(desktop_px)
        dsk_dim  = dsk[0] if dsk else "—"
        dsk_size = human_size(dsk[1]) if dsk and dsk[1] else (dsk[2] if dsk else "—")
        if dsk and dsk[1]:
            total_dsk += dsk[1]

        orig_dim, orig_size_b = row["orig_dest"]
        orig_wsize = human_size(orig_size_b) if orig_size_b else "dry-run"
        if orig_size_b:
            total_orig += orig_size_b

        print(row_fmt([
            row["name"][:29],
            row["orig_dim"],
            mob_dim, mob_size,
            dsk_dim, dsk_size,
            orig_dim, orig_wsize,
        ]))

    print("─" * 100)
    print(row_fmt([
        f"TOTAL ({len(rows)} images)",
        "",
        "", human_size(total_mob),
        "", human_size(total_dsk),
        "", human_size(total_orig),
    ]))
    print("═" * 100)
    print(f"\nDone. {len(rows)} image(s) processed.")

# ── entry point ───────────────────────────────────────────────────────────────
def main():
    cfg  = ask_config()
    rows = process_images(cfg)
    if rows:
        print_summary(rows, cfg)

if __name__ == "__main__":
    main()