"""조사 그래프의 시간 경계와 근거·분기를 검증한다."""

import pytest

from fds_agent.agent.explanation import evidence_payload, explain_report
from fds_agent.agent.investigation import build_graph


@pytest.fixture(autouse=True)
def disable_live_api(monkeypatch):
    from fds_agent.core.config import Settings

    monkeypatch.setattr(
        "fds_agent.agent.explanation.get_settings",
        lambda: Settings(_env_file=None, groq_api_key=None),
    )


def target():
    return dict(
        id="target",
        step=12,
        name_orig="a",
        name_dest="b",
        features={"amount": 100, "oldbalanceOrg": 100},
        risk_score=0.9,
        threshold=0.2,
        is_fraud=True,
        model_run_id="test",
    )


def test_report_cites_only_past_evidence():
    past = dict(id="past", step=11, name_orig="c", name_dest="a", amount=50)
    result = build_graph(lambda _: (target(), [past])).invoke({"transaction_id": "target"})
    report = result["report"]
    assert report["status"] == "review_required"
    assert report["findings"][-1]["evidence_ids"] == ["past"]
    assert report["trace"] == [
        "collect_evidence", "analyze_evidence", "compose_report",
        "generate_explanation", "validate_explanation",
    ]
    assert report["explanation_status"] == "not_configured"


@pytest.mark.parametrize("step", [12, 13])
def test_same_or_future_step_is_rejected(step):
    graph = build_graph(lambda _: (target(), [{"step": step}]))
    with pytest.raises(ValueError):
        graph.invoke({"transaction_id": "target"})


def test_missing_accounts_take_insufficient_branch():
    item = target()
    item["name_orig"] = None
    report = build_graph(lambda _: (item, [])).invoke({"transaction_id": "target"})["report"]
    assert report["status"] == "insufficient_context"
    assert report["findings"] == []


def base_report():
    return build_graph(lambda _: (target(), [])).invoke({"transaction_id": "target"})["report"]


def valid_output(report):
    return {"claims": [
        {"finding_code": f["code"], "explanation": f["description"],
         "evidence_ids": f["evidence_ids"]} for f in report["findings"]
    ]}


def test_generated_explanation_preserves_prediction():
    original = base_report()
    result = explain_report(original, valid_output)
    assert result["generation_mode"] == "llm_assisted"
    for key in ("risk_score", "threshold", "status", "findings", "model_run_id"):
        assert result[key] == original[key]
    assert original["explanation"] is None
    assert set(evidence_payload(original)) == {"status", "risk_score", "threshold", "findings"}


@pytest.mark.parametrize("failure", ["unknown_id", "missing", "duplicate", "extra", "style"])
def test_invalid_explanation_falls_back(failure):
    original = base_report()
    output = valid_output(original)
    if failure == "unknown_id":
        output["claims"][0]["evidence_ids"] = ["fabricated"]
    elif failure == "missing":
        output["claims"].pop()
    elif failure == "duplicate":
        output["claims"].append(output["claims"][0])
    elif failure == "extra":
        output["risk_score"] = 1
    else:
        output["claims"][0]["explanation"] = "사기입니다."
    result = explain_report(original, lambda _: output)
    assert result["explanation_status"] == "invalid_output"
    assert result["explanation"] is None
    assert result["risk_score"] == original["risk_score"]


def test_timeout_falls_back():
    import httpx

    def timeout(_):
        raise httpx.ReadTimeout("private provider detail")

    result = explain_report(base_report(), timeout)
    assert result["explanation_status"] == "provider_error"
    assert "private provider detail" not in str(result)


@pytest.mark.parametrize("status", [200, 429, 500])
def test_groq_transport_and_payload(monkeypatch, status):
    import json

    import httpx

    from fds_agent.core.config import Settings

    original = base_report()
    original["history"] = [{"name_orig": "PRIVATE_ACCOUNT"}]
    monkeypatch.setattr(
        "fds_agent.agent.explanation.get_settings",
        lambda: Settings(_env_file=None, groq_api_key="test-key"),
    )

    def handler(request):
        body = json.loads(request.content)
        assert str(request.url) == "https://api.groq.com/openai/v1/chat/completions"
        assert body["model"] == "openai/gpt-oss-120b"
        assert body["response_format"]["json_schema"]["strict"] is True
        assert "PRIVATE_ACCOUNT" not in request.content.decode()
        assert json.loads(body["messages"][1]["content"]) == evidence_payload(original)
        return httpx.Response(status, json={"choices": [{
            "finish_reason": "stop",
            "message": {"content": json.dumps(valid_output(original))},
        }]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    monkeypatch.setattr("fds_agent.agent.explanation.httpx.Client", lambda **_: client)
    result = explain_report(original)
    assert result["explanation_status"] == ("generated" if status == 200 else "provider_error")
