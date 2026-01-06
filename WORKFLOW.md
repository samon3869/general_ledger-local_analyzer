# 작업 워크플로우

## 전체 프로세스

1. **Git Clone** (WSL 환경)
2. **CSV 전처리** (`csv_data_normalizaion.ipynb` 사용)
3. **DB 생성** (`db_engine.py` 실행)
4. **Windows용 빌드** (WSL에서)
5. **배포** (빌드된 파일만 팀원에게 전달)

---

## 단계별 가이드

### 1단계: Git Clone

```bash
git clone <repository-url>
cd general_ledger-local_analyzer
```

### 2단계: CSV 전처리

Jupyter Notebook으로 CSV 파일들을 전처리합니다.

```bash
# Jupyter Notebook 실행
jupyter notebook src/csv_data_normalizaion.ipynb
```

**결과:**
- `data/working/after_processing/` 폴더에 전처리된 CSV 파일들 생성
- 각 파일에 `거래유형그룹_해시값` 컬럼이 추가됨

### 3단계: DB 생성

전처리된 CSV 파일들로부터 DB를 생성합니다.

```bash
# db_engine.py 실행
python src/db_engine.py
```

**결과:**
- `data/processed/gl_analyzer.duckdb` 파일 생성

### 4단계: Windows용 빌드

WSL에서 Windows용 .exe 파일을 빌드합니다.

```bash
# 방법 1: 더블클릭 (파일 매니저에서)
# build_exe 파일을 더블클릭

# 방법 2: 터미널에서 실행
./build_exe
```

**결과:**
- `dist/GL_Analyzer.exe` 생성
- `dist/data/` 폴더 복사됨

### 5단계: 배포

**옵션 1: dist 폴더 전체 배포 (권장)**
```
dist/
├── GL_Analyzer.exe
└── data/
    └── processed/
        └── gl_analyzer.duckdb
```
→ `dist` 폴더를 압축하여 팀원에게 전달

**옵션 2: 파일만 배포**
- `GL_Analyzer.exe`
- `data/` 폴더 전체
→ 같은 폴더에 두고 압축하여 전달

**팀원 사용법:**
1. 압축 해제
2. `GL_Analyzer.exe` 더블클릭
3. 브라우저에서 분석 시작

---

## 주의사항

- ✅ DB 파일(`gl_analyzer.duckdb`)은 반드시 `.exe`와 같은 위치의 `data/processed/` 폴더에 있어야 합니다
- ✅ 빌드 시 `data` 폴더가 자동으로 `dist`에 복사됩니다
- ✅ Python이 없는 컴퓨터에서도 실행 가능합니다

---

## 문제 해결

### DB 생성 실패
- CSV 파일 경로 확인
- CSV 파일이 올바른 형식인지 확인

### 빌드 실패
- Windows Python이 설치되어 있는지 확인
- Windows Python 경로를 찾지 못하면 환경변수 설정:
  ```bash
  # 현재 세션에서만 (임시)
  export WINDOWS_PYTHON=/mnt/c/Python311/python.exe
  
  # 영구적으로 설정하려면 ~/.bashrc에 추가
  echo 'export WINDOWS_PYTHON=/mnt/c/Python311/python.exe' >> ~/.bashrc
  source ~/.bashrc
  ```
- 자세한 내용은 `SETUP.md` 참조

### Python 버전 관련
**중요:** 빌드에 사용하는 **Windows Python 버전**이 중요합니다.
- WSL의 가상환경 Python 버전과 같을 필요는 없지만, 비슷한 버전(예: 3.11)을 사용하는 것을 권장합니다
- 빌드 시 Windows Python에 `requirements.txt`가 설치되므로, Windows Python 버전이 빌드된 .exe의 Python 버전이 됩니다
- 권장: Windows Python 3.11 이상

### 실행 시 DB를 찾을 수 없음
- `.exe`와 같은 폴더에 `data/processed/gl_analyzer.duckdb`가 있는지 확인
- 사이드바에서 DB 경로를 수동으로 지정 가능
