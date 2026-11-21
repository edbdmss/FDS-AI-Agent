"""저장 모델 추론 API의 입력 검증과 응답 계약을 확인한다."""

from fastapi.testclient import TestClient

from fds_agent.api.main import app
from fds_agent.models.inference import get_inference


def test_prediction_returns_risk_and_fraud_decision() -> None:
    """검증된 거래 입력에서 위험 점수와 임계값 판단을 반환한다."""
    get_inference.cache_clear()
    client = TestClient(app)
    response = client.post(
        "/v1/predict",
        json={
            "step": 355,
            "type": "TRANSFER",
            "amount": 500.0,
            "oldbalanceOrg": 500.0,
            "oldbalanceDest": 0.0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["risk_score"] <= 1
    assert body["is_fraud"] is (body["risk_score"] >= body["threshold"])
    assert body["model_run_id"] == "20261119T073653Z-1d0e70df"


def test_prediction_rejects_inconsistent_history() -> None:
    """거래 이력 통계가 서로 맞지 않으면 요청을 거부한다."""
    client = TestClient(app)
    response = client.post(
        "/v1/predict",
        json={
            "step": 355,
            "type": "TRANSFER",
            "amount": 500.0,
            "oldbalanceOrg": 500.0,
            "oldbalanceDest": 0.0,
            "send_prior_count": 0,
            "send_prior_amount_sum": 100.0,
        },
    )

    assert response.status_code == 422
