import os
from os.path import basename
import argparse
from datetime import datetime
from shutil import copyfile
import shutil
from pathlib import Path
import zipfile
import patoolib
import sys
from pdf2jpg import pdf2jpg

from PIL import Image

defaultOutputFolder = datetime.now().strftime("%Y%m%d_%H%M%S")
fullOutputPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), defaultOutputFolder)


def parser():
    """
    @brief    Parser function to get all the arguments
    """
    description = ""

    # Construct the argument parse and parse the arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=description)
    parser.add_argument("-i", "--input", type=str, default=None, 
                        help="path to comic cbr, cbz, pdf or folder with images")
    parser.add_argument("-o", "--output", type=str, default="output", 
                        help="path to output")
    parser.add_argument("--dontrename", action='store_true',
                        help="Name image files with included digits and added zeroes")
    print('\n' + str(parser.parse_args()) + '\n')

    return parser.parse_args()


def extract_cbr(filename, tmpdirname):
    patoolib.extract_archive(filename, outdir=tmpdirname)


def extract_cbz(filename, tmpdirname):
    zip_file = zipfile.ZipFile(filename, "r")
    zip_file.extractall(tmpdirname)
    zip_file.close()

def extract_pdf(arguments, tmpdirname):
    result = pdf2jpg.convert_pdf2jpg(arguments.input, tmpdirname, dpi=300, pages="ALL")
    if not result:
        print("WIN ERROR 2 ? - You will probably have to install JAVA and restart terminal or system")


def fix_files(arguments):

    if os.path.splitext(arguments.input)[-1] == '.cbr':
        print("Extracting CBR...")
        if not os.path.exists(defaultOutputFolder):
            os.makedirs(defaultOutputFolder)
        extract_cbr(arguments.input, defaultOutputFolder)
    elif os.path.splitext(arguments.input)[-1] == '.cbz':
        print("Extracting CBZ...")
        if not os.path.exists(defaultOutputFolder):
            os.makedirs(defaultOutputFolder)
        extract_cbz(arguments.input, defaultOutputFolder)
    elif os.path.splitext(arguments.input)[-1] == '.cbz':
        print("Extracting PDF...")
        extract_pdf(arguments.input, defaultOutputFolder)
    elif os.path.isdir(arguments.input):
        print("Processing folder")
        shutil.copytree(arguments.input, defaultOutputFolder)
    else:
        print("Invalid input")
        return

    file_list = []

    # Fix all files in one folder with sub-folder names in each file.

    if not os.path.exists(arguments.output):
        os.makedirs(arguments.output)

    # Go through all images
    for root, dirs, files in os.walk(defaultOutputFolder, topdown=False):
        for file in sorted(files):
            
            # Get directory name of last folder in tree
            last_dir = root.split(os.sep)[-1].replace(" ", "_")

            # Get file extension
            file_ext = os.path.splitext(file)[-1]

            # Rename images is chosen (cbz don't like 1.jpg and 10.jpg so zeroes should be added)
            if arguments.dontrename:
                file_name = os.path.splitext(file)[0]
            else:
                file_name = "%03d%04d" % (int(''.join(filter(str.isdigit, last_dir))), int(''.join(filter(str.isdigit, file))))
            
            # Determine new file name and print it out to see the progress
            new_file_name = file_name + file_ext
            print(f"Creating {new_file_name}")

            # Determine source path for upcoming copy
            source = os.path.join(root, file)

            # Determine destination for upcoming copy
            destination = os.path.join(arguments.output, new_file_name)

            # Copy file and check if file already exist, and exit if duplicate, because we will miss a file if we overwrite.
            copyfile(source, destination)
            if destination in file_list:
                print("ERROR: Duplicate filename")
                sys.exit()
            
            # Add the file to a list of files to return
            file_list.append(destination)

            # Convert file to RGB (readers don't like files with alpha channels or something)
            im = Image.open(destination).convert('RGB')
            im.save(destination)
            im.close()

    # Remove folders
    """
    if os.path.exists(fullOutputPath):
        print("Clean up (%s)" % fullOutputPath)
        try:
            shutil.rmtree(fullOutputPath)
        except:
            print("Failed to remove %s" % fullOutputPath)
    """
    if os.path.exists(defaultOutputFolder):
        print("Clean up (%s)" % defaultOutputFolder)
        try:
            shutil.rmtree(defaultOutputFolder)
        except:
            print("Failed to remove %s" % defaultOutputFolder)

    return file_list


def create_cbz(arguments, file_list):

    """
    @brief    Create the cbz file output
    """

    # Print
    print("Creating a new CBZ file:")

    # Output file name and print
    out_file_name = os.path.splitext(arguments.input.split(os.sep)[-1])[0]
    input_file_path = arguments.input.replace(arguments.input.split(os.sep)[-1], "")
    print(input_file_path)
    print("    %s.cbz" % os.path.join(input_file_path, out_file_name))

    # Create a zip object
    zipObj = zipfile.ZipFile(os.path.join(input_file_path, out_file_name)+".cbz", "w")

    # Zip all files
    for file in file_list:
        zipObj.write(file, basename(file))
    zipObj.close()

    # Delete the output folder
    if os.path.exists(arguments.output):
        print("Clean up (%s)" % arguments.output)
        try:
            shutil.rmtree(arguments.output)
        except:
            print("Failed to remove %s" % arguments.output)


if __name__ == "__main__":

    """
    @brief    Main entry point
    """

    args = parser()

    files = fix_files(args)
    create_cbz(args, files)
