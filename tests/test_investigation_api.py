"""조사 보고서 저장·조회와 오류 응답을 검증한다."""

from uuid import uuid4

from fastapi.testclient import TestClient

from fds_agent.api import main


def test_investigation_saves_and_returns_id(monkeypatch):
    report = {"transaction_id": str(uuid4()), "risk_score": 0.2}
    stored = {**report, "report_id": str(uuid4())}
    monkeypatch.setattr(main, "investigate", lambda _: report)

    def save(value):
        assert value == report
        return stored

    monkeypatch.setattr(main, "save_report", save)
    response = TestClient(main.app).post(
        f"/v1/transactions/{report['transaction_id']}/investigate"
    )
    assert response.status_code == 200
    assert response.json() == stored


def test_report_lookup_never_invokes_llm(monkeypatch):
    def unexpected(_):
        raise AssertionError("조회 중 모델을 호출하지 않도록 검증한다.")

    monkeypatch.setattr(main, "investigate", unexpected)
    monkeypatch.setattr(main, "get_report", lambda _: {"report_id": "saved"})
    response = TestClient(main.app).get(f"/v1/investigations/{uuid4()}")
    assert response.status_code == 200
    assert response.json()["report_id"] == "saved"


def test_save_failure_does_not_return_success(monkeypatch):
    monkeypatch.setattr(main, "investigate", lambda _: {})

    def fail(_):
        raise RuntimeError("private connection details")

    monkeypatch.setattr(main, "save_report", fail)
    response = TestClient(main.app).post(f"/v1/transactions/{uuid4()}/investigate")
    assert response.status_code == 503
    assert "private" not in response.text


def test_missing_report_returns_404(monkeypatch):
    def missing(_):
        raise LookupError()

    monkeypatch.setattr(main, "get_report", missing)
    assert TestClient(main.app).get(f"/v1/investigations/{uuid4()}").status_code == 404
