@echo off
REM One-click runner for main.py
chcp 65001 >nul
cd /d "%~dp0"
python "%~dp0main.py" %*
pause