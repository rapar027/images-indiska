import magic
import os
from collections import defaultdict

def get_image_type(file_path):
    mime = magic.from_file(file_path, mime=True)

    if mime == "image/jpeg":
        return "jpg"
    elif mime == "image/png":
        return "png"
    else:
        return "unknown"

def scan_and_group(folder_path):
    grouped = defaultdict(list)

    for filename in os.listdir(folder_path):
        path = os.path.join(folder_path, filename)

        if os.path.isfile(path):
            img_type = get_image_type(path)
            if img_type in ["jpg", "png"]:
                grouped[img_type].append(filename)

    # Print result
    for img_type in ["jpg", "png"]:
        files = grouped[img_type]
        print(f"{img_type.upper()} ({len(files)}):")
        for f in files:
            print(f"- {f}")
        print()  # blank line


# Example usage
scan_and_group("/Users/ravi.parekh/Documents/personal/images-indiska/images")
