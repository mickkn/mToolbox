import argparse
import subprocess

import cv2
from tqdm import tqdm


def arg_parser():
    """Parser function to get all the arguments

    Returns:
        Argument parser
    """

    description = ""

    # Construct the argument parse and parse the arguments
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=description
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        default=None,
        required=True,
        help="Source video path"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output.mp4",
        help="Scaled video path"
    )
    parser.add_argument(
        "-r", "--resolution",
        type=int,
        nargs="+",
        metavar="Desired video resolution",
        default=[1920, 1080],
        help="Desired video output resolution. e.g. 1920 1080",
    )

    print("\n" + str(parser.parse_args()) + "\n")

    return parser.parse_args()


def scale_video(source_video_path, up_scaled_video_path, scaling_resolution):
    """Function to scale video.

    Args:
        source_video_path: Path to the source video.
        up_scaled_video_path: Path to the scaled video.
        scaling_resolution: Tuple containing (width, height) of the desired resolution.

    Returns:

    """
    video_source_name = source_video_path
    source_video = cv2.VideoCapture(video_source_name)
    dest_video = up_scaled_video_path
    source_fps = source_video.get(cv2.CAP_PROP_FPS)
    total_frames = int(source_video.get(cv2.CAP_PROP_FRAME_COUNT))
    video_format = cv2.VideoWriter_fourcc(*"H264")
    scaled_video = cv2.VideoWriter(
        dest_video, video_format, source_fps, scaling_resolution
    )
    print("\nRescaling...........\n")
    pbar = tqdm(total=total_frames)
    while True:
        ret, frame = source_video.read()
        if ret:
            b = cv2.resize(
                frame, scaling_resolution, fx=0, fy=0, interpolation=cv2.INTER_CUBIC
            )
            scaled_video.write(b)
            pbar.update(1)
        else:
            pbar.close()
            break
    source_video.release()
    scaled_video.release()
    cv2.destroyAllWindows()
    try:
        p = subprocess.Popen(
            ["ffprobe", "-show_streams", "-print_format", "json", source_video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        streams = p.communicate()[0]
        streams = streams.decode("utf-8")
        if "audio" in streams.lower():
            print("\nExtracting audio from source video.........\n")
            subprocess.call(["ffmpeg", "-i", source_video_path, "sourceaudio.mp3"])
            print("\nMerging source audio and upscaled video.........\n")
            subprocess.call(
                [
                    "ffmpeg",
                    "-i",
                    dest_video,
                    "-i",
                    "sourceaudio.mp3",
                    "-map",
                    "0:0",
                    "-map",
                    "1:0",
                    up_scaled_video_path,
                ]
            )
    except Exception as e:
        print(e)
        print("You will have to install ffprobe and ffmpeg to merge audio stream.")
        print("Get them here: https://ffmpeg.org/download.html")
        print("Install them to PATH or just place the binaries in the same folder as this script.")
    else:
        print("\nNo audio stream found.........\n")


if __name__ == '__main__':

    args = arg_parser()

    scale_video(args.input, args.output, tuple(args.resolution))