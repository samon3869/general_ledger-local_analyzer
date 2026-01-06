@echo off
chcp 65001 >nul 2>&1
REM General Ledger Analyzer Launcher (Windows)
REM Double-click this file to run the Streamlit app

echo ========================================
echo Starting General Ledger Analyzer...
echo ========================================

REM Change to script directory
cd /d "%~dp0"

REM Check if executable exists (built with PyInstaller)
if exist "dist\GL_Analyzer.exe" (
    echo Found standalone executable. Running...
    echo.
    start "" "dist\GL_Analyzer.exe"
    exit /b 0
)

REM Check if executable exists in current directory
if exist "GL_Analyzer.exe" (
    echo Found standalone executable. Running...
    echo.
    start "" "GL_Analyzer.exe"
    exit /b 0
)

REM If no executable, check for Python
set PYTHON_CMD=python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ========================================
    echo ERROR: Python not found!
    echo ========================================
    echo.
    echo This application requires Python to run.
    echo.
    echo Options:
    echo 1. Install Python from https://www.python.org/downloads/
    echo 2. Use the pre-built executable (GL_Analyzer.exe)
    echo    - Ask the developer for the .exe file
    echo    - Or build it yourself: python build_exe.py
    echo.
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
    REM Get the actual Python executable path
    for /f "delims=" %%i in ('where %PYTHON_CMD%') do set PYTHON_EXE=%%i
    echo Using Python: %PYTHON_EXE%
    
    REM Check streamlit using the actual Python path
    "%PYTHON_EXE%" -c "import streamlit" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo Streamlit not found. Installing required packages...
        echo This may take a few minutes...
        "%PYTHON_EXE%" -m pip install -r requirements.txt
        if %ERRORLEVEL% NEQ 0 (
            echo ERROR: Failed to install packages.
            echo Please try manually: "%PYTHON_EXE%" -m pip install -r requirements.txt
            pause
            exit /b 1
        )
        REM Verify installation
        "%PYTHON_EXE%" -c "import streamlit" 2>nul
        if %ERRORLEVEL% NEQ 0 (
            echo ERROR: Streamlit installation failed. Please install manually:
            echo   "%PYTHON_EXE%" -m pip install streamlit
            pause
            exit /b 1
        )
        echo Packages installed successfully.
    ) else (
        echo All required packages are already installed.
    )
)

REM Run Streamlit app
echo.
echo Starting Streamlit app...
echo Browser will open automatically.
echo Press Ctrl+C to stop.
echo.

cd src
REM Use the actual Python executable path
if defined PYTHON_EXE (
    "%PYTHON_EXE%" -m streamlit run app.py --server.headless true
) else (
    %PYTHON_CMD% -m streamlit run app.py --server.headless true
)

pause
