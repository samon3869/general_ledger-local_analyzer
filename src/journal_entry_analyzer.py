from __future__ import annotations

from typing import Literal

import pandas as pd


class JournalEntryAnalyzer:
    """
    조건 필터링 → 전표 확장 → 거래유형별 대표 표본 추출을 수행하는 분석 클래스.
    데이터는 이미 transaction_hash 컬럼을 포함해야 한다.

    필수 컬럼(기본값 기준): jeonpyo_id, account_code, amount, description, transaction_hash
    """

    def __init__(
        self,
        data: pd.DataFrame,
        je_id_col: str = "jeonpyo_id",
        hash_col: str = "transaction_hash",
    ):
        missing = {je_id_col, hash_col} - set(data.columns)
        if missing:
            raise ValueError(f"필수 컬럼이 없습니다: {missing}")
        self.data = data
        self.je_id_col = je_id_col
        self.hash_col = hash_col

    def filter_by_condition(
        self,
        condition: str | None,
        engine: Literal["pandas"] = "pandas",
    ) -> pd.DataFrame:
        """
        Step 1: SQL 스타일 조건문으로 1차 필터링. 조건이 없으면 원본 반환.

        Parameters
        ----------
        condition: str | None
            예: "amount > 10000000"
        engine: {"pandas"}, default "pandas"
            현재 구현은 pandas.query 기반.
        """
        if not condition or not condition.strip():
            return self.data.copy()

        normalized = (
            condition.replace(" AND ", " and ")
            .replace(" OR ", " or ")
        )
        try:
            return self.data.query(normalized, engine="python").copy()
        except Exception as exc:
            raise ValueError(f"조건문 오류: {exc}") from exc

    def expand_full_entry(
        self,
        filtered: pd.DataFrame,
        expand_full_entry: bool,
    ) -> pd.DataFrame:
        """
        Step 2: expand_full_entry=True이면 조건에 걸린 jeonpyo_id의 모든 라인을 반환.
        """
        if not expand_full_entry or filtered.empty:
            return filtered.copy()

        je_ids = filtered[self.je_id_col].dropna().unique()
        if len(je_ids) == 0:
            return filtered.copy()

        return self.data[self.data[self.je_id_col].isin(je_ids)].copy()

    def unique_representative(
        self,
        df: pd.DataFrame,
        unique_pattern_only: bool,
    ) -> pd.DataFrame:
        """
        Step 3: transaction_hash 별로 가장 먼저 등장하는 jeonpyo_id 하나만 남기고,
        그 전표의 모든 라인을 반환.
        """
        if not unique_pattern_only or df.empty:
            return df.copy()

        has_hash = df[df[self.hash_col].notna()].copy()
        if has_hash.empty:
            return df.copy()

        first_ids = (
            has_hash[[self.hash_col, self.je_id_col]]
            .drop_duplicates(subset=[self.hash_col], keep="first")
        )
        rep_ids = first_ids[self.je_id_col].unique()
        reps = df[df[self.je_id_col].isin(rep_ids)].copy()

        no_hash = df[df[self.hash_col].isna()]
        if not no_hash.empty:
            reps = pd.concat([reps, no_hash], ignore_index=True)

        return reps

    def run(
        self,
        condition: str | None,
        expand_full_entry: bool = True,
        unique_pattern_only: bool = True,
    ) -> pd.DataFrame:
        """
        Step1 → Step2 → Step3 순차 실행.
        """
        step1 = self.filter_by_condition(condition)
        step2 = self.expand_full_entry(step1, expand_full_entry)
        step3 = self.unique_representative(step2, unique_pattern_only)
        return step3
