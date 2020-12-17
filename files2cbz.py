import os
from os.path import basename
#import comic2pdf
import argparse
from datetime import datetime
from shutil import copyfile
import shutil
from pathlib import Path
import zipfile
import patoolib

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
    parser.add_argument("-i", "--input", type=str, default=None, help="path to comic")
    parser.add_argument("-o", "--output", type=str, default="output", help="path to output")
    print('\n' + str(parser.parse_args()) + '\n')

    return parser.parse_args()


def extract_cbr(filename, tmpdirname):
    patoolib.extract_archive(filename, outdir=tmpdirname)


def extract_cbz(filename, tmpdirname):
    zip_file = zipfile.ZipFile(filename, "r")
    zip_file.extractall(tmpdirname)
    zip_file.close()


def fix_files(arguments):

    extract_cbr(arguments.input, defaultOutputFolder)

    file_list = []

    # Fix all files in one folder with sub-folder names in each file.

    if not os.path.exists(arguments.output):
        os.makedirs(arguments.output)

    for root, dirs, files in os.walk(defaultOutputFolder, topdown=False):
        for file in sorted(files):
            #print(root+file)
            last_dir = root.split(os.sep)[-1].replace(" ", "_")
            file_ext = file.split(".")[-1]
            file_name = "%04d" % int(file.split(".")[0])
            #print(f"Lastdir: {last_dir}")
            #print(f"Fileext: {file_ext}")
            #print(f"Filename: {file_name}")
            new_file_name = f"{last_dir}_{file_name}.{file_ext}"
            print(f"Creating {new_file_name}")
            source = os.path.join(root, file)
            destination = os.path.join(arguments.output, new_file_name)
            copyfile(source, destination)
            file_list.append(destination)

            # Convert file to RGB
            im = Image.open(destination)
            if im.mode != 'RGB':
                im.convert('RGB')
            im.save(destination)
            #print(fullOutputPath)

    if os.path.exists(fullOutputPath):
        print("Clean up (%s)" % fullOutputPath)
        try:
            shutil.rmtree(fullOutputPath)
        except:
            print("Failed to remove %s" % fullOutputPath)

    return file_list


def create_cbz(arguments, file_list):
    print("Creating a new CBZ file:")

    #print(file_list)
    out_file_name = os.path.splitext(arguments.input.split(os.sep)[-1])[0]
    print("    %s.cbz" % out_file_name)
    zipObj = zipfile.ZipFile(out_file_name+".cbz", "w")
    for file in file_list:
        zipObj.write(file, basename(file))
    zipObj.close()
    """
    if os.path.exists(arguments.output):
        print("Clean up (%s)" % arguments.output)
        try:
            shutil.rmtree(arguments.output)
        except:
            print("Failed to remove %s" % arguments.output)
    """

if __name__ == "__main__":

    """
    @brief    Main entry point
    """

    args = parser()

    files = fix_files(args)
    create_cbz(args, files)
