@echo off
cd /d %~dp0

REM ===== First run: create virtual environment =====
if not exist venv (
    echo [Setup] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [Error] Python is not installed or not in PATH.
        pause
        exit /b 1
    )
)

REM ===== First run: install packages (skipped if marker file exists) =====
if not exist venv\.installed (
    echo [Setup] Installing packages... ^(includes tensorflow, may take a while^)
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [Error] Package installation failed
        pause
        exit /b 1
    )
    echo done > venv\.installed
)

REM ===== Run =====
venv\Scripts\python.exe work1.py
pause