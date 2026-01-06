#!/bin/bash
# General Ledger Analyzer 실행 스크립트 (Linux/Mac)
# 이 파일을 더블클릭하거나 터미널에서 실행하면 Streamlit 앱이 실행됩니다.

echo "========================================"
echo "General Ledger Analyzer 시작 중..."
echo "========================================"

# 현재 스크립트 위치로 이동
cd "$(dirname "$0")"

# Python 경로 확인
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "Python을 찾을 수 없습니다. Python이 설치되어 있는지 확인하세요."
        exit 1
    else
        PYTHON_CMD=python
    fi
else
    PYTHON_CMD=python3
fi

# 가상환경 활성화 (있는 경우)
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# pyenv 사용 시 (있는 경우)
if command -v pyenv &> /dev/null; then
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init -)"
    if [ -f ".python-version" ]; then
        pyenv shell $(cat .python-version)
    fi
fi

# requirements.txt 확인 및 설치 안내
if [ -f "requirements.txt" ]; then
    echo "필요한 패키지 확인 중..."
    if ! $PYTHON_CMD -c "import streamlit" 2>/dev/null; then
        echo "필요한 패키지를 설치합니다..."
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo "패키지 설치에 실패했습니다."
            exit 1
        fi
    fi
fi

# Streamlit 앱 실행
echo ""
echo "Streamlit 앱을 시작합니다..."
echo "브라우저가 자동으로 열립니다."
echo "종료하려면 Ctrl+C를 누르세요."
echo ""

cd src
streamlit run app.py --server.headless true
