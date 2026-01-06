# 환경 설정 가이드

## Windows Python 경로 설정

빌드 스크립트가 Windows Python을 자동으로 찾지 못하는 경우, 수동으로 경로를 설정할 수 있습니다.

### 방법 1: 현재 세션에서만 설정 (임시)

터미널에서 한 번만 실행:

```bash
export WINDOWS_PYTHON=/mnt/c/Python311/python.exe
./build_exe
```

**주의:** 터미널을 닫으면 설정이 사라집니다.

### 방법 2: 영구적으로 설정 (권장)

홈 디렉토리의 `.bashrc` 파일에 추가:

```bash
# 편집기로 열기
nano ~/.bashrc
# 또는
vim ~/.bashrc
```

파일 끝에 다음 줄 추가:

```bash
# Windows Python 경로 설정
export WINDOWS_PYTHON=/mnt/c/Python311/python.exe
```

저장 후 다음 중 하나 실행:

```bash
# 설정 적용
source ~/.bashrc

# 또는 새 터미널 열기
```

이제 모든 새 터미널에서 자동으로 설정됩니다.

### 방법 3: Windows Python 경로 찾기

Windows Python이 설치되어 있지만 경로를 모르는 경우:

**Windows에서 확인:**
1. Windows PowerShell 또는 CMD 열기
2. 다음 명령 실행:
   ```cmd
   where python
   ```
3. 출력된 경로를 확인 (예: `C:\Python311\python.exe`)

**WSL에서 확인:**
```bash
# 일반적인 설치 위치 확인
ls /mnt/c/Python311/python.exe
ls /mnt/c/Python312/python.exe
ls /mnt/c/Users/$USER/AppData/Local/Programs/Python/Python311/python.exe
ls /mnt/c/Users/$USER/AppData/Local/Programs/Python/Python312/python.exe
```

### 방법 4: 빌드 스크립트에 직접 지정

빌드 스크립트를 수정하여 직접 경로 지정:

```bash
# build_exe_windows.py 파일을 열고
# find_windows_python() 함수의 possible_paths 리스트에 경로 추가
```

또는 빌드 전에 환경변수 설정:

```bash
WINDOWS_PYTHON=/mnt/c/Python311/python.exe python build_exe_windows.py
```

## 확인 방법

설정이 제대로 되었는지 확인:

```bash
echo $WINDOWS_PYTHON
# 출력 예시: /mnt/c/Python311/python.exe

# 또는 빌드 스크립트 실행 시 자동으로 확인됨
./build_exe
```

## 문제 해결

### 환경변수가 적용되지 않음
- 새 터미널을 열었는지 확인
- `source ~/.bashrc` 실행했는지 확인
- `.bashrc` 파일에 올바르게 추가되었는지 확인

### 경로를 찾을 수 없음
- Windows에 Python이 설치되어 있는지 확인
- 경로에 오타가 없는지 확인 (대소문자 구분)
- WSL에서 `/mnt/c/` 경로로 접근 가능한지 확인
