#!/usr/bin/env python3
"""
WSL에서 Windows용 .exe 파일 빌드 스크립트 (Python 버전)
Windows Python을 찾아서 사용합니다.

사용법:
  python build_exe_windows.py
  또는 파일을 더블클릭 (build 스크립트 사용)
"""

import os
import sys
import subprocess
from pathlib import Path

# 파일 매니저에서 더블클릭한 경우를 위한 처리
if __name__ == "__main__" and len(sys.argv) == 1:
    # 터미널이 없으면 새 터미널에서 실행
    if not os.isatty(sys.stdin.fileno()):
        # GUI 환경에서 실행된 경우
        terminal_cmd = os.getenv("TERMINAL", "gnome-terminal")
        script_path = Path(__file__).absolute()
        try:
            subprocess.Popen([terminal_cmd, "-e", f"python3 {script_path}; read -p 'Press Enter to close...'"])
            sys.exit(0)
        except:
            pass  # 터미널 실행 실패 시 계속 진행

def find_windows_python():
    """Windows Python 실행 파일 찾기"""
    possible_paths = [
        f"/mnt/c/Users/{os.getenv('USER', 'user')}/AppData/Local/Programs/Python/Python311/python.exe",
        f"/mnt/c/Users/{os.getenv('USER', 'user')}/AppData/Local/Programs/Python/Python312/python.exe",
        "/mnt/c/Python311/python.exe",
        "/mnt/c/Python312/python.exe",
        "/mnt/c/Program Files/Python311/python.exe",
        "/mnt/c/Program Files/Python312/python.exe",
    ]
    
    # 환경변수로 지정된 경우
    if os.getenv("WINDOWS_PYTHON"):
        if Path(os.getenv("WINDOWS_PYTHON")).exists():
            return Path(os.getenv("WINDOWS_PYTHON"))
    
    for path_str in possible_paths:
        path = Path(path_str)
        if path.exists():
            return path
    
    return None

def main():
    print("=" * 60)
    print("Building Windows .exe from WSL")
    print("=" * 60)
    
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Windows Python 찾기
    python_exe = find_windows_python()
    
    if not python_exe:
        print("\nERROR: Windows Python not found!")
        print("\nPlease install Python on Windows, then:")
        print("  1. Find the Python path (e.g., C:\\Python311\\python.exe)")
        print("  2. Set environment variable:")
        print("     export WINDOWS_PYTHON=/mnt/c/Python311/python.exe")
        print("  3. Run this script again")
        print("\nOr use: python build_exe_windows.py")
        sys.exit(1)
    
    print(f"Found Windows Python: {python_exe}")
    
    # Python 버전 확인
    try:
        version_output = subprocess.run(
            [str(python_exe), "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Python version: {version_output.stdout.strip()}")
    except:
        print("Warning: Could not check Python version")
    
    print()
    
    # PyInstaller 설치 확인
    print("Checking PyInstaller...")
    try:
        subprocess.run(
            [str(python_exe), "-c", "import PyInstaller"],
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError:
        print("Installing PyInstaller...")
        subprocess.run([str(python_exe), "-m", "pip", "install", "pyinstaller"], check=True)
    
    # requirements.txt 설치 확인
    if (script_dir / "requirements.txt").exists():
        print("Checking required packages...")
        try:
            subprocess.run(
                [str(python_exe), "-c", "import streamlit"],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            print("Installing requirements...")
            subprocess.run(
                [str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"],
                check=True
            )
    
    # 빌드 명령어
    app_file = script_dir / "src" / "app.py"
    
    build_cmd = [
        str(python_exe), "-m", "PyInstaller",
        "--name=GL_Analyzer",
        "--onefile",
        "--console",
        "--hidden-import=streamlit",
        "--hidden-import=pandas",
        "--hidden-import=duckdb",
        "--hidden-import=journal_entry_analyzer",
        "--hidden-import=db_engine",
        "--collect-all=streamlit",
        "--collect-all=altair",
        "--collect-submodules=streamlit",
        "--add-data", f"{script_dir / 'src' / 'app.py'};src",  # app.py를 src 폴더로 포함
    ]
    
    # data 폴더 추가 (Windows 경로 형식)
    # PyInstaller는 --add-data로 포함하지만, 실행 시 .exe와 같은 폴더에 있어야 함
    # 따라서 빌드 후 data 폴더를 dist에 복사해야 함
    data_dir = script_dir / "data"
    if data_dir.exists():
        # WSL에서 Windows로 경로 변환
        try:
            import subprocess as sp
            win_path = sp.check_output(["wslpath", "-w", str(data_dir)], text=True).strip()
            build_cmd.extend(["--add-data", f"{win_path};data"])
        except:
            # wslpath가 없으면 상대 경로 사용
            build_cmd.extend(["--add-data", "data;data"])
    
    build_cmd.append(str(app_file))
    
    print("\nBuilding executable...")
    print("This may take several minutes...")
    print()
    
    try:
        # Windows Python을 사용하여 빌드
        subprocess.run(build_cmd, check=True, cwd=script_dir)
        
        print("\n" + "=" * 60)
        print("Build completed successfully!")
        print("=" * 60)
        
        exe_path = script_dir / "dist" / "GL_Analyzer.exe"
        if exe_path.exists():
            print(f"\nExecutable location: {exe_path}")
            
            # data 폴더를 dist에 복사 (.exe와 같은 위치에 있어야 함)
            import shutil
            dist_data = script_dir / "dist" / "data"
            if data_dir.exists():
                if dist_data.exists():
                    shutil.rmtree(dist_data)
                shutil.copytree(data_dir, dist_data)
                print(f"Data folder copied to: {dist_data}")
            
            # 루트로도 복사 (선택사항)
            root_exe = script_dir / "GL_Analyzer.exe"
            shutil.copy2(exe_path, root_exe)
            print(f"Also copied to: {root_exe}")
            
            print("\n" + "=" * 60)
            print("✅ 빌드 완료! 배포 준비됨")
            print("=" * 60)
            print("\n배포할 파일:")
            print(f"  📦 {exe_path.name}")
            print(f"  📁 data/ 폴더 전체")
            print("\n또는 dist 폴더 전체를 압축하여 배포:")
            print(f"  📦 dist/ 폴더")
            print("\n팀원들은 .exe 파일을 더블클릭하면 됩니다!")
            print("(data 폴더가 .exe와 같은 위치에 있어야 합니다)")
        else:
            print("\nWarning: GL_Analyzer.exe not found in dist folder")
            print("Check build output for errors.")
            
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
