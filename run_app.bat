@echo off
chcp 65001 >nul 2>&1
REM General Ledger Analyzer Launcher (Windows)
REM Double-click this file to run the Streamlit app

echo ========================================
echo Starting General Ledger Analyzer...
echo ========================================

REM Change to script directory
cd /d "%~dp0"

REM Check Python installation
set PYTHON_PATH=python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found. Please install Python.
    pause
    exit /b 1
)

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Check and install requirements
if exist "requirements.txt" (
    echo Checking required packages...
    python -c "import streamlit" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo Installing required packages...
        python -m pip install -r requirements.txt
        if %ERRORLEVEL% NEQ 0 (
            echo ERROR: Failed to install packages.
            pause
            exit /b 1
        )
    )
)

REM Verify streamlit is available
python -c "import streamlit" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Streamlit is not installed. Please install it manually:
    echo   python -m pip install streamlit
    pause
    exit /b 1
)

REM Run Streamlit app
echo.
echo Starting Streamlit app...
echo Browser will open automatically.
echo Press Ctrl+C to stop.
echo.

cd src
python -m streamlit run app.py --server.headless true

pause
