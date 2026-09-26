# Readme

For future self.  
Install [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)  
Install [Ghostscript](https://www.ghostscript.com/download/gsdnld.html)

## YouTube downloader

`youtube.py` downloads YouTube videos from the command line.

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Download the best video:

```powershell
python youtube.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Download audio only as MP3:

```powershell
python youtube.py "https://www.youtube.com/watch?v=VIDEO_ID" --audio-only
```

Save to a specific folder or filename:

```powershell
python youtube.py "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir downloads
python youtube.py "https://www.youtube.com/watch?v=VIDEO_ID" --audio-only --output my_track.mp3
```

`--audio-only` needs FFmpeg. You can install a repo-local `ffmpeg.exe` with:

```powershell
.\install-ffmpeg.bat
```

