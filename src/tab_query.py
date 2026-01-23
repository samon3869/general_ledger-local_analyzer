from __future__ import annotations

import pandas as pd
import streamlit as st

from db_engine import GLEngine
from journal_entry_analyzer import JournalEntryAnalyzer


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
    - expand_full_entry=True면 조건에 걸린 전표번호 전체 라인을 반환.
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


def render_query_tab(engine: GLEngine, columns: list[str]) -> None:
    """데이터 조회 탭 렌더링."""
    with st.sidebar.expander("🔍 데이터 조회 설정", expanded=True):
            st.header("Step1: 조건 입력")
            condition = st.text_area(
                "SQL 스타일 조건 (DuckDB WHERE 절용)",
                placeholder="예: amount > 10000000 AND account_code = '10100'",
                height=80,
                key="query_condition",
            )
            # HTML details 태그를 사용하여 접을 수 있는 도움말 생성 (expander 중첩 방지)
            st.markdown(
                """
                <details>
                <summary style="cursor: pointer; color: #1f77b4; font-weight: bold;">📖 조건 작성 도움말</summary>
                
                **컬럼명 작성 규칙:**
                - 공백이나 대문자가 포함된 컬럼명은 `"COLUMN"` 처럼 쌍따옴표로 감싸세요
                - 일반 컬럼명은 따옴표 없이 사용 가능합니다
                
                **값 작성 규칙:**
                - 문자열 값: 항상 `'텍스트'` 단일따옴표 사용
                - 숫자처럼 보이지만 문자열로 저장된 컬럼은 반드시 `'123'`처럼 따옴표로 감싸세요
                - 문자열 내 작은따옴표는 두 번 연속으로 작성: `'O''Connor'`
                
                **사용 예시:**
                - `"NAME" = 'O''Connor'` (문자열 내 작은따옴표 처리)
                - `"CLASSDESCR" = 'Cash Flow Reserve Fund'` (문자열 비교)
                - `amount > 10000000 AND account_code = '10100'` (숫자 및 문자열 비교)
                - `"DESCRIPTION" ILIKE '%bonus%'` (대소문자 무시 contains 검색)
                - `"DATE" BETWEEN '2025-01-01' AND '2025-01-31'` (날짜 범위)
                - `"ACCOUNT" IN ('10100','20100')` (여러 값 중 하나)
                - `"MEMO" IS NULL` / `"MEMO" IS NOT NULL` (NULL 값 체크)
                
                **주의사항:**
                - 컬럼명과 값의 따옴표 사용을 정확히 구분하세요
                - 문자열 값은 반드시 단일따옴표를 사용하세요
                </details>
                """,
                unsafe_allow_html=True,
            )
            
            st.markdown("---")
            st.header("Step2: 전표 확장 설정")
            expand_full = st.checkbox("라인이 속해있는 전표의 모든 라인 출력", value=False, key="expand_full")
            
            # je_col은 Step2가 활성화되어 있을 때만 선택 가능
            je_col = None
            if expand_full:
                je_default = columns.index("전표번호") if "전표번호" in columns else 0
                je_col = st.selectbox(
                    "전표 식별 컬럼",
                    options=columns,
                    index=je_default,
                    key="je_col",
                )

            st.markdown("---")
            st.header("Step3: 거래유형 대표 표본")
            unique_only = st.checkbox("거래유형별 1개 전표만 남김", value=False, key="unique_only")

            hash_col = None
            if unique_only:
                hash_default = columns.index("거래유형그룹_해시값") if "거래유형그룹_해시값" in columns else 0
                hash_col = st.selectbox(
                    "거래유형 해시 컬럼",
                    options=columns,
                    index=hash_default,
                    key="hash_col",
                )

            limit = st.slider(
                "조회 최대 행 수 (DB LIMIT)", min_value=1000, max_value=1000000, value=50000, step=1000, key="query_limit"
            )

            st.markdown("---")
            run = st.button("실행 (Step1→2→3)", key="run_query", use_container_width=True)

    # 실행 로직은 expander 밖에서 처리 (변수는 session_state에서 가져옴)
    run = st.session_state.get("run_query", False)
    
    # 조회 버튼이 눌렸을 때만 새로 조회하고 결과를 저장
    if run:
        # session_state에서 변수 가져오기
        condition = st.session_state.get("query_condition", "")
        expand_full = st.session_state.get("expand_full", False)
        unique_only = st.session_state.get("unique_only", False)
        limit = st.session_state.get("query_limit", 50000)
        je_col = st.session_state.get("je_col") if expand_full else None
        hash_col = st.session_state.get("hash_col") if unique_only else None
        try:
            query = build_duckdb_query(columns, condition, expand_full, limit, je_col)
            # 쿼리 저장
            st.session_state["query_executed"] = query
        except Exception as exc:
            st.error(f"쿼리 준비 실패: {exc}")
            # 오류 발생 시 기존 결과도 초기화
            if "query_result" in st.session_state:
                del st.session_state["query_result"]
            if "query_result_info" in st.session_state:
                del st.session_state["query_result_info"]
            if "query_executed" in st.session_state:
                del st.session_state["query_executed"]
        else:
            with st.spinner("쿼리 실행 중..."):
                try:
                    df = engine.run_query(query)
                except Exception as exc:
                    st.error(f"쿼리 실행 실패: {exc}")
                    # 오류 발생 시 기존 결과도 초기화
                    if "query_result" in st.session_state:
                        del st.session_state["query_result"]
                    if "query_result_info" in st.session_state:
                        del st.session_state["query_result_info"]
                    if "query_executed" in st.session_state:
                        del st.session_state["query_executed"]
                else:
                    if df.empty:
                        st.warning("조건에 맞는 데이터가 없습니다.")
                        # 빈 결과도 저장
                        st.session_state["query_result"] = None
                        st.session_state["query_result_info"] = "조건에 맞는 데이터가 없습니다."
                    else:
                        result = df
                        if unique_only:
                            if not hash_col:
                                st.error("거래유형 해시 컬럼을 선택하세요.")
                                st.session_state["query_result"] = None
                                st.session_state["query_result_info"] = None
                            elif not je_col:
                                st.error("Step3를 사용하려면 Step2를 먼저 활성화하고 전표 식별 컬럼을 선택하세요.")
                                st.session_state["query_result"] = None
                                st.session_state["query_result_info"] = None
                            else:
                                # Analyzer는 전표번호 / 거래유형그룹_해시값 명칭을 기대하므로 임시 매핑
                                mapped_df = df.rename(columns={je_col: "전표번호", hash_col: "거래유형그룹_해시값"})
                                analyzer = JournalEntryAnalyzer(mapped_df)
                                result_mapped = analyzer.unique_representative(mapped_df, unique_pattern_only=True)
                                # 출력 시 원본 컬럼명으로 복원
                                result = result_mapped.rename(columns={"전표번호": je_col, "거래유형그룹_해시값": hash_col})
                                # 결과 저장
                                st.session_state["query_result"] = result
                                st.session_state["query_result_info"] = f"Step1+2 결과 {len(df):,}행 → Step3 적용 후 {len(result):,}행 (표시 최대 {limit:,}행)"
                        else:
                            # 결과 저장
                            st.session_state["query_result"] = result
                            st.session_state["query_result_info"] = f"Step1+2 결과 {len(df):,}행 → Step3 적용 후 {len(result):,}행 (표시 최대 {limit:,}행)"
    
    # 저장된 결과가 있으면 표시 (조회 버튼을 누르지 않아도 유지)
    if "query_result" in st.session_state and st.session_state["query_result"] is not None:
        result = st.session_state["query_result"]
        result_info = st.session_state.get("query_result_info", "")
        
        # 실행된 쿼리 보기 (결과 위에 표시)
        if "query_executed" in st.session_state:
            with st.expander("실행된 쿼리 보기", expanded=False):
                st.code(st.session_state["query_executed"], language="sql")
        
        # 숫자형 컬럼 합계 계산 및 표시
        numeric_cols = result.select_dtypes(include=[pd.Int64Dtype(), pd.Float64Dtype(), 'int64', 'float64', 'int32', 'float32']).columns.tolist()
        if numeric_cols:
            st.markdown("### 📊 숫자형 컬럼 합계")
            st.markdown("조회된 데이터의 숫자형 컬럼 합계입니다.")
            
            # 각 숫자형 컬럼의 합계 계산
            summary_data = []
            for col in numeric_cols:
                try:
                    col_sum = result[col].sum()
                    # NaN이 아닌 값의 개수
                    non_null_count = result[col].notna().sum()
                    summary_data.append({
                        "컬럼명": col,
                        "합계": f"{col_sum:,.0f}" if pd.notna(col_sum) and col_sum == int(col_sum) else f"{col_sum:,.2f}",
                        "유효 행 수": f"{non_null_count:,}",
                    })
                except Exception:
                    # 합계 계산 실패 시 스킵
                    continue
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
            else:
                st.info("합계를 계산할 수 있는 숫자형 컬럼이 없습니다.")
        else:
            st.info("합계를 계산할 수 있는 숫자형 컬럼이 없습니다.")
        
        if result_info:
            st.success(result_info)
        
        # 결과 크기 체크 (메모리 사용량)
        result_memory_mb = result.memory_usage(deep=True).sum() / 1024 / 1024
        MAX_DISPLAY_SIZE_MB = 200  # 200MB 이상이면 일부만 표시
        
        if result_memory_mb > MAX_DISPLAY_SIZE_MB:
            st.warning(
                f"⚠️ 결과 크기가 {result_memory_mb:.1f}MB로 큽니다. "
                f"화면에는 처음 100,000행만 표시되며, 전체 데이터는 CSV 다운로드를 이용해주세요."
            )
            # 처음 100,000행만 표시
            display_result = result.head(100000)
            st.dataframe(display_result, use_container_width=True, hide_index=True)
            st.info(f"전체 {len(result):,}행 중 처음 100,000행만 표시됩니다.")
        else:
            st.dataframe(result, use_container_width=True, hide_index=True)

        csv = result.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="CSV 다운로드 (전체 데이터)",
            data=csv,
            file_name="general_ledger_filtered.csv",
            mime="text/csv",
            key="csv_download_query",  # 고유 키로 변경하여 다운로드 버튼이 결과를 사라지게 하지 않도록
        )
    elif "query_result" in st.session_state and st.session_state["query_result"] is None:
        # 빈 결과 메시지 표시
        info = st.session_state.get("query_result_info", "")
        if info:
            st.warning(info)
    elif not run:
        st.info("좌측 필터를 설정하고 '실행 (Step1→2→3)'을 눌러주세요.")
