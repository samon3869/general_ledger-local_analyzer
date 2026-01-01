from pathlib import Path
import duckdb
import subprocess

# DB 경로설정
DEFAULT_DB_PATH = Path("data/processed/gl_analyzer.duckdb")
# 더미 csv 경로설정
OKLAHOMA_SAMPLE_GL_PATH = Path("data/raw/oklahoma_GL_2025_4Q.csv")

class GLEngine:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self):
        return duckdb.connect(self.db_path)

    def prepare_table(self, first_csv_path=OKLAHOMA_SAMPLE_GL_PATH):
        """
        테이블 스키마 생성
        """
        p = Path(first_csv_path)
        if not p.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {p.absolute()}")
            
        safe_path = p.resolve().as_posix()
        display_name = p.name

        conn = self.get_connection()
        cursor = conn.cursor()
            
        try:
            cursor.execute("DROP TABLE IF EXISTS general_ledger")
            
            # STRICT_MODE를 제거하는 대신, 모호한 설정들을 수동으로 확정합니다.
            query = f"""
                CREATE TABLE general_ledger AS 
                SELECT * FROM read_csv_auto(
                    '{safe_path}', 
                    ALL_VARCHAR=TRUE,
                    STRICT_MODE=FALSE,
                    SAMPLE_SIZE=10000
                ) 
                LIMIT 0
            """
            cursor.execute(query)
            
            schema_info = cursor.execute("PRAGMA table_info('general_ledger')").fetchall()
            
            print(f"✅ Schema successfully created from local file: {display_name}")
            print(f"📊 Detected Columns: {len(schema_info)} total")
            
            for col in schema_info[:10]:
                print(f"   - {col[1]} ({col[2]})")
                
            return schema_info
                    
        except Exception as e:
            print(f"❌ Error creating schema: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def ingest_csv_files(self, csv_path=OKLAHOMA_SAMPLE_GL_PATH):
        """
        CSV 데이터를 테이블에 대량 적재 및 물리적 행 수 기반 무결성 검증
        """
        p = Path(csv_path)
        if not p.exists():
            print(f"파일을 찾을 수 없습니다: {p.absolute()}")
            return

        safe_path = p.resolve().as_posix()
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 이전 에러 로그 테이블 삭제
            cursor.execute("DROP TABLE IF EXISTS ingestion_errors")

            print(f"🚀 '{p.name}' 검증 및 적재 시작...")
            
            # 1. 시스템 명령어 'wc -l'로 물리적 라인 수 파악
            # DuckDB의 파싱 에러와 상관없이 파일의 실제 줄 수를 셉니다.
            wc_result = subprocess.run(['wc', '-l', safe_path], capture_output=True, text=True)
            total_lines = int(wc_result.stdout.split()[0])
            raw_data_count = total_lines - 1  # 헤더 제외

            # 2. COPY 문 실행 시 REJECTS_TABLE 옵션 추가
            # 어떤 행이, 왜 에러가 나서 넘어갔는지 'ingestion_errors' 테이블에 기록합니다.
            query = f"""
                COPY general_ledger FROM '{safe_path}' (
                    HEADER TRUE,
                    STRICT_MODE FALSE,
                    NULL_PADDING TRUE,
                    REJECTS_TABLE 'ingestion_errors'
                );
            """
            cursor.execute(query)
            
            # 3. 에러 발생 여부 확인
            cursor.execute("SELECT count(*) FROM ingestion_errors")
            error_count = cursor.fetchone()[0]
            
            # 4. 결과 리포트
            cursor.execute("SELECT count(*) FROM general_ledger")
            final_count = cursor.fetchone()[0]

            print(f"\n--- 📊 정밀 검증 리포트 ---")
            print(f"📥 DB 적재 성공: {final_count:,} 행")
            print(f"❌ 파싱 에러(Rejected): {error_count:,} 행")
            
            if error_count > 0:
                print(f"⚠️ 에러 내용 일부 (Top 3):")
                # 에러 원인 컬럼 등을 조회 (DuckDB 버전에 따라 컬럼명 상이할 수 있음)
                cursor.execute("SELECT line_number, error_message FROM ingestion_errors LIMIT 3")
                for err in cursor.fetchall():
                    print(f"  - 라인 {err[0]}: {err[1]}")
            else:
                print(f"💯 파싱 에러가 단 한 건도 발생하지 않았습니다.")

        except Exception as e:
            print(f"❌ 적재 중 치명적 오류: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

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
        engine.prepare_table()
        
        # 2단계: 데이터 적재 및 무결성 검증
        print("\n[Step 2] 데이터 적재 및 무결성 검사 중...")
        engine.ingest_csv_files()
        
        # 3단계: 실제 데이터 조회 테스트 (run_query 활용)
        print("\n[Step 3] 데이터 조회 테스트 (Top 5 Rows)")
        print("-" * 50)
        
        # 데이터가 실제로 존재하는지 상위 5개 행을 가져와 봅니다.
        # 이 단계에서 데이터가 화면에 출력되면 성공입니다.
        try:
            sample_query = "SELECT * FROM general_ledger LIMIT 5"
            df_sample = engine.run_query(sample_query)
            
            if not df_sample.empty:
                print(df_sample)
                
                # 집계 쿼리도 한 번 날려봅니다.
                count_query = "SELECT COUNT(*) as total_rows FROM general_ledger"
                total_count = engine.run_query(count_query)['total_rows'][0]
                print(f"\n✅ 조회 결과: 총 {total_count:,} 개의 행이 DB에 저장되어 있습니다.")
            else:
                print("⚠️ 테이블은 생성되었으나 데이터가 비어있습니다.")
        except Exception as query_err:
            print(f"❌ 쿼리 실행 중 오류: {query_err}")

        print("-" * 50)
        print("✨ Commit 3: 적재 및 무결성 검증 단계 완료")
        
    except Exception as e:
        print(f"\n🚨 테스트 중단: {e}")