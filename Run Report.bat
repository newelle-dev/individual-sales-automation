@echo off
setlocal enabledelayedexpansion

title Individual Sales Automation Runner

echo ======================================
echo   Individual Sales Automation Runner
echo ======================================
echo.

rem 1. Check if input directory exists
if not exist "input" (
    echo [ERROR] The 'input' folder was not found.
    echo Please make sure this file is in the project root folder.
    echo.
    pause
    exit /b 1
)

rem 2. Check if input directory contains CSV files
dir /b "input\*.csv" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No CSV files found in the 'input' folder.
    echo Please place your Wessconnect export CSV files into 'input\' and try again.
    echo.
    dir /b "input\*.xlsx" "input\*.xls" >nul 2>&1
    if not errorlevel 1 (
        echo [WARNING] Found Excel files (.xlsx/.xls) in 'input\'.
        echo Wessconnect exports must be saved/exported in CSV format (.csv).
        echo.
    )
    pause
    exit /b 1
)

if not exist "output" mkdir "output"

rem 3. Detect Python executable (.venv first, then py launcher, then python)
set PYTHON_CMD=

if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
    echo Using virtual environment Python (.venv)...
) else (
    where py >nul 2>&1
    if !errorlevel!==0 (
        set PYTHON_CMD=py
    ) else (
        where python >nul 2>&1
        if !errorlevel!==0 (
            set PYTHON_CMD=python
        )
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python was not found on this computer.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo and make sure "Add Python to PATH" is enabled during installation.
    echo.
    pause
    exit /b 1
)

echo Running report pipeline...
echo.
%PYTHON_CMD% main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to generate report. Please check the messages above.
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ======================================
echo   [SUCCESS] Report Generated Successfully!
echo   Output: output\stylist_sales_pivot.csv
echo ======================================
echo.
pause
exit /b 0
