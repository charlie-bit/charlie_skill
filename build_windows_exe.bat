@echo off
setlocal

cd /d %~dp0

where python >nul 2>nul
if errorlevel 1 (
  echo python not found
  exit /b 1
)

if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install pyinstaller requests beautifulsoup4

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name "Charlie Skill" ^
  --add-data "skills/company-filter/data;seed_data" ^
  "skills/company-filter-refresh/refresh.py"

echo.
echo Windows executable created:
echo   %CD%\dist\Charlie Skill.exe
