# 빌드 가이드

## WSL에서 Windows용 .exe 빌드하기

### 방법 1: 더블클릭으로 빌드 (가장 간단) ⭐

1. **`build_exe`** 파일을 더블클릭하세요
2. 터미널이 열리며 빌드가 시작됩니다
3. 빌드 완료 후 `dist/GL_Analyzer.exe` 파일이 생성됩니다

### 방법 2: 터미널에서 실행

```bash
./build_exe
```

또는

```bash
python build_exe_windows.py
```

### 방법 3: Bash 스크립트 사용

```bash
./build_exe_windows.sh
```

## 사전 요구사항

- Windows에 Python이 설치되어 있어야 합니다
- WSL에서 Windows Python 경로에 접근 가능해야 합니다

## Windows Python 경로를 찾지 못하는 경우

수동으로 경로 지정:

```bash
export WINDOWS_PYTHON=/mnt/c/Python311/python.exe
./build_exe
```

Windows Python 경로 확인:
- Windows에서 `where python` 실행
- 일반적인 경로:
  - `C:\Python311\python.exe`
  - `C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe`

## 빌드 결과

- `dist/GL_Analyzer.exe` - Windows 실행 파일
- `GL_Analyzer.exe` - 루트 폴더로 복사된 파일

## 배포

다음 파일들을 함께 배포하세요:
- `GL_Analyzer.exe`
- `data/processed/gl_analyzer.duckdb`

Python이 없는 Windows 컴퓨터에서도 실행 가능합니다!
