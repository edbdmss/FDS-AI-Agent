-- 서버 전용 스키마에 거래와 모델 판단을 저장한다.
CREATE SCHEMA IF NOT EXISTS fds;
REVOKE ALL ON SCHEMA fds FROM PUBLIC, anon, authenticated;

CREATE TABLE IF NOT EXISTS fds.transactions (
    id uuid PRIMARY KEY,
    step integer NOT NULL CHECK (step >= 0),
    transaction_type text NOT NULL,
    features jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS fds.predictions (
    transaction_id uuid PRIMARY KEY REFERENCES fds.transactions(id),
    model_run_id text NOT NULL,
    risk_score double precision NOT NULL CHECK (risk_score BETWEEN 0 AND 1),
    threshold double precision NOT NULL CHECK (threshold BETWEEN 0 AND 1),
    is_fraud boolean NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS transactions_step_idx ON fds.transactions(step);
ALTER TABLE fds.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE fds.predictions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON fds.transactions, fds.predictions FROM PUBLIC, anon, authenticated;
