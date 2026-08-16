@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Download and place ffmpeg.exe and ffplay.exe in this repository root.
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "OUT_EXE=%ROOT%\ffmpeg.exe"
set "OUT_FFPLAY=%ROOT%\ffplay.exe"
set "TMPDIR=%TEMP%\trackerl_ffmpeg_%RANDOM%%RANDOM%"
set "ZIP=%TMPDIR%\ffmpeg.zip"
set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

if /I "%~1"=="--help" goto :help
if /I "%~1"=="-h" goto :help
if /I "%~1"=="--dry-run" goto :dryrun

echo [1/4] Preparing temp folder...
mkdir "%TMPDIR%" >nul 2>&1
if errorlevel 1 (
  echo [error] Could not create temp folder: "%TMPDIR%"
  exit /b 1
)

echo [2/4] Downloading FFmpeg zip...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%ZIP%'"
if errorlevel 1 (
  echo [error] Download failed.
  goto :cleanup_fail
)

echo [3/4] Extracting archive...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Expand-Archive -Path '%ZIP%' -DestinationPath '%TMPDIR%\extract' -Force"
if errorlevel 1 (
  echo [error] Extraction failed.
  goto :cleanup_fail
)

echo [4/4] Locating ffmpeg.exe/ffplay.exe and copying to repo root...
set "FOUND_FFMPEG="
for /f "delims=" %%F in ('dir /s /b "%TMPDIR%\extract\ffmpeg.exe" ^| findstr /i "\\bin\\ffmpeg.exe$"') do (
  if not defined FOUND_FFMPEG set "FOUND_FFMPEG=%%F"
)

if not defined FOUND_FFMPEG (
  echo [error] Could not find ffmpeg.exe inside archive.
  goto :cleanup_fail
)

copy /Y "%FOUND_FFMPEG%" "%OUT_EXE%" >nul
if errorlevel 1 (
  echo [error] Failed to copy ffmpeg.exe to "%OUT_EXE%".
  goto :cleanup_fail
)

if not exist "%OUT_EXE%" (
  echo [error] ffmpeg.exe was not found at "%OUT_EXE%" after copy.
  goto :cleanup_fail
)

set "FOUND_FFPLAY="
for /f "delims=" %%F in ('dir /s /b "%TMPDIR%\extract\ffplay.exe" ^| findstr /i "\\bin\\ffplay.exe$"') do (
  if not defined FOUND_FFPLAY set "FOUND_FFPLAY=%%F"
)

if not defined FOUND_FFPLAY (
  echo [error] Could not find ffplay.exe inside archive.
  goto :cleanup_fail
)

copy /Y "%FOUND_FFPLAY%" "%OUT_FFPLAY%" >nul
if errorlevel 1 (
  echo [error] Failed to copy ffplay.exe to "%OUT_FFPLAY%".
  goto :cleanup_fail
)

if not exist "%OUT_FFPLAY%" (
  echo [error] ffplay.exe was not found at "%OUT_FFPLAY%" after copy.
  goto :cleanup_fail
)

echo [ok] Source: "!FOUND_FFMPEG!"
echo [ok] Source: "!FOUND_FFPLAY!"
echo [ok] Installed: "%OUT_EXE%"
echo [ok] Installed: "%OUT_FFPLAY%"
echo [hint] Use with: set FFMPEG_BIN=%OUT_EXE%
goto :cleanup_ok

:dryrun
echo [dry-run] Would download from: %FFMPEG_URL%
echo [dry-run] Would write to: %OUT_EXE%
echo [dry-run] Would write to: %OUT_FFPLAY%
exit /b 0

:help
echo Usage:
echo   install-ffmpeg.bat
echo   install-ffmpeg.bat --dry-run
echo   install-ffmpeg.bat --help
exit /b 0

:cleanup_fail
set "RC=1"
goto :cleanup

:cleanup_ok
set "RC=0"

:cleanup
if exist "%TMPDIR%" rmdir /S /Q "%TMPDIR%" >nul 2>&1
exit /b %RC%

