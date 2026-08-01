@echo off
setlocal enabledelayedexpansion

title Package Consolidated Report Runner

set REPORTS_DIR=%~dp0
set PROJECT_ROOT=%REPORTS_DIR%..\
for %%I in ("%PROJECT_ROOT%") do set PROJECT_ROOT=%%~fI
set PYTHONPATH=%PROJECT_ROOT%

echo ======================================
echo   Package Consolidated Report Runner
echo ======================================
echo.

set IN_DIR=%REPORTS_DIR%input
set OUT_DIR=%REPORTS_DIR%output
set OUT_FILE=%OUT_DIR%\package_consolidated_by_group.csv

rem If reports/input has no CSV files, check root input directory as fallback
dir /b "%IN_DIR%\*.csv" >nul 2>&1
if errorlevel 1 (
    if exist "%PROJECT_ROOT%\input" (
        dir /b "%PROJECT_ROOT%\input\*.csv" >nul 2>&1
        if not errorlevel 1 (
            echo Note: Using root 'input' directory as input source.
            set IN_DIR=%PROJECT_ROOT%\input
        )
    )
)

if not exist "%IN_DIR%" (
    echo [ERROR] Input directory '%IN_DIR%' missing.
    echo.
    pause
    exit /b 1
)

dir /b "%IN_DIR%\*.csv" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No CSV files found in '%IN_DIR%'.
    echo Please place Wessconnect export CSVs in 'reports\input\' or root 'input\' and try again.
    echo.
    pause
    exit /b 1
)

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

set PYTHON_CMD=
if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    set PYTHON_CMD="%PROJECT_ROOT%\.venv\Scripts\python.exe"
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
    echo Please install Python 3.8+.
    echo.
    pause
    exit /b 1
)

%PYTHON_CMD% -u "%REPORTS_DIR%package_consolidated.py" "%IN_DIR%" "%OUT_FILE%"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Report generation failed (Exit code: %errorlevel%).
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ======================================
echo   [SUCCESS] Package Report Generated!
echo   Output: %OUT_FILE%
echo ======================================
echo.
pause
endlocal
