from PIL import Image
import os
import time

# Replace "path/to/folder" with the actual path to the folder containing the images
folder = r"D:\[REPOS]\mToolbox\Test"

for filename in os.listdir(folder):

    print(filename)

    file_path = os.path.join(folder, filename)

    # Open the image file using Pillow
    with Image.open(file_path) as img:
        # Extract the EXIF data from the image
        exif_data = img.getexif()

        # Get the creation date from the EXIF data
        date_time_original = exif_data.get(0x9003, "")

        # Rename the file based on the creation date
        new_filename = date_time_original + ".jpg"
        new_file_path = os.path.join(folder, new_filename)
        time.sleep(1)
        os.rename(file_path, new_file_path)