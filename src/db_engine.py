from contextlib import contextmanager
from pathlib import Path

import duckdb
import pandas as pd

DEFAULT_DB_PATH = Path("data/processed/gl_analyzer.duckdb")
GL_FOLDER_PATH = Path("data/processed/raw_after_normalization")

# Known column types to override default VARCHAR inference
KNOWN_TYPES = {
    "회계월": "INTEGER",
    "전표번호": "INTEGER",
    "전표행번": "INTEGER",
    "환율": "DOUBLE",
    "전표금액": "DOUBLE",
    "차변금액": "DOUBLE",
    "대변금액": "DOUBLE",
    "전표금액기준통화": "DOUBLE",
    "차변금액기준통화": "DOUBLE",
    "대변금액기준통화": "DOUBLE",
}

class GLEngine:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _connection(self):
        """Context manager that always closes the DuckDB connection."""
        conn = duckdb.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def collect_schema(self, folder_path: Path | str = GL_FOLDER_PATH) -> dict[str, str]:
        """폴더 내 첫 번째 CSV 파일을 샘플로 하여 테이블 스키마 생성."""
        csv_files = sorted(Path(folder_path).glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"'{folder_path}' 폴더에 CSV 파일이 없습니다.")

        sample_file = csv_files[0]
        df = pd.read_csv(sample_file, nrows=0)
        all_columns = set(df.columns.tolist())

        return {col: KNOWN_TYPES.get(col, "VARCHAR") for col in sorted(all_columns)}
    
    def create_table(self, column_types: dict[str, str]) -> None:
        with self._connection() as conn:
            cursor = conn.cursor()

            cursor.execute("DROP TABLE IF EXISTS general_ledger")

            cols = ",\n".join(
                f'"{col}" {dtype}' for col, dtype in column_types.items()
            )

            cursor.execute(f"""
                CREATE TABLE general_ledger (
                    {cols}
                );
            """)

    def ingest_csv_files(self, csv_path: Path | str | None = None) -> None:
        p = Path(csv_path) if csv_path else None
        if not p or not p.exists():
            print(f"파일을 찾을 수 없습니다: {p.absolute() if p else csv_path}")
            return

        with self._connection() as conn:
            cursor = conn.cursor()

            try:
                print(f"🚀 '{p.name}' 검증 및 적재 시작...")

                df = pd.read_csv(p, dtype=str)
                src_row_count = len(df)

                cursor.execute("PRAGMA table_info('general_ledger')")
                table_cols = [row[1] for row in cursor.fetchall()]  # row[1]이 컬럼명

                df = df.reindex(columns=table_cols, fill_value=pd.NA)
                df = df.where(pd.notna(df), None)

                conn.register("tmp_df", df)

                conn.execute("SELECT COUNT(*) FROM general_ledger")
                before_count = conn.fetchone()[0]

                conn.execute("""
                    INSERT INTO general_ledger
                    SELECT * FROM tmp_df
                """)

                conn.commit()

                conn.execute("SELECT COUNT(*) FROM general_ledger")
                after_count = conn.fetchone()[0]
                inserted_rows = after_count - before_count

                print(f"\n--- 📊 적재 리포트 ---")
                print(f"📄 원본 CSV 행 수: {src_row_count:,}")
                print(f"📥 DB 적재 행 수: {inserted_rows:,}")
                print(f"💯 CSV 칼럼 부족 → NULL 처리 완료")

            except Exception as e:
                print(f"❌ 적재 중 치명적 오류: {e}")
                raise
            finally:
                try:
                    conn.unregister("tmp_df")
                except Exception:
                    pass

                cursor.close()

    def ingest_all_raw_data(self, folder_path: Path | str = GL_FOLDER_PATH) -> None:
        """폴더 내의 모든 CSV 파일을 순차적으로 적재합니다."""
        p = Path(folder_path)
        if not p.is_dir():
            print(f"파일을 찾을 수 없습니다: {folder_path}")
            return
        
        csv_files = sorted(list(p.glob("*.csv"))) # 순서대로 적재하기 위해 정렬
        total_files = len(csv_files)
        if total_files == 0:
            print("적재할 CSV 파일이 없습니다.")
            return

        print(f"총 {total_files}개의 파일을 발견했습니다.")

        success_count = 0
        for i, file_path in enumerate(csv_files):
            print(f"\n[{i+1}/{total_files}] 작업중...: {file_path.name}")
            try:
                # 기존의 정밀 적재 메서드 호출
                self.ingest_csv_files(file_path)
                success_count += 1
            except Exception as e:
                print(f"⚠️ 파일 적재 실패({file_path.name}): {e}")

        print(f"\n✅ 전체 공정 완료: {success_count}/{total_files} 파일 적재 성공")
            
    def run_query(self, query: str) -> pd.DataFrame:
        """UI에서 요청한 쿼리 실행 결과를 Pandas DataFrame으로 반환"""
        with self._connection() as conn:
            cursor = conn.cursor()
            df = cursor.execute(query).df()
            cursor.close()

        return df


# --- 확인용 코드 ---
if __name__ == "__main__":    
    engine = GLEngine()
    print(f"🚀 분석 엔진 가동 (DB: {engine.db_path})")

    try:
        # 1단계: 스키마 초기화 및 빈 테이블 생성
        print("\n[Step 1] 테이블 스키마 준비 중...")
        schema = engine.collect_schema()
        engine.create_table(schema)
        
        # 2단계: 폴더 내 모든 파일 순차 적재
        print("\n[Step 2] 데이터 적재 및 무결성 검사 중...")
        engine.ingest_all_raw_data()
        
        # 3단계: 최종 데이터 확인
        print("\n[Step 3] 검증...")
        summary_query = "SELECT COUNT(*) as total FROM general_ledger"
        total = engine.run_query(summary_query)['total'][0]
        print(f"\n[최종결과] DB 내 총 행 수: {total:,} 건")
        
    except Exception as e:
        print(f"\n🚨 시스템 오류: {e}")