#!/usr/bin/env python3
"""
General Ledger Analyzer 실행 스크립트 (크로스 플랫폼)
이 파일을 더블클릭하거나 터미널에서 실행하면 Streamlit 앱이 실행됩니다.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 50)
    print("General Ledger Analyzer 시작 중...")
    print("=" * 50)
    
    # 현재 스크립트 위치로 이동
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Python 실행 파일 확인
    python_exe = sys.executable
    
    # 가상환경 확인 (있는 경우)
    venv_python = script_dir / "venv" / "bin" / "python"
    if venv_python.exists():
        python_exe = str(venv_python)
        print(f"가상환경 사용: {python_exe}")
    
    # requirements.txt 확인 및 설치 안내
    requirements_file = script_dir / "requirements.txt"
    if requirements_file.exists():
        print("필요한 패키지 확인 중...")
        try:
            import streamlit
        except ImportError:
            print("필요한 패키지를 설치합니다...")
            result = subprocess.run(
                [python_exe, "-m", "pip", "install", "-r", str(requirements_file)],
                cwd=script_dir
            )
            if result.returncode != 0:
                print("패키지 설치에 실패했습니다.")
                input("엔터를 눌러 종료하세요...")
                sys.exit(1)
    
    # Streamlit 앱 실행
    print("\nStreamlit 앱을 시작합니다...")
    print("브라우저가 자동으로 열립니다.")
    print("종료하려면 Ctrl+C를 누르세요.\n")
    
    app_file = script_dir / "src" / "app.py"
    if not app_file.exists():
        print(f"오류: {app_file} 파일을 찾을 수 없습니다.")
        input("엔터를 눌러 종료하세요...")
        sys.exit(1)
    
    os.chdir(script_dir / "src")
    
    try:
        subprocess.run(
            [python_exe, "-m", "streamlit", "run", "app.py", "--server.headless", "true"]
        )
    except KeyboardInterrupt:
        print("\n앱을 종료합니다.")
    except Exception as e:
        print(f"오류 발생: {e}")
        input("엔터를 눌러 종료하세요...")
        sys.exit(1)

if __name__ == "__main__":
    main()
