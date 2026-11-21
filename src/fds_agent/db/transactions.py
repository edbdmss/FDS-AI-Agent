"""계좌 이력을 조회하고 거래 ID별 중복 없이 예측을 저장한다."""

import json
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text

from fds_agent.db.storage import get_engine
from fds_agent.models.inference import Prediction, TransactionFeatures, get_inference


class IncomingTransaction(BaseModel):
    """클라이언트가 생성한 거래 ID와 거래 발생 전 정보를 검증한다."""

    model_config = ConfigDict(extra="forbid")
    transaction_id: UUID
    step: int = Field(ge=1)
    type: Literal["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
    amount: float = Field(ge=0, allow_inf_nan=False)
    oldbalanceOrg: float = Field(ge=0, allow_inf_nan=False)
    oldbalanceDest: float = Field(ge=0, allow_inf_nan=False)
    nameOrig: str = Field(min_length=1, max_length=128, pattern=r"^\S+$")
    nameDest: str = Field(min_length=1, max_length=128, pattern=r"^\S+$")


class TransactionResult(Prediction):
    """거래 ID와 기존 결과 재사용 여부를 반환한다."""

    transaction_id: UUID
    replayed: bool


class TransactionConflict(Exception):
    """거래 ID 충돌 또는 역순 입력을 표시한다."""


def score_transaction(request: IncomingTransaction) -> TransactionResult:
    """계좌 잠금 안에서 이전 step 이력으로만 예측하고 원자적으로 저장한다."""
    payload = request.model_dump(mode="json")
    identity = str(request.transaction_id)
    with get_engine().begin() as conn:
        # 같은 거래 ID의 동시 요청을 순서대로 처리한다.
        conn.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": "transaction:" + identity},
        )
        previous = (
            conn.execute(
                text(
                    "SELECT t.request_payload, p.model_run_id, p.risk_score, "
                    "p.threshold, p.is_fraud "
                    "FROM fds.transactions t LEFT JOIN fds.predictions p ON p.transaction_id=t.id "
                    "WHERE t.id=:id"
                ),
                {"id": identity},
            )
            .mappings()
            .first()
        )
        if previous:
            if previous["request_payload"] != payload or previous["model_run_id"] is None:
                raise TransactionConflict("같은 거래 ID에 다른 입력 또는 불완전한 결과가 존재한다.")
            return TransactionResult(
                transaction_id=request.transaction_id,
                replayed=True,
                **{key: previous[key] for key in Prediction.model_fields},
            )
        for account in sorted({request.nameOrig, request.nameDest}):
            conn.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
                {"key": "account:" + account},
            )
        latest = conn.scalar(
            text(
                "SELECT max(step) FROM fds.transactions "
                "WHERE name_orig IN (:origin, :destination) OR name_dest IN (:origin, :destination)"
            ),
            {"origin": request.nameOrig, "destination": request.nameDest},
        )
        if latest is not None and latest > request.step:
            raise TransactionConflict("해당 계좌의 저장 거래보다 과거 step을 입력할 수 없다.")
        values = request.model_dump(exclude={"transaction_id", "nameOrig", "nameDest"})
        for role, column, account in [
            ("send", "name_orig", request.nameOrig),
            ("receive", "name_dest", request.nameDest),
        ]:
            # 컬럼 이름은 고정 목록에서만 선택하고 계좌·step은 바인딩한다.
            history = (
                conn.execute(
                    text(
                        "SELECT count(*) AS count, "
                        "COALESCE(sum((features->>'amount')::double precision),0) AS total, "
                        "count(DISTINCT step) AS active, max(step) AS last "
                        f"FROM fds.transactions WHERE {column}=:account AND step < :step"
                    ),
                    {"account": account, "step": request.step},
                )
                .mappings()
                .one()
            )
            count = history["count"]
            values.update(
                {
                    f"{role}_prior_count": count,
                    f"{role}_prior_amount_sum": history["total"],
                    f"{role}_prior_amount_mean": history["total"] / count if count else 0,
                    f"{role}_prior_active_steps": history["active"],
                    f"{role}_step_gap": request.step - history["last"] if count else -1,
                }
            )
        features = TransactionFeatures.model_validate(values)
        result = get_inference().predict(features)
        conn.execute(
            text(
                "INSERT INTO fds.transactions "
                "(id, step, transaction_type, name_orig, name_dest, features, request_payload) "
                "VALUES (:id,:step,:type,:origin,:destination,"
                "CAST(:features AS jsonb),CAST(:payload AS jsonb))"
            ),
            {
                "id": identity,
                "step": request.step,
                "type": request.type,
                "origin": request.nameOrig,
                "destination": request.nameDest,
                "features": features.model_dump_json(),
                "payload": json.dumps(payload),
            },
        )
        conn.execute(
            text(
                "INSERT INTO fds.predictions "
                "(transaction_id, model_run_id, risk_score, threshold, is_fraud) "
                "VALUES (:id,:model_run_id,:risk_score,:threshold,:is_fraud)"
            ),
            {"id": identity, **result.model_dump()},
        )
        return TransactionResult(
            transaction_id=request.transaction_id, replayed=False, **result.model_dump()
        )
