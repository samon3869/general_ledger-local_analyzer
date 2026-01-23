from __future__ import annotations

import streamlit as st

from db_engine import GLEngine


def render_sql_query_tab(engine: GLEngine, columns: list[str]) -> None:
    """SQL 직접입력 탭 렌더링."""
    st.header("SQL 직접입력")
    st.markdown("DuckDB SQL 쿼리를 직접 입력하여 실행할 수 있습니다.")
    
    with st.sidebar.expander("📝 SQL 쿼리 입력", expanded=True):
        st.markdown("**SQL 쿼리 작성**")
        sql_query = st.text_area(
            "SQL 쿼리를 입력하세요",
            placeholder="예: SELECT * FROM general_ledger LIMIT 100",
            height=200,
            key="sql_query",
            help="DuckDB SQL 쿼리를 직접 입력하세요. general_ledger 테이블을 조회할 수 있습니다.",
        )
        
        st.markdown("---")
        run_sql = st.button("SQL 실행", type="primary", key="run_sql", use_container_width=True)
        
        # HTML details 태그를 사용하여 접을 수 있는 도움말 생성
        st.markdown(
            """
            <details>
            <summary style="cursor: pointer; color: #1f77b4; font-weight: bold;">📖 SQL 작성 도움말</summary>
            
            **테이블명:**
            - `general_ledger` 테이블을 조회할 수 있습니다
            
            **컬럼명 작성 규칙:**
            - 공백이나 대문자가 포함된 컬럼명은 `"COLUMN"` 처럼 쌍따옴표로 감싸세요
            - 일반 컬럼명은 따옴표 없이 사용 가능합니다
            
            **사용 예시:**
            - `SELECT * FROM general_ledger LIMIT 100`
            - `SELECT "회계월", "전표번호", SUM("차변금액") FROM general_ledger GROUP BY "회계월", "전표번호"`
            - `SELECT * FROM general_ledger WHERE "회계월" = 202501`
            
            **주의사항:**
            - DELETE, DROP, ALTER 등 데이터를 변경하거나 삭제하는 쿼리는 실행되지 않습니다
            - SELECT 쿼리만 실행 가능합니다
            </details>
            """,
            unsafe_allow_html=True,
        )
    
    # 실행 로직
    run_sql = st.session_state.get("run_sql", False)
    
    # SQL 실행 버튼이 눌렸을 때만 새로 조회하고 결과를 저장
    if run_sql:
        sql_query = st.session_state.get("sql_query", "").strip()
        
        if not sql_query:
            st.warning("SQL 쿼리를 입력해주세요.")
            if "sql_query_result" in st.session_state:
                del st.session_state["sql_query_result"]
            if "sql_query_result_info" in st.session_state:
                del st.session_state["sql_query_result_info"]
        else:
            # 보안: SELECT만 허용 (대소문자 무시)
            query_upper = sql_query.upper().strip()
            if not query_upper.startswith("SELECT"):
                st.error("SELECT 쿼리만 실행 가능합니다.")
                if "sql_query_result" in st.session_state:
                    del st.session_state["sql_query_result"]
                if "sql_query_result_info" in st.session_state:
                    del st.session_state["sql_query_result_info"]
            else:
                with st.spinner("SQL 쿼리 실행 중..."):
                    try:
                        df = engine.run_query(sql_query)
                        # 결과 저장
                        st.session_state["sql_query_result"] = df
                        st.session_state["sql_query_result_info"] = f"쿼리 실행 완료: {len(df):,}행"
                    except Exception as exc:
                        st.error(f"SQL 쿼리 실행 실패: {exc}")
                        # 오류 발생 시 기존 결과도 초기화
                        if "sql_query_result" in st.session_state:
                            del st.session_state["sql_query_result"]
                        if "sql_query_result_info" in st.session_state:
                            del st.session_state["sql_query_result_info"]
    
    # 저장된 결과가 있으면 표시 (SQL 실행 버튼을 누르지 않아도 유지)
    if "sql_query_result" in st.session_state and st.session_state["sql_query_result"] is not None:
        df = st.session_state["sql_query_result"]
        result_info = st.session_state.get("sql_query_result_info", "")
        
        if result_info:
            st.success(result_info)
        
        # 결과 크기 체크 (메모리 사용량)
        result_memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        MAX_DISPLAY_SIZE_MB = 200  # 200MB 이상이면 일부만 표시
        
        if result_memory_mb > MAX_DISPLAY_SIZE_MB:
            st.warning(
                f"⚠️ 결과 크기가 {result_memory_mb:.1f}MB로 큽니다. "
                f"화면에는 처음 100,000행만 표시되며, 전체 데이터는 CSV 다운로드를 이용해주세요."
            )
            # 처음 100,000행만 표시
            display_result = df.head(100000)
            st.dataframe(display_result, use_container_width=True, hide_index=True)
            st.info(f"전체 {len(df):,}행 중 처음 100,000행만 표시됩니다.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="CSV 다운로드 (전체 데이터)",
            data=csv,
            file_name="sql_query_result.csv",
            mime="text/csv",
            key="csv_download_sql",
        )
        
        # 쿼리 미리보기
        with st.expander("실행된 쿼리 보기"):
            st.code(st.session_state.get("sql_query", ""), language="sql")
    elif not run_sql:
        st.info("좌측 사이드바에서 SQL 쿼리를 입력하고 'SQL 실행' 버튼을 눌러주세요.")
