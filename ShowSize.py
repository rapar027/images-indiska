#!/usr/bin/env python3

import os

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

# Nested recursive search
for current_root, _, files in os.walk(ROOT_PATH):
    for file_name in files:
        full_path = os.path.join(current_root, file_name)

        try:
            size = os.path.getsize(full_path)

            # Folder relative to ROOT_PATH
            relative_folder = os.path.relpath(current_root, ROOT_PATH)

            files_data.append({
                "filename": file_name,
                "folder": relative_folder,
                "size_bytes": size,
                "size_human": human_readable_size(size)
            })

        except Exception:
            pass


# =========================================================
# SORT BY SIZE DESCENDING
# =========================================================
files_data.sort(key=lambda x: x["size_bytes"], reverse=True)


# =========================================================
# PRINT OUTPUT
# =========================================================
print(f"{'FILENAME':<50} | {'FOLDER (RELATIVE)':<60} | {'SIZE':>12}")
print("-" * 130)

for item in files_data:
    print(
        f"{item['filename']:<50} | "
        f"{item['folder']:<60} | "
        f"{item['size_human']:>12}"
    )