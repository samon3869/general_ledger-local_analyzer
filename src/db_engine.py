from pathlib import Path
import duckdb

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
            
            query = f"""
                CREATE TABLE general_ledger AS 
                SELECT * FROM read_csv_auto(
                    '{safe_path}', 
                    strict_mode=False,   -- 잘못된 형식의 행 무시 (필수)
                    SAMPLE_SIZE=20000    -- 스키마 분석 범위
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


# --- 확인용 코드 ---
if __name__ == "__main__":
    engine = GLEngine()
    print(f"DB 파일 경로: {engine.db_path}")

    try:
        engine.prepare_table()
        print("\n--- Test Finished Successfully ---")
    except Exception as e:
        print(f"\n--- Test Failed: {e} ---")