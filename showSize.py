#!/usr/bin/env python3

import os
from PIL import Image

# =========================================================
# HARDCODE THE ROOT PATH HERE
# =========================================================
ROOT_PATH = r"/Users/ravi.parekh/Documents/personal/images-indiska/images"

# Example:
# ROOT_PATH = r"C:\Users\john\Downloads"
# ROOT_PATH = r"/home/john/downloads"
# =========================================================


def human_readable_size(size_bytes):
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024


files_data = []

# Supported image formats
IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".bmp",
    ".tiff",
    ".avif"
)

# =========================================================
# RECURSIVE SEARCH
# =========================================================
for current_root, _, files in os.walk(ROOT_PATH):

    for file_name in files:

        # Skip non-image files
        if not file_name.lower().endswith(IMAGE_EXTENSIONS):
            continue

        full_path = os.path.join(current_root, file_name)

        try:
            # File size in bytes
            size_bytes = os.path.getsize(full_path)

            # File size in MB
            size_mb = round(size_bytes / (1024 * 1024), 2)

            # Read dimensions
            try:
                with Image.open(full_path) as img:
                    width, height = img.size
                    dimensions = f"{width}x{height}"
            except Exception:
                dimensions = "Unknown"

            # Relative folder path
            relative_folder = os.path.relpath(current_root, ROOT_PATH)

            files_data.append({
                "filename": file_name,
                "folder": relative_folder,
                "dimensions": dimensions,
                "size_bytes": size_bytes,
                "size_mb": size_mb,
                "size_human": human_readable_size(size_bytes)
            })

        except Exception as e:
            print(f"Error reading {full_path}: {e}")


# =========================================================
# SORT BY FILE SIZE DESCENDING
# =========================================================
files_data.sort(key=lambda x: x["size_bytes"], reverse=True)


# =========================================================
# PRINT OUTPUT
# =========================================================
print(
    f"{'FILENAME':<45} | "
    f"{'DIMENSIONS':<12} | "
    f"{'SIZE(MB)':>10} | "
    f"{'SIZE':>12} | "
    f"{'FOLDER (RELATIVE)':<45}"
)

print("-" * 150)

for item in files_data:

    print(
        f"{item['filename']:<45} | "
        f"{item['dimensions']:<12} | "
        f"{item['size_mb']:>10.2f} | "
        f"{item['size_human']:>12} | "
        f"{item['folder']:<45}"
    )

# =========================================================
# SUMMARY
# =========================================================
total_files = len(files_data)
total_size_bytes = sum(x["size_bytes"] for x in files_data)

print("\n" + "=" * 150)
print(f"Total Images : {total_files}")
print(f"Total Size   : {human_readable_size(total_size_bytes)}")
print("=" * 150)