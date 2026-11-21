"""조사 당시 보고서를 저장하고 LLM 재호출 없이 조회한다."""

import json
from uuid import UUID, uuid4

from sqlalchemy import text

from fds_agent.db.storage import get_engine


def save_report(report: dict) -> dict:
    """조사 실행별 ID와 저장 시각을 반환하며 기존 보고서를 덮어쓰지 않는다."""
    identity = str(uuid4())
    with get_engine().begin() as conn:
        created_at = conn.execute(
            text("INSERT INTO fds.investigation_reports (id, transaction_id, report) "
                 "VALUES (:id, :transaction_id, CAST(:report AS jsonb)) RETURNING created_at"),
            {"id": identity, "transaction_id": report["transaction_id"],
             "report": json.dumps(report, ensure_ascii=False, allow_nan=False)},
        ).scalar_one()
    return {**report, "report_id": identity, "created_at": created_at.isoformat()}


def get_report(identity: UUID) -> dict:
    """저장된 보고서를 조회하고 없는 ID를 구분한다."""
    with get_engine().connect() as conn:
        row = conn.execute(
            text("SELECT id, report, created_at FROM fds.investigation_reports WHERE id=:id"),
            {"id": str(identity)},
        ).mappings().first()
    if row is None:
        raise LookupError("조사 보고서를 찾을 수 없다.")
    return {**row["report"], "report_id": str(row["id"]),
            "created_at": row["created_at"].isoformat()}
