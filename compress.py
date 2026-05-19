from PIL import Image
import os

# =========================================================
# CONFIG
# =========================================================

# Folder to scan recursively
ROOT_FOLDER = r"/Users/ravi.parekh/Documents/personal/images-indiska/images"

# Output folder
OUTPUT_FOLDER = r"/Users/ravi.parekh/Documents/personal/images-indiska/images/com"

# Max width
MAX_WIDTH = 1080

# Compression quality (1-100)
QUALITY = 75

# Supported image formats
SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


# =========================================================
# HELPERS
# =========================================================

def human_size(size_bytes):
    units = ["B", "KB", "MB", "GB"]

    size = float(size_bytes)

    for unit in units:
        if size < 1024:
            return f"{size:.2f} {unit}"

        size /= 1024

    return f"{size:.2f} TB"


# =========================================================
# CREATE OUTPUT FOLDER
# =========================================================

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# =========================================================
# HEADER
# =========================================================

print(
    f"{'FILE':<40} | "
    f"{'BEFORE SIZE':>12} | "
    f"{'AFTER SIZE':>12} | "
    f"{'BEFORE PIXEL':>15} | "
    f"{'AFTER PIXEL':>15}"
)

print("-" * 105)


# =========================================================
# PROCESS IMAGES
# =========================================================

for current_root, _, files in os.walk(ROOT_FOLDER):

    for file_name in files:

        if not file_name.lower().endswith(SUPPORTED_EXTENSIONS):
            continue

        input_path = os.path.join(current_root, file_name)

        try:
            img = Image.open(input_path)

            # Original pixel size
            original_width = img.width
            original_height = img.height

            # =================================================
            # RESIZE ONLY IF WIDTH > MAX_WIDTH
            # =================================================

            if img.width > MAX_WIDTH:

                width_percent = MAX_WIDTH / float(img.width)

                new_height = int(float(img.height) * width_percent)

                resized_img = img.resize(
                    (MAX_WIDTH, new_height),
                    Image.LANCZOS
                )

                final_width = MAX_WIDTH
                final_height = new_height

            else:

                resized_img = img.copy()

                final_width = img.width
                final_height = img.height

            # =================================================
            # KEEP SAME FOLDER STRUCTURE
            # =================================================

            relative_path = os.path.relpath(current_root, ROOT_FOLDER)

            output_dir = os.path.join(OUTPUT_FOLDER, relative_path)

            os.makedirs(output_dir, exist_ok=True)

            output_path = os.path.join(output_dir, file_name)

            # =================================================
            # HANDLE PNG TRANSPARENCY
            # =================================================

            if resized_img.mode in ("RGBA", "P"):
                resized_img = resized_img.convert("RGB")

            # =================================================
            # SAVE IMAGE
            # =================================================

            resized_img.save(
                output_path,
                optimize=True,
                quality=QUALITY
            )

            # =================================================
            # FILE SIZES
            # =================================================

            before_size = human_size(os.path.getsize(input_path))
            after_size = human_size(os.path.getsize(output_path))

            before_pixel = f"{original_width}x{original_height}"
            after_pixel = f"{final_width}x{final_height}"

            # =================================================
            # OUTPUT
            # =================================================

            print(
                f"{file_name:<40} | "
                f"{before_size:>12} | "
                f"{after_size:>12} | "
                f"{before_pixel:>15} | "
                f"{after_pixel:>15}"
            )

        except Exception as e:

            print(f"FAILED: {file_name} -> {e}")

print("\nDONE")