#!/usr/bin/env python3
"""
PyInstaller로 빌드된 Streamlit 앱 실행 래퍼
이 스크립트는 .exe의 entry point로 사용됩니다.
"""
import sys
import os
from pathlib import Path

def get_exe_dir():
    """
    실제 exe 파일이 있는 디렉토리를 반환합니다.
    PyInstaller --onefile 모드에서도 올바르게 작동합니다.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller --onefile 모드에서는 sys.executable이 임시 폴더의 exe를 가리킬 수 있음
        # 실제 exe 파일의 위치를 찾기 위해 다른 방법 사용
        
        # 방법 1: 실행 시점의 작업 디렉토리 사용 (가장 확실함)
        # exe를 실행한 폴더가 작업 디렉토리이므로 이를 저장해야 함
        # 하지만 이미 함수가 호출된 후라면 작업 디렉토리가 변경되었을 수 있음
        
        # 방법 2: sys.executable의 실제 경로 확인
        # --onefile 모드에서는 sys.executable이 실제 exe를 가리키지만,
        # 실행 중에는 임시 폴더의 복사본을 가리킬 수 있음
        
        # 방법 3: 프로세스 정보 사용 (Windows)
        try:
            import win32api
            exe_path = win32api.GetModuleFileName(win32api.GetModuleHandle(None))
            return Path(exe_path).parent.resolve()
        except ImportError:
            pass
        
        # 방법 4: sys.executable 사용 (일반적인 경우)
        # --onefile 모드에서도 때로는 실제 경로를 가리킬 수 있음
        exe_path = Path(sys.executable)
        exe_dir = exe_path.parent.resolve()
        
        # 임시 폴더가 아닌지 확인 (일반적으로 Temp 폴더에 있지 않으면 실제 위치)
        temp_paths = ['Temp', 'tmp', '_MEI']
        if not any(temp in str(exe_dir) for temp in temp_paths):
            return exe_dir
        
        # 방법 5: 작업 디렉토리 사용 (fallback)
        # exe를 실행한 폴더가 작업 디렉토리일 가능성이 높음
        cwd = Path(os.getcwd()).resolve()
        return cwd
    else:
        # 일반 실행
        return Path(__file__).parent.resolve()

def get_actual_exe_dir():
    """
    Windows에서 실제 exe 파일이 있는 디렉토리를 찾습니다.
    --onefile 모드에서도 올바르게 작동합니다.
    """
    if sys.platform == 'win32':
        try:
            import ctypes
            from ctypes import wintypes
            
            # GetModuleFileNameW를 사용하여 실제 exe 경로 가져오기
            kernel32 = ctypes.windll.kernel32
            GetModuleFileNameW = kernel32.GetModuleFileNameW
            GetModuleFileNameW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD]
            GetModuleFileNameW.restype = wintypes.DWORD
            
            # NULL 핸들은 현재 프로세스의 exe를 의미
            MAX_PATH = 260
            buffer = ctypes.create_unicode_buffer(MAX_PATH)
            length = GetModuleFileNameW(None, buffer, MAX_PATH)
            
            if length > 0:
                exe_path = Path(buffer.value)
                exe_dir = exe_path.parent.resolve()
                return exe_dir
        except Exception as e:
            print(f"Warning: Could not get exe path using Windows API: {e}")
    
    # Fallback: sys.executable 사용
    exe_path = Path(sys.executable)
    exe_dir = exe_path.parent.resolve()
    
    # 임시 폴더가 아닌지 확인
    temp_indicators = ['Temp', 'tmp', '_MEI', 'AppData\\Local\\Temp']
    if any(indicator in str(exe_dir) for indicator in temp_indicators):
        # 임시 폴더인 경우, 작업 디렉토리 사용
        cwd = Path(os.getcwd()).resolve()
        # WSL 경로가 아닌지 확인
        if 'wsl.localhost' not in str(cwd) and not str(cwd).startswith('/'):
            return cwd
    
    return exe_dir

def main():
    # PyInstaller로 빌드된 경우
    if getattr(sys, 'frozen', False):
        # 가장 먼저 실행 시점의 작업 디렉토리 저장
        # (이 시점에서 os.getcwd()는 exe를 실행한 폴더를 가리킴)
        original_cwd = Path(os.getcwd()).resolve()
        
        # 실제 exe 파일이 있는 디렉토리 찾기
        exe_dir = get_actual_exe_dir()
        
        # WSL 경로인 경우 처리
        exe_dir_str = str(exe_dir)
        if 'wsl.localhost' in exe_dir_str or exe_dir_str.startswith('/'):
            print(f"INFO: WSL path detected: {exe_dir}")
            print(f"  Original working directory: {original_cwd}")
            print(f"  sys.executable: {sys.executable}")
            
            # 원래 작업 디렉토리 확인
            original_cwd_str = str(original_cwd)
            if 'wsl.localhost' in original_cwd_str or original_cwd_str.startswith('/'):
                # 둘 다 WSL 경로인 경우, 원래 작업 디렉토리 사용
                print(f"  Using original working directory: {original_cwd}")
                exe_dir = original_cwd
            else:
                # 원래 작업 디렉토리가 Windows 경로면 사용
                print(f"  Using original working directory (Windows path): {original_cwd}")
                exe_dir = original_cwd
            
            print(f"  Note: Running from WSL. DB file should be at: {exe_dir / 'data' / 'processed' / 'gl_analyzer.duckdb'}")
        
        # _MEIPASS는 임시 폴더 (번들된 파일들이 압축 해제된 곳)
        if hasattr(sys, '_MEIPASS'):
            meipass_path = Path(sys._MEIPASS)
        else:
            meipass_path = Path(sys.executable).parent
        
        # app.py 경로 찾기 (번들된 파일은 _MEIPASS에 있음)
        app_path = meipass_path / "src" / "app.py"
        if not app_path.exists():
            app_path = meipass_path / "app.py"
        
        if not app_path.exists():
            print(f"ERROR: Cannot find app.py")
            print(f"  Searched in: {meipass_path}")
            print(f"  sys._MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
            print(f"  sys.executable: {sys.executable}")
            sys.exit(1)
        
        # Streamlit 실행
        from streamlit.web import cli as stcli
        
        # 앱 파일의 절대 경로
        app_path_abs = app_path.absolute()
        
        # 환경변수로 전달 (DB 파일은 이 디렉토리에서 찾음)
        os.environ['EXE_DIR'] = str(exe_dir)
        
        print("=" * 60)
        print("Path Information:")
        print(f"  Actual exe directory: {exe_dir}")
        print(f"  Original working directory: {original_cwd}")
        print(f"  Temp bundle directory (_MEIPASS): {meipass_path}")
        print(f"  sys.executable: {sys.executable}")
        print(f"  Running Streamlit app from: {app_path_abs}")
        print("=" * 60)
        
        # 앱 파일의 부모 폴더로 이동 (import 경로 문제 방지)
        # 하지만 DB 파일은 exe_dir에서 찾아야 하므로 환경변수로 전달했음
        os.chdir(app_path_abs.parent)
        
        print(f"Current working directory (for imports): {os.getcwd()}")
        
        # Streamlit 실행
        sys.argv = [
            "streamlit",
            "run",
            str(app_path_abs),
            "--server.headless",
            "false",
            "--global.developmentMode",
            "false",
            "--server.port",
            "8501"
        ]
        
        stcli.main()
    else:
        # 일반 실행 (개발 모드)
        from streamlit.web import cli as stcli
        app_path = Path(__file__).parent / "src" / "app.py"
        sys.argv = ["streamlit", "run", str(app_path), "--server.headless", "false"]
        stcli.main()

if __name__ == "__main__":
    main()
