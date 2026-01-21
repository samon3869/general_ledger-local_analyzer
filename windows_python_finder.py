"""
Windows Python 실행 파일 찾기 유틸리티

PyInstaller는 크로스 플랫폼 빌드를 지원하지 않으므로,
Windows용 .exe를 만들려면 Windows Python이 필요합니다.
"""

import os
from pathlib import Path


def find_windows_python():
    """
    Windows Python 실행 파일 찾기
    
    참고: PyInstaller는 크로스 플랫폼 빌드를 지원하지 않습니다.
    - WSL Python으로 PyInstaller 실행 → Linux 바이너리 생성
    - Windows Python으로 PyInstaller 실행 → Windows .exe 생성
    
    따라서 Windows .exe를 만들려면 반드시 Windows Python이 필요합니다.
    
    Returns:
        Path: Windows Python 실행 파일 경로, 없으면 None
    """
    # 환경변수로 지정된 경우 (최우선)
    if os.getenv("WINDOWS_PYTHON"):
        env_path = Path(os.getenv("WINDOWS_PYTHON"))
        if env_path.exists():
            return env_path
    
    # Windows Users 디렉토리에서 실제 사용자명 찾기
    users_dir = Path("/mnt/c/Users")
    windows_users = []
    if users_dir.exists():
        for item in users_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                windows_users.append(item.name)
    
    # 가능한 경로 목록 생성
    possible_paths = []
    
    # 1. 환경변수에서 가져온 사용자명 사용
    wsl_user = os.getenv('USER', '')
    if wsl_user:
        for version in ['313', '312', '311', '310']:
            possible_paths.append(
                f"/mnt/c/Users/{wsl_user}/AppData/Local/Programs/Python/Python{version}/python.exe"
            )
    
    # 2. 실제 Windows Users 디렉토리 스캔
    for user in windows_users:
        for version in ['313', '312', '311', '310']:
            possible_paths.append(
                f"/mnt/c/Users/{user}/AppData/Local/Programs/Python/Python{version}/python.exe"
            )
    
    # 3. 일반적인 설치 경로
    for version in ['313', '312', '311', '310']:
        possible_paths.extend([
            f"/mnt/c/Python{version}/python.exe",
            f"/mnt/c/Program Files/Python{version}/python.exe",
            f"/mnt/c/Program Files (x86)/Python{version}/python.exe",
        ])
    
    # 중복 제거 (순서 유지)
    seen = set()
    unique_paths = []
    for path_str in possible_paths:
        if path_str not in seen:
            seen.add(path_str)
            unique_paths.append(path_str)
    
    # 경로 확인
    for path_str in unique_paths:
        path = Path(path_str)
        if path.exists():
            return path
    
    return None
