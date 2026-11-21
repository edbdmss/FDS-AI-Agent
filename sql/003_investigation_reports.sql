-- 조사 실행마다 당시 근거와 설명을 변경 불가능한 스냅샷으로 기록한다.
CREATE TABLE IF NOT EXISTS fds.investigation_reports (
    id uuid PRIMARY KEY,
    transaction_id uuid NOT NULL REFERENCES fds.transactions(id),
    report jsonb NOT NULL CHECK (jsonb_typeof(report) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS investigation_reports_transaction_idx
    ON fds.investigation_reports(transaction_id, created_at DESC, id);
ALTER TABLE fds.investigation_reports ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON fds.investigation_reports FROM PUBLIC, anon, authenticated;
