# general_ledger-local_analyzer
A tool to analyze local General Ledger records exceeding 1 million lines

## 1. WSL + pyenv 설정

[env-settings.md 파일 참고](https://github.com/samon3869/Costaurant/blob/main/env-settings.md)
```bash
pyenv virtualenv 3.11.9 general_ledger-local-analyzer
pyenv local general_ledger-local-analyzer
```

## 2. Standalone App 폴더구조 Design

```bash
GL_Analyzer/
├── data/
│   ├── raw/                # General Ledger(CSV)를 넣는 곳
│   └── processed/          # 생성된 gl_data.duckdb 파일이 저장되는 곳
├── src/
│   ├── app.py              # Main Streamlit UI 코드
│   ├── db_engine.py        # DuckDB 쿼리 및 변환 로직
│   └── utils.py            # 회계 로직 (회계 계정 분류 등)
├── config.yaml             # 경로 및 설정 파일
├── requirements.txt        # 필요한 라이브러리 목록
├── run_app.bat             # (중요) 동료들이 더블클릭할 실행 파일
└── .gitignore
```

