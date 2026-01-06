#!/bin/bash
# WSL에서 Windows용 .exe 파일 빌드 스크립트
# 이 스크립트는 WSL 환경에서 Windows Python을 사용하여 빌드합니다.

set -e

echo "============================================================"
echo "Building Windows .exe from WSL"
echo "============================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Windows Python 경로 찾기
WINDOWS_PYTHON_PATHS=(
    "/mnt/c/Users/$USER/AppData/Local/Programs/Python/Python311/python.exe"
    "/mnt/c/Users/$USER/AppData/Local/Programs/Python/Python312/python.exe"
    "/mnt/c/Python311/python.exe"
    "/mnt/c/Python312/python.exe"
    "/mnt/c/Program Files/Python311/python.exe"
    "/mnt/c/Program Files/Python312/python.exe"
)

PYTHON_EXE=""
for path in "${WINDOWS_PYTHON_PATHS[@]}"; do
    if [ -f "$path" ]; then
        PYTHON_EXE="$path"
        echo "Found Windows Python: $PYTHON_EXE"
        break
    fi
done

if [ -z "$PYTHON_EXE" ]; then
    echo ""
    echo "ERROR: Windows Python not found!"
    echo ""
    echo "Please install Python on Windows, then try again."
    echo "Or specify the path manually:"
    echo "  export WINDOWS_PYTHON=/mnt/c/path/to/python.exe"
    echo "  ./build_exe_windows.sh"
    echo ""
    exit 1
fi

# 환경변수로 지정된 경우 사용
if [ -n "$WINDOWS_PYTHON" ]; then
    PYTHON_EXE="$WINDOWS_PYTHON"
fi

echo "Using Python: $PYTHON_EXE"
echo ""

# PyInstaller 설치 확인
echo "Checking PyInstaller..."
"$PYTHON_EXE" -c "import PyInstaller" 2>/dev/null || {
    echo "Installing PyInstaller..."
    "$PYTHON_EXE" -m pip install pyinstaller
}

# requirements.txt 설치 확인
if [ -f "requirements.txt" ]; then
    echo "Checking required packages..."
    "$PYTHON_EXE" -c "import streamlit" 2>/dev/null || {
        echo "Installing requirements..."
        "$PYTHON_EXE" -m pip install -r requirements.txt
    }
fi

# 빌드 실행
echo ""
echo "Building executable..."
echo "This may take several minutes..."
echo ""

APP_FILE="$SCRIPT_DIR/src/app.py"

# Windows 경로로 변환
WIN_SCRIPT_DIR=$(wslpath -w "$SCRIPT_DIR" 2>/dev/null || echo "$SCRIPT_DIR")
WIN_APP_FILE=$(wslpath -w "$APP_FILE" 2>/dev/null || echo "$APP_FILE")

# PyInstaller 빌드 명령어
BUILD_CMD=(
    "$PYTHON_EXE" -m PyInstaller
    --name=GL_Analyzer
    --onefile
    --console
    --hidden-import=streamlit
    --hidden-import=pandas
    --hidden-import=duckdb
    --hidden-import=journal_entry_analyzer
    --hidden-import=db_engine
    --collect-all=streamlit
    --collect-all=altair
    --collect-submodules=streamlit
)

# data 폴더 추가
if [ -d "data" ]; then
    BUILD_CMD+=(--add-data "data;data")
fi

BUILD_CMD+=("$WIN_APP_FILE")

# Windows에서 실행 (cmd.exe를 통해)
echo "Running build command..."
cmd.exe /c "cd /d $WIN_SCRIPT_DIR && ${BUILD_CMD[*]}"

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "Build completed successfully!"
    echo "============================================================"
    echo ""
    EXE_PATH="$SCRIPT_DIR/dist/GL_Analyzer.exe"
    if [ -f "$EXE_PATH" ]; then
        echo "Executable location: $EXE_PATH"
        # 루트로 복사
        cp "$EXE_PATH" "$SCRIPT_DIR/GL_Analyzer.exe"
        echo "Also copied to: $SCRIPT_DIR/GL_Analyzer.exe"
        echo ""
        echo "You can now distribute:"
        echo "  - GL_Analyzer.exe"
        echo "  - data/processed/gl_analyzer.duckdb"
    else
        echo "Warning: GL_Analyzer.exe not found in dist folder"
    fi
else
    echo ""
    echo "Build failed!"
    exit 1
fi
