from __future__ import annotations

import streamlit as st

from db_engine import GLEngine


def build_aggregation_query(
    columns: list[str],
    group_by_cols: list[str],
    agg_functions: dict[str, list[str]],
    condition: str | None,
    having_condition: str | None,
) -> str:
    """
    집계 쿼리 생성.
    - group_by_cols: 그룹핑할 컬럼들
    - agg_functions: {컬럼명: [집계함수들]} 형태 (예: {"차변금액": ["SUM", "COUNT"]})
    - condition: WHERE 절 조건 (집계 전 필터링)
    - having_condition: HAVING 절 조건 (집계 후 필터링)
    """
    base_condition = condition.strip() if condition and condition.strip() else "1=1"
    
    # GROUP BY 절 구성
    group_by_clause = ", ".join(f'"{col}"' for col in group_by_cols) if group_by_cols else ""
    
    # SELECT 절 구성
    select_parts = []
    # 그룹핑 컬럼들
    if group_by_cols:
        select_parts.extend(f'"{col}"' for col in group_by_cols)
    
    # 집계 함수들
    for col, funcs in agg_functions.items():
        for func in funcs:
            func_upper = func.upper()
            # 숫자형 집계 함수는 TRY_CAST를 사용하여 안전하게 변환 (변환 실패 시 NULL 반환)
            # COUNT는 타입에 관계없이 사용 가능하므로 CAST 불필요
            if func_upper == "SUM":
                # VARCHAR나 다른 타입도 DOUBLE로 변환하여 SUM 가능하도록
                select_parts.append(f'SUM(TRY_CAST("{col}" AS DOUBLE)) AS "{col}_SUM"')
            elif func_upper == "COUNT":
                select_parts.append(f'COUNT("{col}") AS "{col}_COUNT"')
            elif func_upper == "AVG":
                select_parts.append(f'AVG(TRY_CAST("{col}" AS DOUBLE)) AS "{col}_AVG"')
            elif func_upper == "MIN":
                # MIN/MAX는 문자열도 가능하지만, 숫자형으로 변환하여 일관성 유지
                select_parts.append(f'MIN(TRY_CAST("{col}" AS DOUBLE)) AS "{col}_MIN"')
            elif func_upper == "MAX":
                select_parts.append(f'MAX(TRY_CAST("{col}" AS DOUBLE)) AS "{col}_MAX"')
    
    select_clause = ", ".join(select_parts)
    
    # HAVING 절 구성
    having_clause = ""
    if having_condition and having_condition.strip():
        having_clause = f"\n        HAVING {having_condition.strip()}"
    
    if group_by_clause:
        return f"""
        SELECT {select_clause}
        FROM general_ledger
        WHERE {base_condition}
        GROUP BY {group_by_clause}{having_clause}
        ORDER BY {group_by_clause}
        """
    else:
        # 그룹핑이 없으면 전체 집계 (HAVING은 GROUP BY와 함께 사용)
        if having_clause:
            # HAVING 절이 있으면 GROUP BY가 필요하지만, 전체 집계이므로 빈 GROUP BY 사용 불가
            # 대신 WHERE 절에 집계 함수를 사용할 수 없으므로 경고
            return f"""
        SELECT {select_clause}
        FROM general_ledger
        WHERE {base_condition}
        """
        else:
            return f"""
        SELECT {select_clause}
        FROM general_ledger
        WHERE {base_condition}
        """


def render_aggregation_tab(engine: GLEngine, columns: list[str]) -> None:
    """집계 데이터 탭 렌더링."""
    st.header("집계 데이터 생성")
    st.markdown("좌측 사이드바에서 집계 설정을 구성한 후 실행 버튼을 눌러주세요.")

    with st.sidebar.expander("📈 집계 데이터 설정", expanded=True):
            st.header("그룹핑 컬럼 선택")
            group_by_cols = st.multiselect(
                "그룹핑할 컬럼을 선택하세요 (복수 선택 가능)",
                options=columns,
                key="group_by_cols",
                help="선택한 컬럼별로 데이터를 그룹핑합니다. 비워두면 전체 집계가 됩니다.",
            )
            
            st.markdown("---")
            st.header("집계 대상 컬럼 선택")
            agg_target_cols = st.multiselect(
                "집계할 컬럼을 선택하세요 (복수 선택 가능)",
                options=columns,
                key="agg_target_cols",
            )
            
            st.markdown("---")
            st.header("집계 함수 선택")
            agg_functions = {}
            if agg_target_cols:
                for col in agg_target_cols:
                    selected_funcs = st.multiselect(
                        f'"{col}"에 적용할 집계 함수',
                        options=["SUM", "COUNT", "AVG", "MIN", "MAX"],
                        key=f"agg_func_{col}",
                    )
                    if selected_funcs:
                        agg_functions[col] = selected_funcs
            
            st.markdown("---")
            st.header("필터 조건 (선택사항)")
            
            st.markdown("**WHERE 절 (집계 전 필터링)**")
            agg_condition = st.text_area(
                "집계 전 필터링할 조건",
                placeholder="예: 회계월 >= 202501 AND 회계월 <= 202512",
                height=80,
                key="agg_condition",
                help="집계하기 전에 원본 데이터를 필터링합니다.",
            )
            # HTML details 태그를 사용하여 접을 수 있는 도움말 생성 (expander 중첩 방지)
            st.markdown(
                """
                <details>
                <summary style="cursor: pointer; color: #1f77b4; font-weight: bold;">📖 WHERE 절 작성 도움말</summary>
                
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
            st.markdown("**HAVING 절 (집계 후 필터링)**")
            having_condition = st.text_area(
                "집계 결과를 필터링할 조건",
                placeholder='예: "차변금액_SUM" > 1000000 OR "차변금액_COUNT" >= 10',
                height=80,
                key="having_condition",
                help="집계 결과에 대해 필터링합니다. 집계 함수 결과 컬럼명을 사용하세요 (예: 차변금액_SUM, 차변금액_COUNT).",
            )
            # HTML details 태그를 사용하여 접을 수 있는 도움말 생성 (expander 중첩 방지)
            st.markdown(
                """
                <details>
                <summary style="cursor: pointer; color: #1f77b4; font-weight: bold;">📖 HAVING 절 작성 도움말</summary>
                
                **집계 결과 컬럼명 형식:**
                - `{원본컬럼명}_{집계함수}` 형식으로 참조
                - 예: `차변금액` 컬럼에 `SUM` 적용 → `차변금액_SUM`
                - 예: `차변금액` 컬럼에 `COUNT` 적용 → `차변금액_COUNT`
                
                **사용 예시:**
                - `"차변금액_SUM" > 1000000` (합계가 100만원 초과인 그룹만)
                - `"차변금액_COUNT" >= 10` (건수가 10건 이상인 그룹만)
                - `"차변금액_SUM" > 1000000 AND "차변금액_AVG" < 500000` (복합 조건)
                - `"차변금액_SUM" > "대변금액_SUM"` (차변 합계가 대변 합계보다 큰 그룹)
                
                **주의사항:**
                - 집계 함수 결과 컬럼명은 반드시 쌍따옴표로 감싸세요
                - HAVING 절은 GROUP BY와 함께 사용됩니다
                </details>
                """,
                unsafe_allow_html=True,
            )
            
            st.markdown("---")
            run_agg = st.button("집계 실행", type="primary", key="run_agg", use_container_width=True)
    
    # 실행 로직은 expander 밖에서 처리 (변수는 session_state에서 가져옴)
    run_agg = st.session_state.get("run_agg", False)
    if run_agg:
        # session_state에서 변수 가져오기
        group_by_cols = st.session_state.get("group_by_cols", [])
        agg_target_cols = st.session_state.get("agg_target_cols", [])
        agg_condition = st.session_state.get("agg_condition", "")
        having_condition = st.session_state.get("having_condition", "")
        
        # 집계 함수 재구성
        agg_functions = {}
        if agg_target_cols:
            for col in agg_target_cols:
                func_key = f"agg_func_{col}"
                selected_funcs = st.session_state.get(func_key, [])
                if selected_funcs:
                    agg_functions[col] = selected_funcs
        
        if not agg_functions:
            st.warning("집계할 컬럼과 집계 함수를 선택해주세요.")
        else:
            try:
                # 그룹핑이 없는데 HAVING 절이 있으면 경고
                if not group_by_cols and having_condition and having_condition.strip():
                    st.warning("HAVING 절은 GROUP BY와 함께 사용해야 합니다. 그룹핑 컬럼을 선택해주세요.")
                else:
                    query = build_aggregation_query(columns, group_by_cols, agg_functions, agg_condition, having_condition)
                    # 쿼리 저장
                    st.session_state["agg_query_executed"] = query
                    with st.spinner("집계 쿼리 실행 중..."):
                        df_agg = engine.run_query(query)
                    
                    if df_agg.empty:
                        st.warning("집계 결과가 없습니다.")
                        st.session_state["agg_result"] = None
                        st.session_state["agg_result_info"] = "집계 결과가 없습니다."
                    else:
                        # 결과 저장
                        st.session_state["agg_result"] = df_agg
                        st.session_state["agg_result_info"] = f"집계 완료: {len(df_agg):,}행"
                        
            except Exception as exc:
                st.error(f"집계 실행 실패: {exc}")
                # 오류 발생 시 기존 결과 초기화
                if "agg_result" in st.session_state:
                    del st.session_state["agg_result"]
                if "agg_result_info" in st.session_state:
                    del st.session_state["agg_result_info"]
                if "agg_query_executed" in st.session_state:
                    del st.session_state["agg_query_executed"]
                with st.expander("오류 상세 정보"):
                    st.exception(exc)
    
    # 저장된 결과가 있으면 표시 (집계 실행 버튼을 누르지 않아도 유지)
    if "agg_result" in st.session_state and st.session_state["agg_result"] is not None:
        df_agg = st.session_state["agg_result"]
        result_info = st.session_state.get("agg_result_info", "")
        
        # 실행된 쿼리 보기 (결과 위에 표시)
        if "agg_query_executed" in st.session_state:
            with st.expander("실행된 쿼리 보기", expanded=False):
                st.code(st.session_state["agg_query_executed"], language="sql")
        
        if result_info:
            st.success(result_info)
        
        # 결과 크기 체크 (메모리 사용량)
        result_memory_mb = df_agg.memory_usage(deep=True).sum() / 1024 / 1024
        MAX_DISPLAY_SIZE_MB = 200  # 200MB 이상이면 일부만 표시
        
        if result_memory_mb > MAX_DISPLAY_SIZE_MB:
            st.warning(
                f"⚠️ 결과 크기가 {result_memory_mb:.1f}MB로 큽니다. "
                f"화면에는 처음 100,000행만 표시되며, 전체 데이터는 CSV 다운로드를 이용해주세요."
            )
            # 처음 100,000행만 표시
            display_result = df_agg.head(100000)
            st.dataframe(display_result, use_container_width=True, hide_index=True)
            st.info(f"전체 {len(df_agg):,}행 중 처음 100,000행만 표시됩니다.")
        else:
            st.dataframe(df_agg, use_container_width=True, hide_index=True)
        
        # CSV 다운로드
        csv_agg = df_agg.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="집계 결과 CSV 다운로드 (전체 데이터)",
            data=csv_agg,
            file_name="general_ledger_aggregated.csv",
            mime="text/csv",
            key="download_agg",
        )
    elif "agg_result" in st.session_state and st.session_state["agg_result"] is None:
        # 빈 결과 메시지 표시
        info = st.session_state.get("agg_result_info", "")
        if info:
            st.warning(info)
    elif not run_agg:
        st.info("집계 설정을 완료한 후 '집계 실행' 버튼을 눌러주세요.")
