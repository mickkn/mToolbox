import argparse
import os
import shutil
import sys
import threading
import zipfile
from datetime import datetime
from os.path import basename

import patoolib
from PIL import Image
from pdf2jpg import pdf2jpg

Image.MAX_IMAGE_PIXELS = None   # disables the warning
from shutil import copyfile

defaultOutputFolder = datetime.now().strftime("%Y%m%d_%H%M%S")
fullOutputPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), defaultOutputFolder)


def parser():
    """
    @brief    Parser function to get all the arguments
    """
    description = ""

    # Construct the argument parse and parse the arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=description)
    parser.add_argument("-i", "--input", nargs='+', default=None, 
                        help="path(s) to comics cbr, cbz, pdf or folder with images")
    parser.add_argument("-o", "--output", type=str, default="output", 
                        help="path to output")
    parser.add_argument("--dontrename", action='store_true',
                        help="Name image files with included digits and added zeroes")
    parser.add_argument("--onlyextract", action='store_true',
                        help="Only extract files from input")
    parser.add_argument("--silence", action='store_true',
                        help="Don't do print outs.")
    parser.add_argument("--subfolders", action='store_true',
                        help="Instead of using multiple inputs just use all sub folders in folder")
    #parser.add_argument("--subfiles", action='store_true',
    #                    help="Instead of using multiple inputs just use all sub files in folder")
    print('\n' + str(parser.parse_args()) + '\n')

    return parser.parse_args()


def extract_cbr(filename, tmpdirname):
    patoolib.extract_archive(filename, outdir=tmpdirname)


def extract_cbz(filename, tmpdirname):
    zip_file = zipfile.ZipFile(filename, "r")
    zip_file.extractall(tmpdirname)
    zip_file.close()


def extract_pdf(filename, tmpdirname):
    result = pdf2jpg.convert_pdf2jpg(filename, tmpdirname, dpi=300, pages="ALL")
    if not result:
        print("WIN ERROR 2 ? - You will probably have to install JAVA and restart terminal or system")


def create_cbz(arguments, input, file_list, index):

    """
    @brief    Create the cbz file output
    """

    # Print
    print("Creating a new CBZ file:")

    # Output file name and print
    out_file_name = os.path.splitext(input.split(os.sep)[-1])[0]
    input_file_path = input.replace(input.split(os.sep)[-1], "")
    print(input_file_path)
    print("    %s.cbz" % os.path.join(input_file_path, out_file_name))

    # Create a zip object
    zipObj = zipfile.ZipFile(os.path.join(input_file_path, out_file_name)+".cbz", "w")

    # Zip all files
    for file in file_list:
        zipObj.write(file, basename(file))
    zipObj.close()

    # Delete the output folder
    if os.path.exists(arguments.output+str(index)):
        print(f"Clean up ({arguments.output + str(index)})")
        try:
            shutil.rmtree(arguments.output+str(index))
        except:
            print("Failed to remove %s" % arguments.output+str(index))


def fix_files(arguments, input, index):

    outputFolder = defaultOutputFolder+"_"+str(index)

    if os.path.splitext(input)[-1] == '.cbr':
        print("Extracting CBR...")
        if not os.path.exists(outputFolder):
            os.makedirs(outputFolder)
        if arguments.onlyextract:
            extract_cbr(input, os.path.splitext(input)[0])
            return
        else:
            extract_cbr(input, outputFolder)
    elif os.path.splitext(input)[-1] == '.cbz':
        print("Extracting CBZ...")
        if not os.path.exists(outputFolder):
            os.makedirs(outputFolder)
        if arguments.onlyextract:
            extract_pdf(input, os.path.splitext(input)[0])
            return
        else:
            extract_cbz(input, outputFolder)
    elif os.path.splitext(input)[-1] == '.pdf':
        print("Extracting PDF...")
        if arguments.onlyextract:
            extract_pdf(input, os.path.splitext(input)[0])
            return
        else:
            extract_pdf(input, outputFolder)
    elif os.path.isdir(input):
        print("Processing folder")
        shutil.copytree(input, outputFolder)
    else:
        print("Invalid input")
        return

    # Init a file list
    file_list = []

    # Fix all files in one folder with sub-folder names in each file.

    if not os.path.exists(arguments.output+str(index)):
        os.makedirs(arguments.output+str(index))

    # Go through all images
    for root, dirs, files in os.walk(outputFolder, topdown=False):
        for file in sorted(files):
            
            # Get directory name of last folder in tree unless defaultOutputFolder
            if root.split(os.sep)[-1] == outputFolder:
                last_dir = None
            else:
                last_dir = root.split(os.sep)[-1].replace(" ", "_")

            # Get file extension
            file_ext = os.path.splitext(file)[-1]

            # Rename images is chosen (cbz don't like 1.jpg and 10.jpg so zeroes should be added)
            if arguments.dontrename:
                file_name = os.path.splitext(file)[0]
            else:
                if last_dir == None:
                    file_name = "%04d" % (int(''.join(filter(str.isdigit, file))))
                else:
                    file_name = "%03d%04d" % (int(''.join(filter(str.isdigit, last_dir))), int(''.join(filter(str.isdigit, file))))
            
            # Determine new file name and print it out to see the progress
            new_file_name = file_name + file_ext
            if not arguments.silence:
                print(f"Creating {new_file_name}")

            # Determine source path for upcoming copy
            source = os.path.join(root, file)

            # Determine destination for upcoming copy
            destination = os.path.join(arguments.output+str(index), new_file_name)

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
    if os.path.exists(outputFolder):
        print("Clean up (%s)" % outputFolder)
        try:
            shutil.rmtree(outputFolder)
        except:
            print("Failed to remove %s" % outputFolder)

    if not args.onlyextract:
        create_cbz(args, input, file_list, index)


if __name__ == "__main__":

    """
    @brief    Main entry point
    """

    args = parser()

    threads = []

    # If sub folders are used, save all sub folders in the args.input
    if args.subfolders:
        sub_folders = []
        for sub_folder, _, _ in os.walk(args.input[0]):
            if sub_folder is not args.input[0]:
                print(sub_folder)
                sub_folders.append(sub_folder)
        args.input = sub_folders

    for item in args.input:
        thread = threading.Thread(target=fix_files, args=(args, item, args.input.index(item)))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

        #files = fix_files(args, item)
        #if not args.onlyextract:
        #    create_cbz(args, item, files)
