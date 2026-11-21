"""저장한 LightGBM 모델로 거래 위험도를 계산한다."""

import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Literal

import lightgbm as lgb
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from fds_agent.core.config import get_settings


class TransactionFeatures(BaseModel):
    """거래 입력과 거래 발생 전에 계산한 계좌 이력을 검증한다."""

    model_config = ConfigDict(extra="forbid")

    step: int = Field(ge=0)
    type: Literal["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
    amount: float = Field(ge=0, allow_inf_nan=False)
    oldbalanceOrg: float = Field(ge=0, allow_inf_nan=False)
    oldbalanceDest: float = Field(ge=0, allow_inf_nan=False)
    send_prior_count: int = Field(default=0, ge=0)
    send_prior_amount_sum: float = Field(default=0, ge=0, allow_inf_nan=False)
    send_prior_amount_mean: float = Field(default=0, ge=0, allow_inf_nan=False)
    send_prior_active_steps: int = Field(default=0, ge=0)
    send_step_gap: int = Field(default=-1, ge=-1)
    receive_prior_count: int = Field(default=0, ge=0)
    receive_prior_amount_sum: float = Field(default=0, ge=0, allow_inf_nan=False)
    receive_prior_amount_mean: float = Field(default=0, ge=0, allow_inf_nan=False)
    receive_prior_active_steps: int = Field(default=0, ge=0)
    receive_step_gap: int = Field(default=-1, ge=-1)

    @model_validator(mode="after")
    def validate_history(self) -> "TransactionFeatures":
        """거래 이력 통계의 건수와 금액 관계를 검증한다."""
        for role in ("send", "receive"):
            count = getattr(self, f"{role}_prior_count")
            total = getattr(self, f"{role}_prior_amount_sum")
            mean = getattr(self, f"{role}_prior_amount_mean")
            active = getattr(self, f"{role}_prior_active_steps")
            gap = getattr(self, f"{role}_step_gap")
            if active > count or (count == 0 and (total != 0 or mean != 0 or gap != -1)):
                raise ValueError(f"{role} 과거 이력 통계가 서로 일치하지 않는다.")
            if count > 0 and (active == 0 or gap < 1 or gap > self.step):
                raise ValueError(f"{role} 과거 이력은 현재 step보다 이전이어야 한다.")
        return self


class Prediction(BaseModel):
    """사기 위험 점수와 고정 임계값 판단을 반환한다."""

    risk_score: float
    threshold: float
    is_fraud: bool
    model_run_id: str


class FraudInference:
    """모델 manifest, 특징 순서, 범주와 임계값을 일관되게 적용한다."""

    def __init__(self, model_root: Path, run_id: str) -> None:
        self.model_dir = model_root / run_id
        self.run_id = run_id
        self.manifest = json.loads((self.model_dir / "manifest.json").read_text())
        self.selection = json.loads((self.model_dir / "frozen_selection.json").read_text())
        self.model_name = self.selection["selected"]
        selected = self.selection["candidates"][self.model_name]
        self.features = selected["features"]
        self.threshold = float(selected["threshold"])
        model_path = self.model_dir / f"{self.model_name}.txt"
        expected_hash = selected["sha256"]
        actual_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError("모델 파일 해시가 manifest와 일치하지 않는다.")
        self.model = lgb.Booster(model_file=str(model_path))
        if self.model.feature_name() != self.features:
            raise ValueError("모델 특징 순서가 manifest와 일치하지 않는다.")
        self.categories = self.selection["categories"]

    def predict(self, transaction: TransactionFeatures) -> Prediction:
        """거래 전 잔액과 과거 이력으로 위험 점수와 판단을 계산한다."""
        values = transaction.model_dump()
        values.update(
            amount_log1p=math.log1p(transaction.amount),
            oldbalanceOrg_log1p=math.log1p(transaction.oldbalanceOrg),
            oldbalanceDest_log1p=math.log1p(transaction.oldbalanceDest),
            amount_to_origin_balance=transaction.amount / (transaction.oldbalanceOrg + 1),
            origin_balance_minus_amount=transaction.oldbalanceOrg - transaction.amount,
            origin_balance_equals_amount=int(transaction.oldbalanceOrg == transaction.amount),
            origin_balance_zero=int(transaction.oldbalanceOrg == 0),
            destination_balance_zero=int(transaction.oldbalanceDest == 0),
            amount_to_destination_balance=transaction.amount / (transaction.oldbalanceDest + 1),
            amount_to_receive_history=transaction.amount
            / (transaction.receive_prior_amount_mean + 1),
        )
        if values["type"] not in self.categories:
            raise ValueError("저장 모델에서 지원하지 않는 거래 유형이다.")
        frame = pd.DataFrame([values], columns=self.features)
        frame["type"] = pd.Categorical(frame["type"], categories=self.categories)
        score = float(self.model.predict(frame)[0])
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("모델이 유효하지 않은 위험 점수를 반환한다.")
        return Prediction(
            risk_score=score,
            threshold=self.threshold,
            is_fraud=score >= self.threshold,
            model_run_id=self.run_id,
        )

    def predict_batch(self, transactions: list[TransactionFeatures]) -> list[Prediction]:
        """검증한 거래 묶음을 한 번에 점수화한다."""
        if not transactions:
            return []
        frame = pd.DataFrame([item.model_dump() for item in transactions])
        if not frame["type"].isin(self.categories).all():
            raise ValueError("저장 모델에서 지원하지 않는 거래 유형을 포함한다.")
        for column in ["amount", "oldbalanceOrg", "oldbalanceDest"]:
            frame[f"{column}_log1p"] = np.log1p(frame[column])
        frame["amount_to_origin_balance"] = frame.amount / (frame.oldbalanceOrg + 1)
        frame["origin_balance_minus_amount"] = frame.oldbalanceOrg - frame.amount
        frame["origin_balance_equals_amount"] = (frame.oldbalanceOrg == frame.amount).astype(int)
        frame["origin_balance_zero"] = (frame.oldbalanceOrg == 0).astype(int)
        frame["destination_balance_zero"] = (frame.oldbalanceDest == 0).astype(int)
        frame["amount_to_destination_balance"] = frame.amount / (frame.oldbalanceDest + 1)
        frame["amount_to_receive_history"] = frame.amount / (frame.receive_prior_amount_mean + 1)
        frame["type"] = pd.Categorical(frame["type"], categories=self.categories)
        scores = self.model.predict(frame[self.features], num_threads=4)
        if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
            raise ValueError("모델이 유효하지 않은 위험 점수를 반환한다.")
        return [
            Prediction(
                risk_score=float(score),
                threshold=self.threshold,
                is_fraud=bool(score >= self.threshold),
                model_run_id=self.run_id,
            )
            for score in scores
        ]


@lru_cache(maxsize=4)
def get_inference() -> FraudInference:
    """설정한 실행 ID의 저장 모델을 한 번 불러온다."""
    settings = get_settings()
    model_root = Path(__file__).resolve().parents[3] / "artifacts" / "models"
    return FraudInference(model_root, settings.model_run_id)
