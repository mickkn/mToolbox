import argparse
from moviepy import VideoFileClip

def video_to_audio(input_path, output_path):
    with VideoFileClip(input_path) as video:
        audio = video.audio
        if audio is None:
            raise ValueError("No audio stream found in the video.")
        audio.write_audiofile(output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert video to audio (mp3).")
    parser.add_argument("-i", "--input", required=True, help="Input video file path")
    parser.add_argument("-o", "--output", default="output.mp3", help="Output audio file path (default: output.mp3)")
    args = parser.parse_args()

    try:
        video_to_audio(args.input, args.output)
        print(f"Audio saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}")