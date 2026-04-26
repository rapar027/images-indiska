import os
import shutil
import magic

# Path to the folder with your images
folder_path = '/Users/ravi.parekh/Documents/personal/images-indiska/images'

# Create separate folders for .jpg and .png images
jpg_folder = os.path.join(folder_path, 'jpg')
png_folder = os.path.join(folder_path, 'png')

# Create the folders if they don't exist
os.makedirs(jpg_folder, exist_ok=True)
os.makedirs(png_folder, exist_ok=True)

# Initialize the magic library to detect file types
mime = magic.Magic(mime=True)

# Loop through each file in the folder
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)
    
    # Skip subfolders
    if os.path.isdir(file_path):
        continue
    
    # Get the file's real MIME type
    file_type = mime.from_file(file_path)

    # Check if the file is a valid image type and move it to the correct folder
    if file_type == 'image/jpeg':
        # Move to jpg folder
        new_location = os.path.join(jpg_folder, filename)
        shutil.move(file_path, new_location)
        print(f'Moved {filename} to jpg folder')

    elif file_type == 'image/png':
        # Move to png folder
        new_location = os.path.join(png_folder, filename)
        shutil.move(file_path, new_location)
        print(f'Moved {filename} to png folder')

    else:
        print(f'Skipped {filename} (not a JPG or PNG image)')
