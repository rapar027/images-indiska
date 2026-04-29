import os

# Path to the folder with your files
folder_path = '/Users/ravi.parekh/Documents/personal/images-indiska/images/png'

# New extension you want to apply (e.g., '.jpg', '.png')
new_extension = '.png'  # Change to the desired extension

# Loop through each file in the folder
for filename in os.listdir(folder_path):
    # Get the full path of the file
    file_path = os.path.join(folder_path, filename)

    # Check if it's a file (and not a subfolder)
    if os.path.isfile(file_path):
        # Get the file name without the extension
        name_without_extension = os.path.splitext(filename)[0]
        
        # Construct the new file name with the desired extension
        new_filename = name_without_extension + new_extension
        
        # Get the full path for the new file name
        new_file_path = os.path.join(folder_path, new_filename)
        
        # Rename the file
        os.rename(file_path, new_file_path)
        print(f'Renamed: {filename} -> {new_filename}')