from pathlib import Path
import duckdb

DEFAULT_DB_PATH = Path("data/processed/gl_analyzer.duckdb")

class GLEngine:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self):
        return duckdb.connect(self.db_path)

# --- 확인용 코드 ---
if __name__ == "__main__":
    engine = GLEngine()
    conn = engine.get_connection()
    print(f"DB 파일 생성 및 연결 성공: {engine.db_path}")
    conn.close()