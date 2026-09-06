@echo off
echo ================================================================
echo    Building AMC Addendum Downloader Windows Executable (.exe)
echo ================================================================
echo.

python -m PyInstaller --noconfirm --onedir --name "AMC_Addendum_Downloader" ^
    --add-data "config;config" ^
    --hidden-import "openpyxl" ^
    --hidden-import "lxml" ^
    --hidden-import "lxml.html" ^
    --hidden-import "requests" ^
    --hidden-import "urllib3" ^
    --hidden-import "selenium" ^
    --hidden-import "engine" ^
    --hidden-import "engine.date_utils" ^
    --hidden-import "engine.db" ^
    --hidden-import "engine.downloader" ^
    --hidden-import "engine.excel_reporter" ^
    --hidden-import "engine.extractor" ^
    main.py

if not exist "dist\AMC_Addendum_Downloader\config" mkdir "dist\AMC_Addendum_Downloader\config"
copy /Y "config\amc_catalog.json" "dist\AMC_Addendum_Downloader\config\amc_catalog.json"

echo.
echo ================================================================
echo    Build Completed Successfully!
echo    Executable Location: dist\AMC_Addendum_Downloader\AMC_Addendum_Downloader.exe
echo ================================================================
