import os
import argparse


def create_folders(common_name, start_number, end_number, num_digits):
    for number in range(start_number, end_number + 1):
        folder_name = f"{common_name}_{str(number).zfill(num_digits)}"
        os.makedirs(folder_name, exist_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create multiple folders with common name and incremented number.")
    parser.add_argument("common_name", help="Common name for the folders")
    parser.add_argument("start_number", type=int, help="Starting number")
    parser.add_argument("end_number", type=int, help="Ending number")
    parser.add_argument("--num_digits", type=int, default=2, help="Number of digits for the incremented number (default: 2)")

    args = parser.parse_args()

    create_folders(args.common_name, args.start_number, args.end_number, args.num_digits)