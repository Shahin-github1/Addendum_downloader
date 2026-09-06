@echo off
title AMC Addendum Daily Downloader
cd /d "%~dp0"

echo ================================================================
echo          Starting Daily AMC Addendum Downloader
echo ================================================================
echo.

if exist "dist\AMC_Addendum_Downloader\AMC_Addendum_Downloader.exe" (
    echo [INFO] Running Standalone Executable...
    "dist\AMC_Addendum_Downloader\AMC_Addendum_Downloader.exe" %*
) else (
    echo [INFO] Running via Python...
    python main.py %*
)

echo.
echo ================================================================
echo    Process Completed. Check the downloads folder for today's files.
echo ================================================================
echo.
pause
