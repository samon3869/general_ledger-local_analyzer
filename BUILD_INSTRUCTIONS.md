# 실행 파일 빌드 가이드

Python이 설치되지 않은 컴퓨터에서도 실행 가능한 독립 실행 파일(.exe)을 만드는 방법입니다.

## 방법 1: PyInstaller로 실행 파일 생성 (권장)

### 준비사항
- Python 3.11 이상 설치 필요 (빌드 시에만 필요)
- 모든 패키지 설치: `pip install -r requirements.txt`

### 빌드 실행
```bash
python build_exe.py
```

### 결과물
- `dist/GL_Analyzer.exe` - 실행 파일
- 이 파일을 다른 컴퓨터에 복사하여 실행 가능

### 배포 시 포함할 파일
- `GL_Analyzer.exe`
- `data/processed/gl_analyzer.duckdb` (데이터베이스 파일)

### 주의사항
- 실행 파일 크기가 큽니다 (~100-200MB, Python 포함)
- 첫 실행 시 Windows Defender가 경고할 수 있습니다 (서명되지 않은 실행 파일)

---

## 방법 2: Python 포터블 버전 포함 (대안)

Python을 포함한 포터블 버전을 만들려면:

1. **Python 포터블 다운로드**
   - https://www.python.org/downloads/ 에서 Windows embeddable package 다운로드
   - 압축 해제 후 프로젝트 폴더에 `python_portable/` 폴더로 복사

2. **배치 파일 수정**
   - `run_app.bat`에서 포터블 Python 경로 사용

3. **패키지 설치**
   - 포터블 Python의 pip로 패키지 설치

---

## 현재 배치 파일의 제한사항

현재 `run_app.bat`는:
- ✅ Python이 설치된 컴퓨터에서 작동
- ✅ 자동으로 패키지 설치
- ❌ Python이 없는 컴퓨터에서는 작동하지 않음

Python이 없는 환경에서는 위의 방법 1 또는 2를 사용하세요.
