@echo off
REM General Ledger Analyzer 실행 스크립트 (Windows)
REM 이 파일을 더블클릭하면 Streamlit 앱이 실행됩니다.

echo ========================================
echo General Ledger Analyzer 시작 중...
echo ========================================

REM 현재 스크립트 위치로 이동
cd /d "%~dp0"

REM Python 경로 확인 (pyenv 사용 시)
set PYTHON_PATH=python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python을 찾을 수 없습니다. Python이 설치되어 있는지 확인하세요.
    pause
    exit /b 1
)

REM 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM requirements.txt 확인 및 설치 안내
if exist "requirements.txt" (
    echo 필요한 패키지 확인 중...
    python -c "import streamlit" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo 필요한 패키지를 설치합니다...
        pip install -r requirements.txt
        if %ERRORLEVEL% NEQ 0 (
            echo 패키지 설치에 실패했습니다.
            pause
            exit /b 1
        )
    )
)

REM Streamlit 앱 실행
echo.
echo Streamlit 앱을 시작합니다...
echo 브라우저가 자동으로 열립니다.
echo 종료하려면 이 창에서 Ctrl+C를 누르세요.
echo.

cd src
streamlit run app.py --server.headless true

pause
