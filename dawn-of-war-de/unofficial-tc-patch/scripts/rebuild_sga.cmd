@echo off
REM =============================================================================
REM rebuild_sga.cmd — Windows batch script to repack SGA using Archive.exe
REM 
REM This script MUST be run from Windows Command Prompt (not WSL2)
REM Run from repository root: dawn-of-war-de\unofficial-tc-patch\
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo WH40K DoW:DE -- SGA Rebuild (Windows native)
echo.

REM Configuration
set "GAME_DIR=D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition"
set "ARCHIVE_EXE=%GAME_DIR%\Archive.exe"
set "BUILD_FILE=.copilot_workspace\EnginLocBuild.txt"
set "DATA_DIR=data"
set "OUTPUT_SGA=EnginLocMod.sga"

REM Verify Archive.exe
if not exist "%ARCHIVE_EXE%" (
    echo [ERROR] Archive.exe not found: %ARCHIVE_EXE%
    echo.
    echo Please edit this script and set GAME_DIR to your game installation path
    pause
    exit /b 1
)
echo [OK] Found Archive.exe

REM Verify data directory
if not exist "%DATA_DIR%\" (
    echo [ERROR] data\ directory not found
    echo.
    echo Run font patching scripts first to create data\ directory:
    echo   cd /home/shado/crystal-mods/dawn-of-war-de/unofficial-tc-patch
    echo   python3 scripts/apply_font_fix.py --root . --size 36 --mode fallback-only
    pause
    exit /b 1
)
echo [OK] Found data\ directory

REM Verify buildfile
if not exist "%BUILD_FILE%" (
    echo [ERROR] Buildfile not found: %BUILD_FILE%
    echo.
    echo Creating buildfile...
    if not exist ".copilot_workspace\" mkdir ".copilot_workspace"
    
    (
        echo Archive
        echo TOCStart alias="data" relativeroot="."
        echo FileSettingsStart defcompression="1"
        echo     Override wildcard=".*(gfx)$" minsize="-1" maxsize="-1" ct="1"
        echo     Override wildcard=".*(fnt)$" minsize="-1" maxsize="-1" ct="2"
        echo     Override wildcard=".*(ttf|ttc)$" minsize="-1" maxsize="-1" ct="0"
        echo     Override wildcard=".*(fda|rat)$" minsize="-1" maxsize="-1" ct="2"
        echo FileSettingsEnd
        echo TOCEnd
    ) > "%BUILD_FILE%"
    
    echo [OK] Buildfile created
)

REM Backup existing SGA
if exist "%OUTPUT_SGA%" (
    set "TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%-%time:~0,2%%time:~3,2%%time:~6,2%"
    set "TIMESTAMP=!TIMESTAMP: =0!"
    set "BACKUP=%OUTPUT_SGA%.backup.!TIMESTAMP!"
    echo.
    echo Backing up existing SGA to: !BACKUP!
    move "%OUTPUT_SGA%" "!BACKUP!" >nul
    echo [OK] Backup created
)

REM Build SGA
echo.
echo Building SGA (this takes about 60 seconds)...
echo.

"%ARCHIVE_EXE%" -build "%BUILD_FILE%" -sourcedir "%DATA_DIR%" -archive "%OUTPUT_SGA%" -verbose

if errorlevel 1 (
    echo.
    echo [ERROR] Archive.exe failed with exit code %errorlevel%
    pause
    exit /b %errorlevel%
)

if not exist "%OUTPUT_SGA%" (
    echo.
    echo [ERROR] %OUTPUT_SGA% was not created
    pause
    exit /b 1
)

echo.
echo [SUCCESS] EnginLocMod.sga built successfully!
echo.

REM Show file size
for %%F in ("%OUTPUT_SGA%") do set "SIZE=%%~zF"
set /a SIZE_MB=!SIZE! / 1048576
echo File size: !SIZE_MB! MB
echo Path: %CD%\%OUTPUT_SGA%

echo.
echo ========================================================================
echo Next steps:
echo   1. Verify SGA was created: dir EnginLocMod.sga
echo   2. Package for distribution: make package (in WSL2)
echo   3. Test in-game
echo   4. For size 48 variant: re-patch fonts with SIZE=48 and rerun
echo ========================================================================
echo.

pause
