@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python topilmadi. https://www.python.org/downloads/ dan o'rnating.
  echo O'rnatishda "Add Python to PATH" ni belgilang, keyin shu faylni qayta oching.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe (
  echo Birinchi marta: tayyorlanmoqda, 1-2 daqiqa kuting...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
:run
python bot.py
echo.
echo Bot to'xtadi. 5 soniyadan keyin qayta ishga tushadi (to'xtatish: oynani yoping).
timeout /t 5 >nul
goto run
