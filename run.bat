@echo off
chcp 65001 >nul
cd /d %~dp0

REM ===== 최초 실행: 가상환경 생성 =====
if not exist venv (
    echo [설치] 가상환경 생성 중...
    python -m venv venv
    if errorlevel 1 (
        echo [오류] Python이 설치되어 있지 않거나 PATH에 없습니다.
        pause
        exit /b 1
    )
)

REM ===== 최초 실행: 패키지 설치 (설치 완료 마커가 없으면) =====
if not exist venv\.installed (
    echo [설치] 필요한 패키지 설치 중... (tensorflow 포함, 첫 실행은 시간이 걸립니다)
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [오류] 패키지 설치 실패
        pause
        exit /b 1
    )
    echo done > venv\.installed
)

REM ===== 실행 =====
venv\Scripts\python.exe work1.py
pause