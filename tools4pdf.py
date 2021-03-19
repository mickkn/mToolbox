import os
import argparse
import img2pdf
import ocrmypdf


image_types = (".jpg", ".jpeg")


def parser():

    """
    @brief    Parser function to get all the arguments
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
    print('\n' + str(parser.parse_args()) + '\n')

    return parser.parse_args()


def create_pdf(args):

    """
    @brief    Create images to pdf
    """
    
    imagelist = []                                                 # Contains the list of all images to be converted to PDF.

    folder = args.inputs
    output_file = args.output                                  

    # Find files
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in [f for f in filenames if f.endswith(image_types)]:
            full_path = os.path.join(dirpath, filename)
            imagelist.append(full_path)

    # Sort files
    imagelist.sort()                                               # Sort the images by name.
    for i in range(0, len(imagelist)):
        print(imagelist[i])

    # Convert images to PDF
    with open(args.output + ".pdf","wb") as f:
        f.write(img2pdf.convert(imagelist, dpi=600))

    if args.ocr:
        create_ocr(args.output + ".pdf")


def create_ocr(file):

    """
    @brief    Add OCR to document
    """
    
    ocrmypdf.ocr(language="dan", progress_bar=True, use_threads=True, deskew=True, input_file=file, output_file=file.replace(".pdf", "_orc.pdf"))


if __name__ == "__main__":

    """
    @brief    Main entry point
    """

    args = parser()

    if not args.ocr_only:
        create_pdf(args)
    elif args.ocr_only:
        create_ocr(args.inputs)