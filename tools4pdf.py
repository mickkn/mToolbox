import os
import argparse
import img2pdf


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

    """Create images to pdf

    Args:
        arguments: argument parser

    Returns:

    """

    # Contains the list of all images to be converted to PDF.
    image_list = []

    folder = arguments.inputs

    # Find files
    for dir_path, _, filenames in os.walk(folder):
        for filename in [f for f in filenames if f.endswith(image_types)]:
            full_path = os.path.join(dir_path, filename)
            image_list.append(full_path)

    # Sort files
    # Sort the images by name.
    image_list.sort()
    for i in range(0, len(image_list)):
        print(image_list[i])

    # Convert images to PDF
    with open(arguments.output + ".pdf", "wb") as f:
        f.write(img2pdf.convert(image_list))

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
