from pathlib import Path
from PIL import Image
import tempfile
import os

# Folder containing your .webp images
FOLDER = Path("./images")  # Change as needed

resized_files = []
skipped_files = []

total_old_size = 0
total_new_size = 0

for file in FOLDER.glob("*.webp"):
    stem = file.stem

    # Ignore generated variants
    if stem.endswith("-300") or stem.endswith("-720"):
        continue

    old_size = file.stat().st_size

    with Image.open(file) as img:
        old_w, old_h = img.size

        # Skip images already <= 720px wide
        if old_w <= 720:
            skipped_files.append([
                file.name,
                f"{old_w}x{old_h}",
                "Width <= 720"
            ])
            continue

        ratio = 720 / old_w
        new_w = 720
        new_h = round(old_h * ratio)

        resized = img.resize(
            (new_w, new_h),
            Image.Resampling.LANCZOS
        )

        # Save to temporary file first
        with tempfile.NamedTemporaryFile(
                suffix=".webp",
                delete=False
        ) as tmp:
            temp_file = tmp.name

        resized.save(
            temp_file,
            format="WEBP",
            quality=85,
            method=6
        )

    new_size = os.path.getsize(temp_file)

    # Only replace if file becomes smaller
    if new_size < old_size:
        os.replace(temp_file, file)

        saved_bytes = old_size - new_size
        saved_pct = (saved_bytes / old_size) * 100

        total_old_size += old_size
        total_new_size += new_size

        resized_files.append([
            file.name,
            f"{old_w}x{old_h}",
            f"{new_w}x{new_h}",
            old_size / 1024,
            new_size / 1024,
            saved_bytes / 1024,
            saved_pct
        ])
    else:
        os.remove(temp_file)

        skipped_files.append([
            file.name,
            f"{old_size/1024:.1f} KB",
            f"{new_size/1024:.1f} KB",
            "Would increase size"
        ])

# --------------------------------------------------
# RESIZED FILES
# --------------------------------------------------

print("\n=== RESIZED FILES ===\n")

if resized_files:
    header = (
        f"{'File':40}"
        f"{'Old Dim':15}"
        f"{'New Dim':15}"
        f"{'Old Size':12}"
        f"{'New Size':12}"
        f"{'Saved'}"
    )

    print(header)
    print("-" * len(header))

    for row in resized_files:
        print(
            f"{row[0]:40}"
            f"{row[1]:15}"
            f"{row[2]:15}"
            f"{row[3]:>8.1f} KB"
            f"{row[4]:>8.1f} KB"
            f"  {row[5]:>8.1f} KB ({row[6]:.1f}%)"
        )
else:
    print("No files resized.")

# --------------------------------------------------
# SKIPPED FILES
# --------------------------------------------------

print("\n=== SKIPPED FILES ===\n")

if skipped_files:
    for row in skipped_files:
        print(" | ".join(str(x) for x in row))
else:
    print("No skipped files.")

# --------------------------------------------------
# TOTALS
# --------------------------------------------------

print("\n=== TOTAL SUMMARY ===\n")

if total_old_size > 0:
    total_saved = total_old_size - total_new_size
    total_saved_pct = (total_saved / total_old_size) * 100

    print(f"Original Size : {total_old_size / 1024:.1f} KB")
    print(f"New Size      : {total_new_size / 1024:.1f} KB")
    print(f"Saved         : {total_saved / 1024:.1f} KB")
    print(f"Reduction     : {total_saved_pct:.1f}%")
else:
    print("No files were resized.")