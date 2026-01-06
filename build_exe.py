#!/usr/bin/env python3
"""
PyInstaller를 사용하여 실행 파일(.exe) 생성 스크립트
이 스크립트를 실행하면 Python이 없는 컴퓨터에서도 실행 가능한 .exe 파일이 생성됩니다.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print("Building General Ledger Analyzer Executable")
    print("=" * 60)
    
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # PyInstaller 설치 확인
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # 빌드 명령어
    app_file = script_dir / "src" / "app.py"
    src_dir = script_dir / "src"
    
    # data 폴더 경로 처리
    data_dir = script_dir / "data"
    add_data_args = []
    if data_dir.exists():
        add_data_args.extend(["--add-data", f"data{os.pathsep}data"])
    
    # src 폴더도 포함 (모듈 import용)
    if src_dir.exists():
        add_data_args.extend(["--add-data", f"src{os.pathsep}src"])
    
    build_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=GL_Analyzer",
        "--onefile",
        "--console",  # 콘솔 창 표시 (에러 확인용)
        "--hidden-import=streamlit",
        "--hidden-import=pandas",
        "--hidden-import=duckdb",
        "--hidden-import=journal_entry_analyzer",
        "--hidden-import=db_engine",
        "--collect-all=streamlit",
        "--collect-all=altair",
        "--collect-submodules=streamlit",
    ]
    
    # add-data 인자 추가
    build_cmd.extend(add_data_args)
    build_cmd.append(str(app_file))
    
    print("\nBuilding executable...")
    print("This may take several minutes...")
    print()
    
    try:
        subprocess.run(build_cmd, check=True)
        print("\n" + "=" * 60)
        print("Build completed successfully!")
        print("=" * 60)
        exe_path = script_dir / "dist" / "GL_Analyzer.exe"
        print(f"\nExecutable location: {exe_path}")
        
        # .exe 파일을 루트로 복사 (선택사항)
        import shutil
        root_exe = script_dir / "GL_Analyzer.exe"
        try:
            shutil.copy2(exe_path, root_exe)
            print(f"Also copied to: {root_exe}")
            print("\nNow you can:")
            print("  1. Double-click 'run_app.bat' - it will use GL_Analyzer.exe")
            print("  2. Or double-click 'GL_Analyzer.exe' directly")
        except Exception as e:
            print(f"Could not copy to root: {e}")
        
        print("\nYou can now distribute these files:")
        print("  - GL_Analyzer.exe (or dist/GL_Analyzer.exe)")
        print("  - data/processed/gl_analyzer.duckdb (database file)")
        print("\nNote: The .exe file is large (~100-200MB) as it includes Python.")
        print("      No Python installation needed on target computer!")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
