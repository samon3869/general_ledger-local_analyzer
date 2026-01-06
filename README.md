# General Ledger Analyzer
대용량 분개장(General Ledger) 데이터를 분석하는 포터블 도구

## 빠른 시작

### Windows 사용자
1. `run_app.bat` 파일을 더블클릭하세요.
2. 브라우저가 자동으로 열리며 앱이 실행됩니다.

### Linux/Mac 사용자
1. `run_app.sh` 파일을 더블클릭하거나 터미널에서 실행:
   ```bash
   ./run_app.sh
   ```
2. 또는 Python 스크립트로 실행:
   ```bash
   python run_app.py
   ```

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
├── run_app.bat                   # Windows 실행 스크립트
├── run_app.sh                    # Linux/Mac 실행 스크립트
└── run_app.py                    # 크로스 플랫폼 Python 실행 스크립트
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
2. **실행 스크립트 실행**: 운영체제에 맞는 실행 파일을 더블클릭하세요.
3. **브라우저에서 분석**: 자동으로 열린 브라우저에서 조건을 입력하고 분석하세요.

## 시스템 요구사항

- Python 3.11 이상
- 필요한 패키지는 `requirements.txt`에 명시되어 있으며, 실행 시 자동 설치됩니다.

## 문제 해결

### Python을 찾을 수 없습니다
- Python이 설치되어 있는지 확인하세요.
- PATH 환경변수에 Python이 포함되어 있는지 확인하세요.

### 패키지 설치 실패
- 인터넷 연결을 확인하세요.
- 수동으로 설치: `pip install -r requirements.txt`

### DB 파일을 찾을 수 없습니다
- `data/processed/gl_analyzer.duckdb` 파일이 존재하는지 확인하세요.
- 또는 사이드바에서 올바른 DB 경로를 입력하세요.
