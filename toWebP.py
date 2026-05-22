import os
from PIL import Image

def convert_images_to_webp(directory=".", quality=80, delete_original=False):
    """
    Walks through the specified directory and converts all JPG, JPEG, and PNG
    images to optimized WebP format.

    :param directory: Target folder path (defaults to current folder '.')
    :param quality: WebP compression quality (1-100). 80 is the sweet spot.
    :param delete_original: Set to True if you want to automatically delete the old files.
    """
    # Supported input image types
    target_extensions = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')
    converted_count = 0

    print(f"🚀 Starting conversion in: {os.path.abspath(directory)}")
    print(f"⚙️ Target WebP Quality: {quality}%\n")

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(target_extensions):
                input_path = os.path.join(root, file)

                # Create the new filename with .webp extension
                file_clean_name, _ = os.path.splitext(file)
                output_path = os.path.join(root, f"{file_clean_name}.webp")

                try:
                    # Open, convert to RGB (required for JPG to WebP), and save
                    with Image.open(input_path) as img:
                        # Convert transparent PNGs nicely or handle raw RGB modes
                        if img.mode in ('RGBA', 'LA'):
                            # Keeps transparency intact for logos
                            img.save(output_path, 'WEBP', quality=quality)
                        else:
                            # Standard JPEG handling
                            img.convert('RGB').save(output_path, 'WEBP', quality=quality)

                    old_size = os.path.getsize(input_path) / 1024
                    new_size = os.path.getsize(output_path) / 1024
                    savings = ((old_size - new_size) / old_size) * 100 if old_size > 0 else 0

                    print(f"✅ Converted: {file} -> {file_clean_name}.webp")
                    print(f"   Size reduced from {old_size:.1f} KB to {new_size:.1f} KB ({savings:.1f}% saved)")

                    converted_count += 1

                    # Safely delete original if flag is set
                    if delete_original:
                        os.remove(input_path)
                        print(f"   🗑️ Deleted original: {file}")

                except Exception as e:
                    print(f"❌ Failed to convert {file}: {str(e)}")

    print(f"\n🎉 Done! Successfully converted {converted_count} images to WebP.")

if __name__ == "__main__":
    # Change delete_original=True if you want to automatically wipe out the old JPG/PNG files
    convert_images_to_webp(directory="./images", quality=80, delete_original=False)