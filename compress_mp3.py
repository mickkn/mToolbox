"""Compress MP3 files with FFmpeg to make them smaller, e.g. for use on a website."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_BITRATE = "96k"
DEFAULT_SUFFIX = "_compressed"
SAMPLE_RATES = [22050, 32000, 44100, 48000]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Compress MP3 files by re-encoding them at a lower bitrate.",
    )
    parser.add_argument("inputs", nargs="+", help="MP3 files or folders containing MP3 files")
    parser.add_argument("-b", "--bitrate", default=DEFAULT_BITRATE, help="Target bitrate, e.g. 64k, 96k, 128k")
    parser.add_argument(
        "-q",
        "--vbr-quality",
        type=int,
        choices=range(0, 10),
        default=None,
        help="Use variable bitrate instead (0 = best/largest, 9 = worst/smallest). Overrides --bitrate",
    )
    parser.add_argument("-m", "--mono", action="store_true", help="Downmix to mono (roughly halves the size)")
    parser.add_argument("-r", "--sample-rate", type=int, choices=SAMPLE_RATES, default=None,
                        help="Resample audio to this rate in Hz")
    parser.add_argument("-o", "--output-dir", default=None, help="Output folder (default: next to the input file)")
    parser.add_argument("-s", "--suffix", default=DEFAULT_SUFFIX, help="Suffix added to output filenames")
    parser.add_argument("-y", "--overwrite", action="store_true", help="Overwrite existing output files")
    return parser.parse_args()


def detect_ffmpeg() -> str | None:
    """Locate an FFmpeg executable.

    Returns:
        Path to FFmpeg, or None if it could not be found.
    """
    env_value = os.environ.get("FFMPEG_BIN")
    if env_value is not None and Path(env_value).exists():
        return env_value

    repo_ffmpeg = REPO_ROOT / "ffmpeg.exe"
    if repo_ffmpeg.exists():
        return str(repo_ffmpeg)

    return shutil.which("ffmpeg")


def collect_files(inputs: list[str], suffix: str) -> list[Path]:
    """Expand the given inputs into a list of MP3 files.

    Args:
        inputs: File and folder paths given on the command line.
        suffix: Output suffix, used to skip files that were already compressed.

    Returns:
        The MP3 files to compress.
    """
    files = []
    for item in inputs:
        path = Path(item)
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*.mp3") if not p.stem.endswith(suffix)))
        elif path.is_file():
            files.append(path)
        else:
            print(f"Skipping '{item}': not found", file=sys.stderr)
    return files


def build_command(ffmpeg: str, source: Path, target: Path, args: argparse.Namespace) -> list[str]:
    """Build the FFmpeg command line for compressing one file.

    Args:
        ffmpeg: Path to the FFmpeg executable.
        source: The input MP3 file.
        target: The output MP3 file.
        args: The parsed command line arguments.

    Returns:
        The FFmpeg command as a list of arguments.
    """
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-stats", "-i", str(source)]
    command += ["-vn", "-map_metadata", "0", "-codec:a", "libmp3lame"]

    if args.vbr_quality is not None:
        command += ["-q:a", str(args.vbr_quality)]
    else:
        command += ["-b:a", args.bitrate]

    if args.mono:
        command += ["-ac", "1"]
    if args.sample_rate is not None:
        command += ["-ar", str(args.sample_rate)]

    command += ["-y" if args.overwrite else "-n", str(target)]
    return command


def format_size(num_bytes: int) -> str:
    """Format a byte count as megabytes.

    Args:
        num_bytes: Size in bytes.

    Returns:
        Human readable size string.
    """
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def compress_file(ffmpeg: str, source: Path, args: argparse.Namespace) -> bool:
    """Compress a single MP3 file and print the size reduction.

    Args:
        ffmpeg: Path to the FFmpeg executable.
        source: The input MP3 file.
        args: The parsed command line arguments.

    Returns:
        True if the file was compressed successfully, otherwise False.
    """
    output_dir = Path(args.output_dir) if args.output_dir is not None else source.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{source.stem}{args.suffix}.mp3"

    if target.exists() and args.overwrite is False:
        print(f"Skipping '{source.name}': '{target}' already exists (use -y to overwrite)")
        return False

    print(f"Compressing '{source.name}' -> '{target}'")
    result = subprocess.run(build_command(ffmpeg, source, target, args), check=False)
    if result.returncode != 0:
        print(f"FFmpeg failed on '{source}' (exit code {result.returncode})", file=sys.stderr)
        return False

    old_size = source.stat().st_size
    new_size = target.stat().st_size
    saved = 100 * (1 - new_size / old_size) if old_size > 0 else 0
    print(f"  {format_size(old_size)} -> {format_size(new_size)} ({saved:.0f}% smaller)")
    return True


def main() -> int:
    """Entry point.

    Returns:
        Process exit code.
    """
    args = parse_args()

    ffmpeg = detect_ffmpeg()
    if ffmpeg is None:
        print("FFmpeg was not found. Install FFmpeg or run install-ffmpeg.bat in the repo root.", file=sys.stderr)
        return 1

    files = collect_files(args.inputs, args.suffix)
    if len(files) == 0:
        print("No MP3 files to compress.", file=sys.stderr)
        return 1

    failures = sum(1 for source in files if compress_file(ffmpeg, source, args) is False)
    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
