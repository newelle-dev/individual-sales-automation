@echo off
REM Quick runner for reports\package_consolidated.py (Windows)
setlocal
set REPORTS_DIR=%~dp0
set PROJECT_ROOT=%REPORTS_DIR%..\
REM Ensure PROJECT_ROOT has no trailing backslash issues
for %%I in ("%PROJECT_ROOT%") do set PROJECT_ROOT=%%~fI
set PYTHONPATH=%PROJECT_ROOT%
echo PYTHONPATH=%PYTHONPATH%

REM Default input and output paths inside reports/
set IN_DIR=%REPORTS_DIR%input
set OUT_FILE=%REPORTS_DIR%output\package_consolidated_by_group.csv

echo Running package_consolidated.py ...
py -u "%REPORTS_DIR%package_consolidated.py" "%IN_DIR%" "%OUT_FILE%"
if errorlevel 1 (
    echo.
    echo Script failed with exit code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
) else (
    echo.
    echo Report generated at %OUT_FILE%
    pause
)
endlocal
