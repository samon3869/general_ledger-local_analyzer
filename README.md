# General Ledger Analyzer
대용량 분개장(General Ledger) 데이터를 분석하는 포터블 도구

## 빠른 시작

### 개발자용 워크플로우 (WSL → 빌드 → 배포)

1. **Git Clone**
   ```bash
   git clone <repository-url>
   cd general_ledger-local_analyzer
   ```

2. **CSV 전처리** (Jupyter Notebook)
   ```bash
   jupyter notebook src/csv_data_normalizaion.ipynb
   ```
   - 전처리된 CSV 파일이 `data/working/after_processing/`에 생성됨

3. **DB 생성**
   ```bash
   python src/db_engine.py
   ```
   - `data/processed/gl_analyzer.duckdb` 파일 생성

4. **Windows용 빌드**
   ```bash
   ./build_exe  # 또는 build_exe 파일 더블클릭
   ```

5. **배포**
   - `dist/` 폴더 전체를 압축하여 팀원에게 전달
   - 자세한 내용은 `WORKFLOW.md` 참조

### 사용자용 (팀원)

**빌드된 .exe 파일이 있는 경우:**
1. 압축 해제
2. `GL_Analyzer.exe` 파일을 더블클릭하세요
3. 브라우저가 자동으로 열리며 앱이 실행됩니다

**Python 설치된 Windows 컴퓨터에서 개발 모드 실행:**
1. `run_app.bat` 파일을 더블클릭하세요
2. 브라우저가 자동으로 열리며 앱이 실행됩니다

## 폴더 구조

```
general_ledger-local_analyzer/
├── data/
│   └── processed/
│       └── gl_analyzer.duckdb    # DuckDB 데이터베이스 파일
├── src/
│   ├── app.py                    # Streamlit UI 메인 앱
│   ├── db_engine.py              # DuckDB 엔진
│   └── journal_entry_analyzer.py  # 분개장 분석 로직
├── requirements.txt              # Python 패키지 목록
├── build_exe                     # WSL에서 Windows용 빌드 (더블클릭)
├── build_exe_windows.py          # WSL에서 Windows용 빌드 스크립트
├── build_exe_windows.sh          # WSL에서 Windows용 빌드 스크립트 (Bash)
├── run_app.bat                   # Windows 실행 스크립트
└── BUILD.md                      # 빌드 가이드
```

## 기능

### Step 1: 조건 필터링
- SQL 스타일 조건문으로 데이터 필터링
- DuckDB WHERE 절 문법 사용

### Step 2: 전표 확장
- 조건에 맞는 행이 속한 전표의 모든 라인을 포함

### Step 3: 거래유형별 대표 표본
- 거래유형 해시값 기준으로 유형별 대표 전표 1개만 추출

## 사용 방법

1. **DB 파일 준비**: `data/processed/gl_analyzer.duckdb` 파일이 있어야 합니다.
2. **실행**: 
   - `.exe` 파일이 있으면 더블클릭
   - 없으면 `run_app.bat` 더블클릭 (Python 필요)
3. **브라우저에서 분석**: 자동으로 열린 브라우저에서 조건을 입력하고 분석하세요.

## 빌드 방법

### WSL에서 Windows용 .exe 빌드

1. **`build_exe` 파일을 더블클릭** (가장 간단)
2. 또는 터미널에서 `./build_exe` 실행
3. 빌드 완료 후 `dist/GL_Analyzer.exe` 생성

자세한 내용은 `BUILD.md` 참조

## 시스템 요구사항

### 실행 시 (Windows)
- 독립 실행 파일(.exe) 사용 시: Python 불필요
- `run_app.bat` 사용 시: Python 3.11 이상 필요

### 빌드 시 (WSL)
- Windows에 Python 3.11 이상 설치 필요
- WSL에서 Windows Python 경로 접근 가능해야 함

## 문제 해결

### Python을 찾을 수 없습니다
- Windows에 Python이 설치되어 있는지 확인하세요.
- WSL에서 Windows Python 경로 확인:
  ```bash
  ls /mnt/c/Python311/python.exe
  ```

### Windows Python 경로를 찾지 못합니다
- 수동으로 경로 지정:
  ```bash
  export WINDOWS_PYTHON=/mnt/c/Python311/python.exe
  ./build_exe
  ```

### 패키지 설치 실패
- 인터넷 연결을 확인하세요.
- Windows Python으로 수동 설치:
  ```bash
  /mnt/c/Python311/python.exe -m pip install -r requirements.txt
  ```

### DB 파일을 찾을 수 없습니다
- `data/processed/gl_analyzer.duckdb` 파일이 존재하는지 확인하세요.
- 또는 사이드바에서 올바른 DB 경로를 입력하세요.
