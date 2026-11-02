@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist config.json (
  echo [!] config.json не найден — копирую из примера...
  copy config.example.json config.json >nul
  echo Открой config.json и вставь discord_token, потом запусти снова.
  pause
  exit /b 1
)
pip install -r requirements.txt
python bot.py
pause
