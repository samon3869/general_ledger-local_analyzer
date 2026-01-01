import duckdb
import os

class GLEngine:
    def __init__(self, db_path="data/processed/gl_analyzer.duckdb"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self):
        return duckdb.connect(self.db_path)

# --- 확인용 코드 ---
if __name__ == "__main__":
    engine = GLEngine()
    conn = engine.get_connection()
    print(f"DB 파일 생성 및 연결 성공: {engine.db_path}")
    conn.close()