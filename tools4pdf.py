import os
import argparse
import img2pdf
import PyPDF2
from pprint import pprint

image_types = (".jpg", ".jpeg")


def arg_parser():

    """Parser function to get all the arguments

    Returns:
        Argument parser
    """

    description = ""

    # Construct the argument parse and parse the arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=description)
    parser.add_argument("-i", "--inputs", type=str, default=None, 
                        help="path to comic cbr, cbz, pdf or folder with images")
    parser.add_argument("-o", "--output", type=str, default="output", 
                        help="output filename")
    parser.add_argument("--ocr", action='store_true',
                        help="Do OCR on document")
    parser.add_argument("--ocr_only", action='store_true',
                        help="Do OCR on input document")
    parser.add_argument("-l", "--language", type=str, default="eng",
                        help="OCR language from Tesserect")
    print('\n' + str(parser.parse_args()) + '\n')

    return parser.parse_args()


def create_pdf(arguments):
    """Create images or pdf files to pdf

    Args:
        arguments: argument parser

    Returns:
        None
    """

    # Contains the list of all images and PDFs to be converted to a single PDF.
    image_list = []
    pdf_list = []

    folder = arguments.inputs

    # Find files
    for dir_path, _, filenames in os.walk(folder):
        for filename in filenames:
            full_path = os.path.join(dir_path, filename)
            if filename.endswith(image_types):
                image_list.append(full_path)
            elif filename.endswith(".pdf"):
                pdf_list.append(full_path)

    # Sort files
    image_list.sort()
    pdf_list.sort()

    pprint(pdf_list)

    # Handle the case where there are no images or PDFs
    if not image_list and not pdf_list:
        print("Error: No images or PDFs found in the specified folder.")
        return  # Exit the function if no valid files are found

    # Create a temporary PDF from images if there are images
    if image_list:
        with open("temp_images.pdf", "wb") as f:
            f.write(img2pdf.convert(image_list))
    else:
        # If no images are found, create an empty temporary PDF to keep the workflow intact
        with open("temp_images.pdf", "wb") as f:
            f.write(b"")  # Empty PDF file that won't cause an error

    # Merge all PDFs
    merger = PyPDF2.PdfMerger()

    # Add the converted images PDF only if there were images
    if image_list:
        merger.append("temp_images.pdf")

    # Add the other PDFs if available
    for pdf in pdf_list:
        merger.append(pdf)

    # Write out the merged PDF
    with open(arguments.output + ".pdf", "wb") as f:
        merger.write(f)

    # Clean up temporary file
    os.remove("temp_images.pdf")

    # If OCR is required, run OCR on the output PDF
    if arguments.ocr:
        create_ocr(arguments.output + ".pdf", arguments)


def create_ocr(file, arguments):

    """Add OCR to document

    Args:
        file: file to work on
        arguments: argument parser

    Returns:
        None
    """

    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)

    # If file is only filename, assume that the file is in root dir.
    if os.sep not in file:
        file = filepath

    command = f"ocrmypdf -l {arguments.language} --deskew --output-type pdf {file} {file.replace('.pdf', '_ocr.pdf')}"
     
    res = os.system(command)
 
    print("Returned Value: ", res)


if __name__ == "__main__":

    """ Main """

    args = arg_parser()

    if not args.ocr_only:
        create_pdf(args)
    elif args.ocr_only:
        create_ocr(args.inputs, args)
