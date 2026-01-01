from pathlib import Path
import duckdb
import subprocess
import pandas as pd

# DB 경로설정
DEFAULT_DB_PATH = Path("data/processed/gl_analyzer.duckdb")
# csv 폴더경로설정
GL_FOLDER_PATH = Path("data/processed/raw_after_normalization")

class GLEngine:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self):
        return duckdb.connect(self.db_path)

    def collect_schema(self, folder_path=GL_FOLDER_PATH):
        """
        폴더 내 첫 번째 파일을 샘플로 하여 테이블 스키마 생성
        """
        # 폴더 내의 첫 번째 csv 파일 찾기
        csv_files = sorted(list(Path(folder_path).glob("*.csv")))
        if not csv_files:
            raise FileNotFoundError(f"'{folder_path}' 폴더에 CSV 파일이 없습니다.")
        sample_file = csv_files[0]            
        
        # 칼럼 datatype 사전작업
        df = pd.read_csv(sample_file, nrows=0) # 헤더만 읽기
        all_columns = set(df.columns.tolist()) # CSV에 실제 존재하는칼럼

        known_types = {
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

        return {
                col: known_types.get(col, "VARCHAR")
                for col in sorted(all_columns)
            }
    
    def create_table(self, column_types):
        conn = self.get_connection()
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

        conn.close()

    def ingest_csv_files(self, csv_path=None):
        p = Path(csv_path)
        if not p.exists():
            print(f"파일을 찾을 수 없습니다: {p.absolute()}")
            return

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            print(f"🚀 '{p.name}' 검증 및 적재 시작...")

            # 1️⃣ CSV 읽기
            df = pd.read_csv(p, dtype=str)
            src_row_count = len(df)

            # 2️⃣ DB 테이블 칼럼 가져오기
            cursor.execute("PRAGMA table_info('general_ledger')")
            table_cols = [row[1] for row in cursor.fetchall()]  # row[1]이 컬럼명

            # 3️⃣ 스키마 정렬 + NULL 처리
            df = df.reindex(columns=table_cols, fill_value=pd.NA)
            df = df.where(pd.notna(df), None)

            # 4️⃣ Pandas → DuckDB 가상 테이블 등록
            conn.register("tmp_df", df)

            # 5️⃣ 적재 전 행 수확인
            conn.execute("SELECT COUNT(*) FROM general_ledger")
            before_count = conn.fetchone()[0]

             # 6️⃣ 실제 테이블 적재
            conn.execute("""
                INSERT INTO general_ledger
                SELECT * FROM tmp_df
            """)

            conn.commit()

            # 7 적재후 행 수 확인
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
            # 7️⃣ 가상 테이블 해제 (중요)
            try:
                conn.unregister("tmp_df")
            except Exception:
                pass

            cursor.close()
            conn.close()

    def ingest_all_raw_data(self, folder_path=GL_FOLDER_PATH):
        """
        폴더 내의 모든 CSV 파일을 스캔하여 순차적으로 적재합니다.
        """
        p = Path(folder_path)
        if not p.is_dir():
            print(f"파일을 찾을 수 없습니다: {folder_path}")
            return
        
        # 모든 csv 파일 목록 가져오기
        csv_files = sorted(list(p.glob("*.csv"))) # 순서대로 적재하기 위해 정렬
        total_files = len(csv_files)
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
            
    def run_query(self, query):
        """UI에서 요청한 쿼리 실행 결과를 Pandas DataFrame으로 반환"""
        conn = self.get_connection()
        cursor = conn.cursor()
        df = cursor.execute(query).df()
        cursor.close()
        conn.close()

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