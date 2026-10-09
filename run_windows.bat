@echo off
title AeroGuard AI Simulator
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -m venv .venv
) else (
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
pause
