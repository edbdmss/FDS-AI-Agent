from uuid import UUID

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text

from fds_agent.agent.chat import ChatRequest, chat
from fds_agent.agent.investigation import investigate
from fds_agent.core.config import get_settings
from fds_agent.db.investigations import get_report, save_report
from fds_agent.db.storage import get_engine, save_prediction
from fds_agent.db.transactions import (
    IncomingTransaction,
    TransactionConflict,
    TransactionResult,
    score_transaction,
)
from fds_agent.models.inference import Prediction, TransactionFeatures, get_inference

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")


@app.post("/v1/chat", tags=["chat"])
def conversational_agent(request: ChatRequest) -> dict:
    """자연어 요청으로 거래 조회와 조사 도구를 실행한다."""
    return chat(request)


@app.post("/v1/transactions/{transaction_id}/investigate", tags=["investigations"])
def investigate_transaction(transaction_id: UUID) -> dict:
    """LangGraph를 실행하고 저장한 조사 보고서를 반환한다."""
    try:
        report = investigate(transaction_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="조사할 거래를 찾을 수 없다.") from None
    except Exception:
        raise HTTPException(status_code=503, detail="거래 조사 실행에 실패한다.") from None
    try:
        return save_report(report)
    except Exception:
        raise HTTPException(status_code=503, detail="조사 보고서 저장에 실패한다.") from None


@app.get("/v1/investigations/{report_id}", tags=["investigations"])
def investigation_detail(report_id: UUID) -> dict:
    """저장 보고서를 모델 재호출 없이 조회한다."""
    try:
        return get_report(report_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="조사 보고서를 찾을 수 없다.") from None
    except Exception:
        raise HTTPException(status_code=503, detail="조사 보고서 조회에 실패한다.") from None


@app.get("/v1/transactions", tags=["transactions"])
def list_transactions(
    account: str | None = Query(default=None, min_length=1, max_length=128),
    before_step: int | None = Query(default=None, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    """계좌와 시점 조건으로 저장 거래 및 예측을 조회한다."""
    query = (
        "SELECT t.id AS transaction_id, t.step, t.transaction_type, t.name_orig, t.name_dest, "
        "p.risk_score, p.threshold, p.is_fraud, p.model_run_id "
        "FROM fds.transactions t JOIN fds.predictions p ON p.transaction_id=t.id WHERE true "
    )
    params = {"limit": limit}
    if account is not None:
        query += "AND (t.name_orig=:account OR t.name_dest=:account) "
        params["account"] = account
    if before_step is not None:
        query += "AND t.step < :before_step "
        params["before_step"] = before_step
    query += "ORDER BY t.step DESC, t.id LIMIT :limit"
    try:
        with get_engine().connect() as connection:
            return [dict(row) for row in connection.execute(text(query), params).mappings()]
    except Exception:
        raise HTTPException(status_code=503, detail="거래 목록 조회에 실패한다.") from None


@app.get("/v1/transactions/{transaction_id}", tags=["transactions"])
def transaction_detail(transaction_id: UUID) -> dict:
    """저장 당시 사용한 특징과 예측 결과를 거래 ID로 조회한다."""
    try:
        with get_engine().connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT t.id AS transaction_id, t.step, "
                        "t.name_orig, t.name_dest, t.features, "
                        "t.created_at, p.risk_score, p.threshold, p.is_fraud, p.model_run_id "
                        "FROM fds.transactions t JOIN fds.predictions p ON p.transaction_id=t.id "
                        "WHERE t.id=:id"
                    ),
                    {"id": str(transaction_id)},
                )
                .mappings()
                .first()
            )
    except Exception:
        raise HTTPException(status_code=503, detail="거래 상세 조회에 실패한다.") from None
    if row is None:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없다.")
    return dict(row)


@app.post("/v1/transactions/score", response_model=TransactionResult, tags=["fraud-detection"])
def score_with_history(transaction: IncomingTransaction) -> TransactionResult:
    """DB 계좌 이력을 자동으로 연결하고 거래 ID별 예측 결과를 저장한다."""
    try:
        return score_transaction(transaction)
    except TransactionConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    except Exception:
        raise HTTPException(status_code=503, detail="거래 처리에 실패한다.") from None


class StoredPrediction(Prediction):
    """저장한 거래 ID와 모델 판단을 반환한다."""

    transaction_id: str


@app.post("/v1/predict-and-save", response_model=StoredPrediction, tags=["fraud-detection"])
def predict_and_save(transaction: TransactionFeatures) -> StoredPrediction:
    """거래와 예측을 Supabase에 저장하고 식별자를 반환한다."""
    result = predict(transaction)
    try:
        transaction_id = save_prediction(transaction, result)
    except Exception:
        # 접속 정보가 포함될 수 있는 DB 예외는 응답에서 숨김 처리한다.
        raise HTTPException(
            status_code=503, detail="DB 저장에 실패한다. 연결 설정을 확인한다."
        ) from None
    return StoredPrediction(transaction_id=transaction_id, **result.model_dump())


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """프로세스 상태만 반환하며 DB·모델 준비 여부는 보장하지 않는다."""
    return {"status": "ok", "environment": settings.environment}


@app.post("/v1/predict", response_model=Prediction, tags=["fraud-detection"])
def predict(transaction: TransactionFeatures) -> Prediction:
    """거래 특징을 받아 위험 점수와 사기 여부를 계산한다."""
    try:
        return get_inference().predict(transaction)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail="저장 모델을 찾지 못한다. PaySim 데이터와 모델 산출물을 준비한다.",
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
