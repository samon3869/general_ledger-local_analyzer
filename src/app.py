from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

from db_engine import DEFAULT_DB_PATH, GLEngine
from tab_aggregation import render_aggregation_tab
from tab_query import render_query_tab
from tab_sql_query import render_sql_query_tab


# --------- Cached helpers --------- #
@st.cache_resource(show_spinner=False)
def get_engine(db_path: str) -> GLEngine:
    return GLEngine(db_path)


@st.cache_data(show_spinner=False)
def get_table_columns(db_path: str) -> list[str]:
    """Return column names of the general_ledger table."""
    engine = GLEngine(db_path)
    try:
        info = engine.run_query("PRAGMA table_info('general_ledger')")
    except Exception:
        return []
    return info["name"].tolist() if "name" in info.columns else []


@st.cache_data(show_spinner=False)
def get_distinct_values(db_path: str, column: str, limit: int = 100) -> list[str]:
    engine = GLEngine(db_path)
    try:
        df = engine.run_query(
            f'SELECT DISTINCT "{column}" AS val FROM general_ledger '
            f'WHERE "{column}" IS NOT NULL ORDER BY 1 LIMIT {limit}'
        )
    except Exception:
        return []
    return df["val"].dropna().astype(str).tolist() if "val" in df.columns else []


@st.cache_data(show_spinner=False)
def get_total_count(db_path: str) -> int:
    engine = GLEngine(db_path)
    try:
        df = engine.run_query("SELECT COUNT(*) AS cnt FROM general_ledger")
        return int(df["cnt"][0])
    except Exception:
        return 0




# --------- UI --------- #
def main() -> None:
    st.set_page_config(page_title="GL Analyzer", layout="wide")
    st.title("📊 일반분개장 조회")
    st.caption("DuckDB + Streamlit frontend for filtered ledger queries.")

    st.sidebar.header("연결 설정")
    # 기본 DB 경로는 프로젝트 루트 기준 상대 경로
    # PyInstaller로 빌드된 경우와 일반 실행 모두 지원
    if getattr(sys, 'frozen', False):
        # PyInstaller --onefile 모드: 번들에 포함된 파일은 _MEIPASS에 있음
        import os
        if hasattr(sys, '_MEIPASS'):
            # 번들에 포함된 data 폴더에서 찾기
            meipass_path = Path(sys._MEIPASS)
            bundled_db = meipass_path / DEFAULT_DB_PATH
            if bundled_db.exists():
                default_db = bundled_db
            else:
                # 번들에 없으면 실제 exe 위치에서 찾기 (fallback)
                exe_dir_str = os.environ.get('EXE_DIR')
                if exe_dir_str:
                    exe_dir = Path(exe_dir_str).resolve()
                else:
                    cwd = Path(os.getcwd()).resolve()
                    if cwd.name == 'src':
                        exe_dir = cwd.parent
                    else:
                        exe_dir = cwd
                default_db = exe_dir / DEFAULT_DB_PATH
        else:
            # _MEIPASS가 없으면 실제 exe 위치 기준
            exe_dir_str = os.environ.get('EXE_DIR')
            if exe_dir_str:
                exe_dir = Path(exe_dir_str).resolve()
            else:
                cwd = Path(os.getcwd()).resolve()
                if cwd.name == 'src':
                    exe_dir = cwd.parent
                else:
                    exe_dir = cwd
            default_db = exe_dir / DEFAULT_DB_PATH
    else:
        # 일반 Python 실행
        default_db = Path(__file__).parent.parent / DEFAULT_DB_PATH
    
    db_path_input = st.sidebar.text_input(
        "DuckDB 파일 경로", value=str(default_db)
    ).strip()

    db_path = Path(db_path_input)
    # 상대 경로인 경우 프로젝트 루트 기준으로 변환
    if not db_path.is_absolute():
        if getattr(sys, 'frozen', False):
            # PyInstaller --onefile 모드: 번들에 포함된 파일은 _MEIPASS에 있음
            import os
            if hasattr(sys, '_MEIPASS'):
                meipass_path = Path(sys._MEIPASS)
                bundled_path = meipass_path / db_path
                if bundled_path.exists():
                    db_path = bundled_path
                else:
                    # 번들에 없으면 실제 exe 위치에서 찾기
                    exe_dir_str = os.environ.get('EXE_DIR')
                    if exe_dir_str:
                        exe_dir = Path(exe_dir_str).resolve()
                        db_path = exe_dir / db_path
                    else:
                        cwd = Path(os.getcwd()).resolve()
                        if cwd.name == 'src':
                            exe_dir = cwd.parent
                        else:
                            exe_dir = cwd
                        db_path = exe_dir / db_path
            else:
                # _MEIPASS가 없으면 실제 exe 위치 기준
                exe_dir_str = os.environ.get('EXE_DIR')
                if exe_dir_str:
                    exe_dir = Path(exe_dir_str).resolve()
                    db_path = exe_dir / db_path
                else:
                    cwd = Path(os.getcwd()).resolve()
                    if cwd.name == 'src':
                        exe_dir = cwd.parent
                    else:
                        exe_dir = cwd
                    db_path = exe_dir / db_path
        else:
            # 일반 Python 실행
            db_path = Path(__file__).parent.parent / db_path
    
    if not db_path.exists():
        # 디버깅 정보 표시
        debug_info = []
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                meipass_path = Path(sys._MEIPASS)
                debug_info.append(f"_MEIPASS: {meipass_path}")
                debug_info.append(f"_MEIPASS/data/processed/gl_analyzer.duckdb 존재: {(meipass_path / 'data' / 'processed' / 'gl_analyzer.duckdb').exists()}")
            debug_info.append(f"EXE_DIR: {os.environ.get('EXE_DIR', 'N/A')}")
            debug_info.append(f"sys.executable: {sys.executable}")
        
        st.error(f"DB 파일을 찾을 수 없습니다: {db_path}")
        with st.expander("디버깅 정보", expanded=True):
            for info in debug_info:
                st.text(info)
        st.stop()

    engine = get_engine(str(db_path))
    columns = get_table_columns(str(db_path))
    if not columns:
        st.error("general_ledger 테이블 정보를 가져오지 못했습니다.")
        st.stop()

    total_rows = get_total_count(str(db_path))
    st.metric("총 행 수", f"{total_rows:,}")

    # 조회 모드 선택
    st.sidebar.markdown("---")
    st.sidebar.header("조회 모드 선택")
    view_mode = st.sidebar.radio(
        "조회 모드를 선택하세요",
        options=["🔍 원장 조회", "📈 집계 데이터 조회", "💻 SQL 직접입력"],
        key="view_mode",
        label_visibility="visible",
    )
    
    # 선택된 모드에 따라 해당 기능 표시
    if view_mode == "🔍 원장 조회":
        render_query_tab(engine, columns)
    elif view_mode == "📈 집계 데이터 조회":
        render_aggregation_tab(engine, columns)
    else:  # "💻 SQL 직접입력"
        render_sql_query_tab(engine, columns)


# Streamlit은 스크립트를 import할 때 top-level 코드를 실행하므로
# main()을 항상 top-level에서 호출해야 합니다.
# Streamlit이 app.py를 import할 때 __name__은 "__main__"이 아니라 모듈 이름이지만,
# Streamlit은 top-level 코드를 실행하므로 main()을 항상 호출합니다.
main()
