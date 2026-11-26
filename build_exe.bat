@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   BeatBar Difficulty Scorer - build script
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo Install Python 3.10+ and make sure "Add to PATH" is checked.
    pause
    exit /b 1
)

echo [1/2] Installing PyInstaller...
python -m pip install --upgrade pyinstaller numpy
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

echo.
echo [2/2] Building exe...
python -m PyInstaller --noconfirm --onefile --windowed ^
    --name BeatBarScore ^
    --paths . ^
    --distpath dist --workpath build_tmp ^
    beatbar_score\gui.py
if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo Done. Output: dist\BeatBarScore.exe
pause
