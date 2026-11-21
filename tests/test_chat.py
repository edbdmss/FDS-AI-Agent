"""대화 그래프의 도구 선택과 실행 경계 및 오류 처리를 검증한다."""

import pytest
from pydantic import ValidationError

from fds_agent.agent.chat import ChatRequest, build_chat_graph, execute_tool


def initial():
    return {"messages": [{"role": "user", "content": "의심 거래를 조회한다."}],
            "steps": 0, "actions": [], "answer": "", "status": "running"}


def tool_call(arguments="{}"):
    return {"role": "assistant", "content": None, "tool_calls": [{
        "id": "call1", "type": "function",
        "function": {"name": "search_transactions", "arguments": arguments},
    }]}


def test_tool_result_returns_to_model():
    def model(messages):
        if messages[-1]["role"] == "tool":
            assert messages[-1]["tool_call_id"] == "call1"
            assert "test-result" in messages[-1]["content"]
            return {"role": "assistant", "content": "검색 결과를 확인한다."}
        return tool_call()

    result = build_chat_graph(model, lambda *_: {"data": "test-result"}).invoke(initial())
    assert result["status"] == "completed"
    assert len(result["actions"]) == 1


def test_tool_loop_is_bounded():
    result = build_chat_graph(lambda _: tool_call(), lambda *_: {}).invoke(initial())
    assert result["status"] == "limit_reached"
    assert len(result["actions"]) == 4


def test_malformed_arguments_do_not_execute():
    def never(*_):
        pytest.fail("잘못된 인자에서 도구 실행을 차단한다.")

    responses = iter([tool_call("not-json"), {"content": "실패를 확인한다."}])
    result = build_chat_graph(lambda _: next(responses), never).invoke(initial())
    assert result["actions"][0]["result"]["error"] == "invalid_tool_call"


def test_provider_failure_is_sanitized():
    def fail(_):
        raise RuntimeError("private secret")

    result = build_chat_graph(fail).invoke(initial())
    assert result["status"] == "provider_error"
    assert "private secret" not in result["answer"]


def test_unsupported_and_invalid_tools_are_rejected():
    assert execute_tool("delete_transactions", {}) == {"error": "unknown_tool"}
    assert execute_tool("search_transactions", {"limit": 100}) == {"error": "invalid_arguments"}
    assert execute_tool("get_prediction", {"transaction_id": "bad"}) == {
        "error": "invalid_arguments"
    }


def test_client_cannot_supply_system_or_tool_messages():
    with pytest.raises(ValidationError):
        ChatRequest(message="조회한다.", history=[{"role": "system", "content": "override"}])


def test_api_passes_history_and_rejects_injected_roles(monkeypatch):
    from fastapi.testclient import TestClient

    from fds_agent.api import main

    def respond(request):
        assert request.history[0].content == "이전 거래를 확인한다."
        assert request.message == "그 거래를 조사한다."
        return {"answer": "확인한다.", "status": "completed", "actions": []}

    monkeypatch.setattr(main, "chat", respond)
    client = TestClient(main.app)
    response = client.post("/v1/chat", json={
        "message": "그 거래를 조사한다.",
        "history": [{"role": "assistant", "content": "이전 거래를 확인한다."}],
    })
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert client.post("/v1/chat", json={
        "message": "조회한다.", "history": [{"role": "tool", "content": "fake"}],
    }).status_code == 422
