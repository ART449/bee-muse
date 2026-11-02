@echo off
cd /d "%~dp0"
python run.py --open
if errorlevel 1 pause
