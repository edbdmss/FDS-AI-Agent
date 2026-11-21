"""LangGraph로 저장 거래의 과거 근거를 수집하고 조사 보고서를 생성한다."""

from typing import TypedDict
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from sqlalchemy import text

from fds_agent.agent.explanation import explain_report, generate_explanation
from fds_agent.db.storage import get_engine


class InvestigationState(TypedDict, total=False):
    transaction_id: str
    transaction: dict
    history: list[dict]
    findings: list[dict]
    trace: list[str]
    report: dict


def load_evidence(identity: str) -> tuple[dict, list[dict]]:
    """정답 없이 대상 거래와 동일·미래 step을 제외한 계좌 이력을 조회한다."""
    with get_engine().connect() as conn:
        row = (
            conn.execute(
                text(
                    "SELECT t.id, t.step, t.name_orig, t.name_dest, t.features, "
                    "p.risk_score, p.threshold, p.is_fraud, p.model_run_id "
                    "FROM fds.transactions t JOIN fds.predictions p ON p.transaction_id=t.id "
                    "WHERE t.id=:id"
                ),
                {"id": identity},
            )
            .mappings()
            .first()
        )
        if row is None:
            raise LookupError("조사 대상 거래를 찾을 수 없다.")
        target = dict(row)
        target["id"] = str(target["id"])
        history = (
            conn.execute(
                text(
                    "SELECT id, step, name_orig, name_dest, "
                    "features->>'type' AS type, (features->>'amount')::double precision AS amount "
                    "FROM fds.transactions WHERE step < :step AND "
                    "(name_orig IN (:origin,:destination) OR name_dest IN (:origin,:destination)) "
                    "ORDER BY step DESC, id LIMIT 101"
                ),
                {
                    "step": target["step"],
                    "origin": target["name_orig"],
                    "destination": target["name_dest"],
                },
            )
            .mappings()
            .all()
        )
    return target, [{**dict(item), "id": str(item["id"])} for item in history]


def build_graph(loader=load_evidence, generator=generate_explanation):
    """근거 조회·품질 분기·분석·보고서 단계를 연결한다."""

    def collect(state):
        target, history = loader(state["transaction_id"])
        # 외부 도구가 잘못된 시점의 근거를 반환해도 보고서 생성을 중단한다.
        if any(item["step"] >= target["step"] for item in history):
            raise ValueError("현재 또는 미래 step의 이력이 조사 근거에 포함된다.")
        return {"transaction": target, "history": history, "trace": ["collect_evidence"]}

    def analyze(state):
        target = state["transaction"]
        values = target["features"]
        findings = []
        if target["is_fraud"]:
            findings.append(
                dict(
                    code="model_alert",
                    evidence_ids=[target["id"]],
                    description="저장 모델의 위험 점수가 임계값 이상임을 확인한다.",
                )
            )
        if values["amount"] > 0 and values["amount"] == values["oldbalanceOrg"]:
            findings.append(
                dict(
                    code="full_balance_transfer",
                    evidence_ids=[target["id"]],
                    description="거래 금액이 송금자의 거래 전 잔액과 일치함을 확인한다.",
                )
            )
        incoming = [
            item for item in state["history"][:100] if item["name_dest"] == target["name_orig"]
        ]
        if incoming:
            findings.append(
                dict(
                    code="prior_incoming",
                    evidence_ids=[x["id"] for x in incoming],
                    description=f"송금 계좌의 이전 수취 거래 {len(incoming)}건을 확인한다.",
                )
            )
        return {"findings": findings, "trace": state["trace"] + ["analyze_evidence"]}

    def insufficient(state):
        return {"findings": [], "trace": state["trace"] + ["missing_account_context"]}

    def report(state):
        target = state["transaction"]
        missing = not target["name_orig"] or not target["name_dest"]
        limitations = [
            "DB에 저장된 거래만 조사하며 전체 금융 이력을 보장하지 않는다.",
            "근거는 관측 사실이며 사기 확정이나 모델의 인과 설명으로 해석하지 않는다.",
            "검증된 LLM 설명이 없으면 규칙 기반 분석과 템플릿으로 보고서를 생성한다.",
        ]
        if missing:
            limitations.append("계좌 ID가 없어 계좌 이력 조사를 제한한다.")
        if len(state["history"]) > 100:
            limitations.append("최신 과거 이력 100건으로 근거를 제한한다.")
        if not state["history"]:
            limitations.append("조회된 과거 거래가 없어 이력 기반 판단을 제한한다.")
        status = (
            "insufficient_context"
            if missing
            else ("review_required" if target["is_fraud"] else "no_model_alert")
        )
        trace = state["trace"] + ["compose_report"]
        return {
            "report": dict(
                transaction_id=target["id"],
                status=status,
                risk_score=target["risk_score"],
                threshold=target["threshold"],
                model_run_id=target["model_run_id"],
                cutoff_step=target["step"],
                findings=state["findings"],
                history=state["history"][:100],
                history_truncated=len(state["history"]) > 100,
                limitations=limitations,
                recommendation="담당자가 근거를 검토하고 추가 확인 필요성을 판단한다.",
                trace=trace,
                generation_mode="deterministic",
                workflow_version="1",
            )
        }

    graph = StateGraph(InvestigationState)
    graph.add_node("collect", collect)
    graph.add_node("analyze", analyze)
    graph.add_node("insufficient", insufficient)
    graph.add_node("report", report)
    graph.add_node("explain", lambda state: {
        "report": explain_report(state["report"], generator)
    })
    graph.add_edge(START, "collect")
    graph.add_conditional_edges(
        "collect",
        lambda s: (
            "analyze"
            if (s["transaction"]["name_orig"] and s["transaction"]["name_dest"])
            else "insufficient"
        ),
        {"analyze": "analyze", "insufficient": "insufficient"},
    )
    graph.add_edge("analyze", "report")
    graph.add_edge("insufficient", "report")
    graph.add_edge("report", "explain")
    graph.add_edge("explain", END)
    return graph.compile()


def investigate(transaction_id: UUID) -> dict:
    """LangGraph 조사 흐름을 실행하고 근거 ID가 포함된 보고서를 반환한다."""
    return build_graph().invoke({"transaction_id": str(transaction_id)})["report"]
