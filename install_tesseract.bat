@echo off
setlocal EnableExtensions
set "CHOCO_EXE=choco"
set "HAS_TESS=0"
set "HAS_GS=0"
set "TESSDATA_DIR="
set "DAN_URL=https://github.com/tesseract-ocr/tessdata_fast/raw/main/dan.traineddata"

echo [1/6] Checking for Administrator rights...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: This script must be run as Administrator.
    echo Right-click this .bat file and choose "Run as administrator".
    pause
    exit /b 1
)

echo [2/6] Checking if Tesseract is already installed...
where tesseract >nul 2>&1
if %errorlevel% equ 0 (
    echo Tesseract is already installed and on PATH.
    set "HAS_TESS=1"
)

echo [3/6] Checking for Chocolatey...
where choco >nul 2>&1
if %errorlevel% neq 0 (
    echo Chocolatey not found. Installing Chocolatey...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    if %errorlevel% neq 0 (
        echo ERROR: Chocolatey installation failed.
        pause
        exit /b 1
    )
)

if exist "%ProgramData%\chocolatey\bin\choco.exe" (
    set "CHOCO_EXE=%ProgramData%\chocolatey\bin\choco.exe"
)

where choco >nul 2>&1
if %errorlevel% neq 0 (
    set "PATH=%PATH%;%ProgramData%\chocolatey\bin"
)

if not exist "%CHOCO_EXE%" (
    where choco >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: Chocolatey is still not available in this session.
        echo Open a new Administrator terminal and run this script again.
        pause
        exit /b 1
    )
)

if "%HAS_TESS%"=="0" (
    echo [4/6] Installing Tesseract via Chocolatey...
    "%CHOCO_EXE%" install tesseract -y --no-progress
    if %errorlevel% neq 0 (
        echo ERROR: Tesseract installation failed.
        pause
        exit /b 1
    )
) else (
    echo [4/6] Skipping Tesseract install.
)

echo [5/6] Checking if Ghostscript is already installed...
where gswin64c >nul 2>&1
if %errorlevel% equ 0 set "HAS_GS=1"
if "%HAS_GS%"=="0" (
    where gs >nul 2>&1
    if %errorlevel% equ 0 set "HAS_GS=1"
)

echo [6/6] Installing Danish Tesseract language data...
for /f "delims=" %%I in ('where tesseract 2^>nul') do (
    set "TESS_EXE=%%I"
    goto :found_tesseract
)

:found_tesseract
if not defined TESS_EXE (
    echo ERROR: Could not resolve tesseract executable path.
    pause
    exit /b 1
)

for %%I in ("%TESS_EXE%") do set "TESS_DIR=%%~dpI"
set "TESSDATA_DIR=%TESS_DIR%tessdata"

if not exist "%TESSDATA_DIR%" (
    echo ERROR: Tesseract tessdata folder was not found at "%TESSDATA_DIR%".
    pause
    exit /b 1
)

if exist "%TESSDATA_DIR%\dan.traineddata" (
    echo Danish language data already exists.
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri '%DAN_URL%' -OutFile '%TESSDATA_DIR%\dan.traineddata'"
    if %errorlevel% neq 0 (
        echo ERROR: Failed to download dan.traineddata.
        pause
        exit /b 1
    )
)

if "%HAS_GS%"=="0" (
    echo Installing Ghostscript via Chocolatey...
    "%CHOCO_EXE%" install ghostscript -y --no-progress
    if %errorlevel% neq 0 (
        echo ERROR: Ghostscript installation failed.
        pause
        exit /b 1
    )
) else (
    echo Ghostscript is already installed and on PATH.
)

echo.
echo Refreshing PATH for this session...
set "PATH=%PATH%;%ProgramFiles%\Tesseract-OCR;%ProgramFiles(x86)%\Tesseract-OCR"
for /d %%D in ("%ProgramFiles%\gs\gs*") do set "PATH=%PATH%;%%D\bin"

where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Tesseract may be installed, but not yet visible in this terminal.
    echo Close and reopen Command Prompt/PowerShell, then run: tesseract --version
    pause
    exit /b 0
)

where gswin64c >nul 2>&1
if %errorlevel% neq 0 (
    where gs >nul 2>&1
    if %errorlevel% neq 0 (
        echo WARNING: Ghostscript may be installed, but not yet visible in this terminal.
        echo Close and reopen Command Prompt/PowerShell, then run: gswin64c -v
        pause
        exit /b 0
    )
)

echo SUCCESS: OCR dependencies are installed.
tesseract --version
tesseract --list-langs | findstr /i /r "^dan$"
if %errorlevel% neq 0 (
    echo WARNING: Danish language not listed yet. Reopen terminal and run: tesseract --list-langs
) else (
    echo Danish language is installed.
)
gswin64c -v
pause
exit /b 0