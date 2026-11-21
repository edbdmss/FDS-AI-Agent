"""Supabase PostgreSQL에 거래와 예측을 원자적으로 저장한다."""

from functools import lru_cache
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from fds_agent.core.config import get_settings


@lru_cache(maxsize=1)
def get_engine():
    """TLS와 작은 연결 풀을 적용하고 서버 비밀값을 로그에 노출하지 않는다."""
    secret = get_settings().database_url
    if secret is None:
        raise RuntimeError("FDS_DATABASE_URL을 설정한다.")
    url = make_url(secret.get_secret_value()).set(drivername="postgresql+psycopg")
    return create_engine(
        url,
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"sslmode": "require", "connect_timeout": 10, "prepare_threshold": None},
    )


def save_prediction(transaction, prediction):
    """한 트랜잭션 안에서 입력과 판단을 함께 기록한다."""
    import json

    transaction_id = str(uuid4())
    with get_engine().begin() as connection:
        connection.execute(
            text(
                "INSERT INTO fds.transactions (id, step, transaction_type, features) "
                "VALUES (:id, :step, :kind, CAST(:features AS jsonb))"
            ),
            {
                "id": transaction_id,
                "step": transaction.step,
                "kind": transaction.type,
                "features": json.dumps(transaction.model_dump()),
            },
        )
        connection.execute(
            text(
                "INSERT INTO fds.predictions "
                "(transaction_id, model_run_id, risk_score, threshold, is_fraud) "
                "VALUES (:id, :model, :score, :threshold, :fraud)"
            ),
            {
                "id": transaction_id,
                "model": prediction.model_run_id,
                "score": prediction.risk_score,
                "threshold": prediction.threshold,
                "fraud": prediction.is_fraud,
            },
        )
    return transaction_id
