import argparse
import os
import shutil
import sys
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


DEFAULT_TEMPLATE = "%(title).200s [%(id)s].%(ext)s"
REPO_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
		description="Download YouTube videos or save audio only.",
	)
	parser.add_argument("url", nargs="?", help="YouTube video or playlist URL")
	parser.add_argument("-u", "--url", dest="url_option", help="YouTube video or playlist URL")
	parser.add_argument(
		"-o",
		"--output",
		default=None,
		help="Output filename or yt-dlp template. A missing extension becomes .%%(ext)s.",
	)
	parser.add_argument(
		"--output-dir",
		default=".",
		help="Folder where the downloaded file(s) should be saved",
	)
	parser.add_argument(
		"-a",
		"--audio-only",
		action="store_true",
		help="Download audio only and convert it with FFmpeg",
	)
	parser.add_argument(
		"--audio-format",
		default="mp3",
		choices=["mp3", "m4a", "wav", "flac", "opus", "vorbis"],
		help="Audio format used with --audio-only",
	)
	parser.add_argument(
		"-f",
		"--format",
		default=None,
		help="Custom yt-dlp format selector for video downloads",
	)
	parser.add_argument(
		"--playlist",
		action="store_true",
		help="Allow downloading every item when the URL points to a playlist",
	)
	parser.add_argument(
		"--write-thumbnail",
		action="store_true",
		help="Save the video thumbnail alongside the download",
	)
	parser.add_argument(
		"--write-description",
		action="store_true",
		help="Save the video description as a text file",
	)
	parser.add_argument(
		"--verbose",
		action="store_true",
		help="Show yt-dlp debug output",
	)
	parser.add_argument(
		"--list-formats",
		action="store_true",
		help="List available formats for the URL and exit",
	)

	args = parser.parse_args()
	args.url = resolve_url(args.url, args.url_option, parser)
	return args


def resolve_url(positional_url: str | None, option_url: str | None, parser: argparse.ArgumentParser) -> str:
	if positional_url and option_url and positional_url != option_url:
		parser.error("Provide the URL only once, either positionally or with --url.")

	url = positional_url or option_url
	if not url:
		parser.error("A YouTube URL is required.")

	return url


def detect_ffmpeg_location() -> str | None:
	env_value = os.environ.get("FFMPEG_BIN")
	if env_value:
		env_path = Path(env_value).expanduser()
		if env_path.exists():
			return str(env_path)

	repo_ffmpeg = REPO_ROOT / "ffmpeg.exe"
	if repo_ffmpeg.exists():
		return str(repo_ffmpeg)

	system_ffmpeg = shutil.which("ffmpeg")
	if system_ffmpeg:
		return system_ffmpeg

	return None


def has_ffmpeg(ffmpeg_location: str | None) -> bool:
	return bool(ffmpeg_location)


def build_output_template(output: str | None, output_dir: str) -> str:
	output_directory = Path(output_dir).expanduser()
	output_directory.mkdir(parents=True, exist_ok=True)

	if not output:
		return str(output_directory / DEFAULT_TEMPLATE)

	if "%(" in output:
		return str(output_directory / output)

	output_path = Path(output).expanduser()
	if not output_path.is_absolute():
		output_path = output_directory / output_path

	suffix = output_path.suffix
	if suffix:
		output_path = output_path.with_suffix("")

	return f"{output_path}.%(ext)s"


def progress_hook(status: dict) -> None:
	state = status.get("status")

	if state == "downloading":
		percent = status.get("_percent_str", "").strip()
		speed = status.get("_speed_str", "").strip()
		eta = status.get("_eta_str", "").strip()
		details = " | ".join(part for part in [percent, speed, eta] if part)
		if details:
			print(details)
	elif state == "finished":
		filename = status.get("filename") or "download"
		print(f"Finished downloading source stream: {filename}")


def get_explicit_output_path(args: argparse.Namespace) -> str | None:
	if not args.output or "%(" in args.output:
		return None

	output_directory = Path(args.output_dir).expanduser()
	output_path = Path(args.output).expanduser()
	if not output_path.is_absolute():
		output_path = output_directory / output_path

	if args.audio_only:
		return str(output_path.with_suffix(f".{args.audio_format}"))

	if output_path.suffix:
		return str(output_path)

	return None


def build_ydl_options(args: argparse.Namespace) -> dict:
	ffmpeg_location = detect_ffmpeg_location()
	output_template = build_output_template(args.output, args.output_dir)

	options = {
		"outtmpl": output_template,
		"noplaylist": not args.playlist,
		"quiet": not args.verbose,
		"no_warnings": not args.verbose,
		"progress_hooks": [] if args.verbose else [progress_hook],
		"writethumbnail": args.write_thumbnail,
		"writedescription": args.write_description,
	}

	if not args.verbose:
		options["noprogress"] = True

	if ffmpeg_location:
		options["ffmpeg_location"] = ffmpeg_location

	if args.list_formats:
		options["listformats"] = True
		return options

	if args.audio_only:
		if not has_ffmpeg(ffmpeg_location):
			raise RuntimeError(
				"FFmpeg is required for --audio-only. Install FFmpeg or run install-ffmpeg.bat in the repo root."
			)

		options.update(
			{
				"format": "bestaudio/best",
				"postprocessors": [
					{
						"key": "FFmpegExtractAudio",
						"preferredcodec": args.audio_format,
						"preferredquality": "0",
					}
				],
			}
		)
		return options

	if args.format:
		options["format"] = args.format
	elif has_ffmpeg(ffmpeg_location):
		options["format"] = "bestvideo*+bestaudio/best"
		options["merge_output_format"] = "mp4"
	else:
		print("FFmpeg was not found, falling back to a single-file best stream download.")
		options["format"] = "best"

	return options


def download_media(args: argparse.Namespace) -> int:
	options = build_ydl_options(args)

	try:
		with YoutubeDL(options) as ydl:
			result = ydl.download([args.url])
		explicit_output_path = get_explicit_output_path(args)
		if result == 0 and explicit_output_path:
			print(f"Saved to: {explicit_output_path}")
		return 0 if result == 0 else result
	except DownloadError as exc:
		print(f"Download failed: {exc}", file=sys.stderr)
		return 1
	except Exception as exc:
		print(f"Error: {exc}", file=sys.stderr)
		return 1


def main() -> int:
	args = parse_args()
	return download_media(args)


if __name__ == "__main__":
	raise SystemExit(main())

