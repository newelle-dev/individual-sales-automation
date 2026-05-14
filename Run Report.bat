@echo off
setlocal

echo ======================================
echo   Individual Sales Automation Runner
echo ======================================
echo.

if not exist "input" (
  echo [ERROR] The input folder was not found.
  echo Please make sure this file is in the project root folder.
  echo.
  pause
  exit /b 1
)

if not exist "output" mkdir "output"

where py >nul 2>&1
if %errorlevel%==0 (
  echo Running report with Python launcher...
  py main.py
  goto :after_run
)

where python >nul 2>&1
if %errorlevel%==0 (
  echo Running report with python...
  python main.py
  goto :after_run
)

echo [ERROR] Python was not found on this computer.
echo Please install Python from https://www.python.org/downloads/
echo and make sure "Add Python to PATH" is enabled.
echo.
pause
exit /b 1

:after_run
echo.
if %errorlevel%==0 (
  echo [SUCCESS] Report generated.
  echo Output file: output\stylist_sales_pivot.csv
) else (
  echo [ERROR] Failed to generate report.
  echo Please check the messages above.
)
echo.
pause
exit /b %errorlevel%
