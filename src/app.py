from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from db_engine import DEFAULT_DB_PATH, GLEngine
from journal_entry_analyzer import JournalEntryAnalyzer


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


def build_duckdb_query(
    columns: list[str],
    condition: str | None,
    expand_full_entry: bool,
    limit: int,
    je_col: str | None,
) -> str:
    """
    Step1 + Step2 를 DuckDB에서 처리하기 위한 쿼리 생성.
    - condition 은 사용자 입력 SQL 조각 (DuckDB 호환)으로 간주.
    - expand_full_entry=True면 조건에 걸린 jeonpyo_id 전체 라인을 반환.
    """
    base_condition = condition.strip() if condition and condition.strip() else "1=1"

    if expand_full_entry:
        if not je_col:
            raise ValueError("전표 식별 컬럼을 선택하세요.")
        return f"""
        WITH target AS (
            SELECT DISTINCT "{je_col}"
            FROM general_ledger
            WHERE {base_condition}
        )
        SELECT gl.*
        FROM general_ledger AS gl
        JOIN target USING ("{je_col}")
        LIMIT {limit}
        """
    else:
        return f"""
        SELECT *
        FROM general_ledger
        WHERE {base_condition}
        LIMIT {limit}
        """


# --------- UI --------- #
def main() -> None:
    st.set_page_config(page_title="GL Analyzer", layout="wide")
    st.title("📊 General Ledger Analyzer")
    st.caption("DuckDB + Streamlit frontend for filtered ledger queries.")

    st.sidebar.header("연결 설정")
    db_path_input = st.sidebar.text_input(
        "DuckDB 파일 경로", value=str(DEFAULT_DB_PATH)
    ).strip()

    db_path = Path(db_path_input)
    if not db_path.exists():
        st.error(f"DB 파일을 찾을 수 없습니다: {db_path}")
        st.stop()

    engine = get_engine(str(db_path))
    columns = get_table_columns(str(db_path))
    if not columns:
        st.error("general_ledger 테이블 정보를 가져오지 못했습니다.")
        st.stop()

    st.sidebar.header("Step1: 조건 입력")
    condition = st.sidebar.text_area(
        "SQL 스타일 조건 (DuckDB WHERE 절용)",
        placeholder="예: amount > 10000000 AND account_code = '10100'",
        height=80,
    )
    with st.sidebar.expander("조건 작성 도움말", expanded=False):
        st.markdown(
            """
            - 컬럼명: 공백/대문자는 `"COLUMN"` 처럼 쌍따옴표로 감싸세요.
            - 문자열 값: 항상 `'텍스트'` 단일따옴표 사용.
            - 숫자처럼 보이지만 문자열로 저장된 컬럼은 반드시 `'123'`처럼 따옴표로 감싸세요.
            - 예시
              - `"NAME" = 'O''Connor'` (문자열 내 작은따옴표는 두 번 연속으로)
              - `"CLASSDESCR" = 'Cash Flow Reserve Fund'`
              - `amount > 10000000 AND account_code = '10100'`
              - `"DESCRIPTION" ILIKE '%bonus%'` (대소문자 무시 contains)
              - `"DATE" BETWEEN '2025-01-01' AND '2025-01-31'`
              - `"ACCOUNT" IN ('10100','20100')`
              - `"MEMO" IS NULL` / `"MEMO" IS NOT NULL`
            """
        )

    st.sidebar.markdown("---")
    st.sidebar.header("Step2: 전표 확장 설정")
    expand_full = st.sidebar.checkbox("라인이 속해있는 전표의 모든 라인 출력", value=True)
    
    # je_col은 Step2가 활성화되어 있을 때만 선택 가능
    je_col = None
    if expand_full:
        je_default = columns.index("jeonpyo_id") if "jeonpyo_id" in columns else 0
        je_col = st.sidebar.selectbox(
            "전표 식별 컬럼",
            options=columns,
            index=je_default,
        )

    st.sidebar.markdown("---")
    st.sidebar.header("Step3: 거래유형 대표 표본")
    unique_only = st.sidebar.checkbox("거래유형별 1개 전표만 남김", value=True)

    hash_col = None
    if unique_only:
        hash_default = columns.index("transaction_hash") if "transaction_hash" in columns else 0
        hash_col = st.sidebar.selectbox(
            "거래유형 해시 컬럼",
            options=columns,
            index=hash_default,
        )

    limit = st.sidebar.slider(
        "조회 최대 행 수 (DB LIMIT)", min_value=1000, max_value=200000, value=50000, step=1000
    )

    st.sidebar.write("---")
    run = st.sidebar.button("실행 (Step1→2→3)")

    total_rows = get_total_count(str(db_path))
    st.metric("총 행 수", f"{total_rows:,}")

    if run:
        try:
            query = build_duckdb_query(columns, condition, expand_full, limit, je_col)
        except Exception as exc:
            st.error(f"쿼리 준비 실패: {exc}")
            return
        with st.spinner("쿼리 실행 중..."):
            try:
                df = engine.run_query(query)
            except Exception as exc:
                st.error(f"쿼리 실행 실패: {exc}")
                return

        if df.empty:
            st.warning("조건에 맞는 데이터가 없습니다.")
            return

        result = df
        if unique_only:
            if not hash_col:
                st.error("거래유형 해시 컬럼을 선택하세요.")
                return
            if not je_col:
                st.error("Step3를 사용하려면 Step2를 먼저 활성화하고 전표 식별 컬럼을 선택하세요.")
                return
            # Analyzer는 jeonpyo_id / transaction_hash 명칭을 기대하므로 임시 매핑
            mapped_df = df.rename(columns={je_col: "jeonpyo_id", hash_col: "transaction_hash"})
            analyzer = JournalEntryAnalyzer(mapped_df)
            result_mapped = analyzer.unique_representative(mapped_df, unique_pattern_only=True)
            # 출력 시 원본 컬럼명으로 복원
            result = result_mapped.rename(columns={"jeonpyo_id": je_col, "transaction_hash": hash_col})

        st.success(
            f"Step1+2 결과 {len(df):,}행 → Step3 적용 후 {len(result):,}행 (표시 최대 {limit:,}행)"
        )
        st.dataframe(result, use_container_width=True, hide_index=True)

        if not result.empty:
            csv = result.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="CSV 다운로드",
                data=csv,
                file_name="general_ledger_filtered.csv",
                mime="text/csv",
            )

    else:
        st.info("좌측 필터를 설정하고 '쿼리 실행'을 눌러주세요.")


if __name__ == "__main__":
    main()
