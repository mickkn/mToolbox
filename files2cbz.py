import argparse
import concurrent.futures
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime
from os.path import basename

import patoolib
from PIL import Image
from pdf2jpg import pdf2jpg

Image.MAX_IMAGE_PIXELS = None  # disables the warning
from shutil import copyfile

default_output_folder = datetime.now().strftime("%Y%m%d_%H%M%S")
fullOutputPath = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), default_output_folder
)


def parser():
    """
    @brief    Parser function to get all the arguments
    """
    description = ""

    # Construct the argument parse and parse the arguments
    arguments = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=description
    )
    arguments.add_argument(
        "-i",
        "--input",
        nargs="+",
        default=None,
        help="path(s) to comics cbr, cbz, pdf or folder with images, or even folder with sub folders",
    )
    arguments.add_argument(
        "-o", "--output", type=str, default="output", help="path to output"
    )
    arguments.add_argument(
        "--dontrename",
        action="store_true",
        help="Name image files with included digits and added zeroes",
    )
    arguments.add_argument(
        "--onlyextract", action="store_true", help="Only extract files from input"
    )
    arguments.add_argument(
        "--silence", action="store_true", help="Don't do print outs."
    )
    arguments.add_argument(
        "--subfolders",
        action="store_true",
        help="Instead of using multiple inputs just use all sub folders in folder (creating multiple cbz files)",
    )
    arguments.add_argument(
        "--threads",
        type=int,
        default=1,
        help="Number of threads to use for processing",
    )

    print("\n" + str(arguments.parse_args()) + "\n")

    return arguments.parse_args()


def extract_cbr(filename, tmpdirname):
    patoolib.extract_archive(filename, outdir=tmpdirname)


def extract_cbz(filename, tmpdirname):
    zip_file = zipfile.ZipFile(filename, "r")
    zip_file.extractall(tmpdirname)
    zip_file.close()


def extract_pdf(filename, tmpdirname):
    result = pdf2jpg.convert_pdf2jpg(filename, tmpdirname, dpi=300, pages="ALL")
    if not result:
        print(
            "WIN ERROR 2 ? - You will probably have to install JAVA and restart terminal or system"
        )


def create_cbz(arguments, inputs, file_list, index):
    """
    @brief    Create the cbz file output
    """

    # Print
    print("Creating a new CBZ file:")

    # Output file name and print
    out_file_name = os.path.splitext(inputs.split(os.sep)[-1])[0]
    input_file_path = inputs.replace(inputs.split(os.sep)[-1], "")
    print(input_file_path)
    print("    %s.cbz" % os.path.join(input_file_path, out_file_name))

    # Create a zip object
    zip_obj = zipfile.ZipFile(os.path.join(input_file_path, out_file_name) + ".cbz", "w")

    # Zip all files
    for file in file_list:
        zip_obj.write(file, basename(file))
    zip_obj.close()

    # Delete the output folder
    if os.path.exists(arguments.output + str(index)):
        print(f"Clean up ({arguments.output + str(index)})")
        try:
            shutil.rmtree(arguments.output + str(index))
        except Exception as e:
            print(f"Failed to remove {arguments.output + str(index)} : {e}")


def fix_files(arguments, inputs, index):
    """Fix files

    Args:
        arguments: argument parser.
        inputs: input file or folder.
        index: index of input.

    Returns:
        None.
    """

    output_folder = default_output_folder + "_" + str(index)

    if os.path.splitext(inputs)[-1] == ".cbr":
        print("Extracting CBR...")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        if arguments.onlyextract:
            extract_cbr(inputs, os.path.splitext(inputs)[0])
            return
        else:
            extract_cbr(inputs, output_folder)
    elif os.path.splitext(inputs)[-1] == ".cbz":
        print("Extracting CBZ...")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        if arguments.onlyextract:
            extract_pdf(inputs, os.path.splitext(inputs)[0])
            return
        else:
            extract_cbz(inputs, output_folder)
    elif os.path.splitext(inputs)[-1] == ".pdf":
        print("Extracting PDF...")
        if arguments.onlyextract:
            extract_pdf(inputs, os.path.splitext(inputs)[0])
            return
        else:
            extract_pdf(inputs, output_folder)
    elif os.path.isdir(inputs):
        print("Processing folder")
        shutil.copytree(inputs, output_folder)
    else:
        print("Invalid input")
        return

    # Init a file list.
    file_list = []

    # Fix all files in one folder with sub-folder names in each file.
    if not os.path.exists(arguments.output + str(index)):
        os.makedirs(arguments.output + str(index))

    # Go through all images.
    for root, dirs, files in os.walk(output_folder, topdown=False):
        for file in sorted(files):
            # Get directory name of last folder in tree unless default_output_folder.
            if root.split(os.sep)[-1] == output_folder:
                last_dir = None
            else:
                last_dir = root.split(os.sep)[-1].replace(" ", "_")

            # Get file extension
            file_ext = os.path.splitext(file)[-1]

            # Rename images is chosen (cbz don't like 1.jpg and 10.jpg so zeroes should be added).
            if arguments.dontrename:
                file_name = os.path.splitext(file)[0]
            else:
                if last_dir is None:
                    # If 'last_dir' is None, extract digits from 'file' and format
                    # 'file_name' with leading zeros as a 4-digit number
                    file_digits = re.search(r"\d+", file)
                    file_name = "%04d" % (
                        int(file_digits.group()) if file_digits else 0
                    )
                else:
                    # If 'last_dir' is not None, extract digits from 'last_dir' and 'file'
                    # then format 'file_name' as a 3-digit number concatenated with a 4-digit number
                    last_dir_digits = re.search(r"\d+", last_dir)
                    file_digits = re.search(r"\d+", file)

                    last_dir_number = (
                        int(last_dir_digits.group()) if last_dir_digits else 0
                    )
                    file_number = int(file_digits.group()) if file_digits else 0

                    file_name = "%03d%04d" % (last_dir_number, file_number)

                    print(file_name)

            # Determine new file name and print it out to see the progress.
            new_file_name = file_name + file_ext
            if not arguments.silence:
                print(f"Creating {new_file_name}")

            # Determine source path for upcoming copy.
            source = os.path.join(root, file)

            # Determine destination for upcoming copy.
            destination = os.path.join(arguments.output + str(index), new_file_name)

            # Copy file and check if file already exist,
            # and exit if duplicate, because we will miss a file if we overwrite.
            copyfile(source, destination)
            if destination in file_list:
                print("ERROR: Duplicate filename")
                sys.exit()

            # Add the file to a list of files to return.
            file_list.append(destination)

            # Convert file to RGB (readers don't like files with alpha channels or something).
            im = Image.open(destination).convert("RGB")
            im.save(destination)
            im.close()

    # Remove folders
    if os.path.exists(output_folder):
        print("Clean up (%s)" % output_folder)
        try:
            shutil.rmtree(output_folder)
        except Exception as e:
            print(f"Failed to remove {output_folder} : {e}")

    if not args.onlyextract:
        create_cbz(args, inputs, file_list, index)


if __name__ == "__main__":
    """
    @brief    Main entry point
    """

    args = parser()

    threads = []

    # Handle multiple inputs.
    if "," in args.input[0]:
        args.input = args.input[0].split(",")

    # If sub folders are used, save all sub folders in the args.input
    elif args.subfolders:
        sub_folders = []
        input_dir = args.input[0]
        for sub_folder in os.listdir(input_dir):
            sub_folder_path = os.path.join(input_dir, sub_folder)
            if os.path.isdir(sub_folder_path):
                sub_folders.append(sub_folder_path)

        args.input = sub_folders

    max_threads = args.threads  # Maximum number of threads to run concurrently

    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        futures = []

        for item in args.input:
            future = executor.submit(fix_files, args, item, args.input.index(item))
            futures.append(future)

        # Wait for all threads to complete
        for future in concurrent.futures.as_completed(futures):
            result = future.result()

        # Optionally, you can check for exceptions in the results
        for future in futures:
            if future.exception() is not None:
                print(f"Thread raised an exception: {future.exception()}")

    print("Done")