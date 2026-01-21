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

from windows_python_finder import find_windows_python

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
        print("\n방법 1: 환경변수로 직접 설정 (권장)")
        print("  export WINDOWS_PYTHON=/mnt/c/Users/YOUR_USERNAME/AppData/Local/Programs/Python/Python313/python.exe")
        print("  ./build_exe")
        print("\n방법 2: Windows에서 Python 경로 확인")
        print("  Windows PowerShell에서: where python")
        print("  출력된 경로를 WSL 경로로 변환:")
        print("  C:\\Users\\AD383HB\\... → /mnt/c/Users/AD383HB/...")
        print("\n방법 3: ~/.bashrc에 영구 설정")
        print("  echo 'export WINDOWS_PYTHON=/mnt/c/Users/YOUR_USERNAME/AppData/Local/Programs/Python/Python313/python.exe' >> ~/.bashrc")
        print("  source ~/.bashrc")
        print("\n자세한 내용은 SETUP.md 참조")
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
        print("Installing PyInstaller (user-site)...")
        subprocess.run(
            [str(python_exe), "-m", "pip", "install", "--user", "pyinstaller"],
            check=True
        )
    
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
            print("Installing requirements (user-site)...")
            subprocess.run(
                [str(python_exe), "-m", "pip", "install", "--user", "-r", "requirements.txt"],
                check=True
            )
    
    # 빌드 명령어
    # 래퍼 스크립트를 entry point로 사용
    wrapper_file = script_dir / "run_streamlit.py"
    app_file = script_dir / "src" / "app.py"
    
    # Streamlit의 static과 runtime 폴더 경로 찾기
    streamlit_static_win = None
    streamlit_runtime_win = None
    try:
        # Windows Python의 site-packages에서 streamlit 경로 찾기
        # Windows 경로를 그대로 유지 (PyInstaller가 Windows에서 실행되므로)
        find_cmd = """
import streamlit
from pathlib import Path
import sys

# streamlit.__file__ 사용
streamlit_path = Path(streamlit.__file__).parent
# Windows 경로를 그대로 출력
print(str(streamlit_path).replace('/', '\\\\'))
"""
        result = subprocess.run(
            [str(python_exe), "-c", find_cmd],
            capture_output=True,
            text=True,
            check=True
        )
        streamlit_dir_win = result.stdout.strip()
        streamlit_static_win = streamlit_dir_win + "\\static"
        streamlit_runtime_win = streamlit_dir_win + "\\runtime"
        
        # WSL에서도 확인하기 위해 경로 변환
        if streamlit_dir_win.startswith("C:\\"):
            streamlit_dir_str = "/mnt/c/" + streamlit_dir_win[3:].replace("\\", "/")
        elif streamlit_dir_win.startswith("C:"):
            streamlit_dir_str = "/mnt/c/" + streamlit_dir_win[2:].replace("\\", "/")
        else:
            streamlit_dir_str = streamlit_dir_win.replace("\\", "/")
        
        streamlit_dir = Path(streamlit_dir_str)
        streamlit_static = streamlit_dir / "static"
        streamlit_runtime = streamlit_dir / "runtime"
        
        print(f"Found Streamlit directory (Windows): {streamlit_dir_win}")
        print(f"Found Streamlit directory (WSL): {streamlit_dir}")
        print(f"  static exists (WSL): {streamlit_static.exists()}")
        print(f"  runtime exists (WSL): {streamlit_runtime.exists()}")
        
        # 존재하지 않으면 None으로 설정
        if not streamlit_static.exists():
            streamlit_static_win = None
        if not streamlit_runtime.exists():
            streamlit_runtime_win = None
    except Exception as e:
        print(f"Warning: Could not find Streamlit directories: {e}")
        print("  Streamlit static/runtime folders may not be included in the build.")
        print("  --collect-all=streamlit should handle this, but explicit inclusion is preferred.")
    
    # spec 파일 생성 (더 정확한 제어를 위해)
    spec_file = script_dir / "GL_Analyzer.spec"
    
    # WSL 경로를 Windows 경로로 변환하는 함수
    def wsl_to_win_path(path):
        path_str = str(path)
        if path_str.startswith("/mnt/c/"):
            return "C:" + path_str[6:].replace("/", "\\")
        elif path_str.startswith("/"):
            # WSL 경로를 Windows 네트워크 경로로 변환
            return "\\\\wsl.localhost\\Ubuntu" + path_str.replace("/", "\\")
        return path_str.replace("/", "\\")
    
    # Windows 경로로 변환
    wrapper_file_win = wsl_to_win_path(wrapper_file)
    script_dir_win = wsl_to_win_path(script_dir)
    src_dir_win = wsl_to_win_path(script_dir / "src")
    db_file_win = wsl_to_win_path(script_dir / "data" / "processed" / "gl_analyzer.duckdb")
    
    # spec 파일 내용 생성
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, copy_metadata

block_cipher = None

# Streamlit의 모든 서브모듈 수집
hiddenimports = collect_submodules('streamlit')
hiddenimports.extend([
    'streamlit',
    'pandas',
    'duckdb',
    'journal_entry_analyzer',
    'db_engine',
])

# 데이터 파일 수집
datas = [
    (r'{src_dir_win}', 'src'),
    (r'{db_file_win}', 'data/processed'),
"""
    
    # Streamlit의 static과 runtime 폴더 추가
    if streamlit_static_win:
        spec_content += f"    (r'{streamlit_static_win}', 'streamlit/static'),\n"
        print(f"  Adding streamlit/static to spec: {streamlit_static_win}")
    
    if streamlit_runtime_win:
        spec_content += f"    (r'{streamlit_runtime_win}', 'streamlit/runtime'),\n"
        print(f"  Adding streamlit/runtime to spec: {streamlit_runtime_win}")
    
    spec_content += f"""]

# Streamlit의 모든 데이터 파일 수집
try:
    streamlit_datas = collect_data_files('streamlit')
    datas.extend(streamlit_datas)
except Exception as e:
    print(f"Warning: Could not collect Streamlit data files: {{e}}")

# Streamlit 메타데이터 포함 (버전 정보 등)
try:
    streamlit_metadata = copy_metadata('streamlit')
    datas.extend(streamlit_metadata)
except Exception as e:
    print(f"Warning: Could not copy Streamlit metadata: {{e}}")

a = Analysis(
    [r'{wrapper_file_win}'],
    pathex=[r'{src_dir_win}'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GL_Analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    # spec 파일 저장
    print(f"\nGenerating spec file: {spec_file}")
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    # spec 파일을 사용하여 빌드
    build_cmd = [
        str(python_exe), "-m", "PyInstaller",
        "--clean",
        str(spec_file)
    ]
    
    print("\nBuilding executable...")
    print("This may take several minutes...")
    print()
    
    try:
        # Windows Python을 사용하여 빌드
        # WSL 경로를 Windows 경로로 변환하여 전달
        subprocess.run(build_cmd, check=True, cwd=script_dir)
        
        print("\n" + "=" * 60)
        print("Build completed successfully!")
        print("=" * 60)
            
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
