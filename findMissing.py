import os
import shutil

FOLDER = "./images"  # change this

SIZES = ["300", "720"]

def get_base_name(filename):
    if filename.endswith(".webp"):
        name = filename[:-5]  # remove .webp

        for size in SIZES:
            suff    ix = f"-{size}"
            if name.endswith(suffix):
                return name[:-len(suffix)], size

        return name, None
    return None, None


def scan_folder(folder):
    files = os.listdir(folder)

    base_map = {}

    # group files by base name
    for f in files:
        if not f.endswith(".webp"):
            continue

        base, size = get_base_name(f)
        if base not in base_map:
            base_map[base] = {}

        if size:
            base_map[base][size] = f
        else:
            base_map[base]["original"] = f

    return base_map


def sync_sizes(folder):
    base_map = scan_folder(folder)
    changes = []

    for base, variants in base_map.items():
        for size in SIZES:
            target = f"{base}-{size}.webp"

            if size not in variants:
                # find source
                source = None

                # prefer the other size
                for s in reversed(SIZES):
                    if s in variants:
                        source = variants[s]
                        break

                if source:
                    src_path = os.path.join(folder, source)
                    dst_path = os.path.join(folder, target)

                    shutil.copy2(src_path, dst_path)

                    changes.append(f"Copied {source} → {target}")

    return changes


if __name__ == "__main__":
    changes = sync_sizes(FOLDER)

    print("\n=== Changes Made ===")
    if not changes:
        print("No changes needed")
    else:
        for c in changes:
            print(c)