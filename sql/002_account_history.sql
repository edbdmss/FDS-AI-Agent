-- 계좌별 과거 거래 조회와 재요청 비교 정보를 추가한다.
ALTER TABLE fds.transactions ADD COLUMN IF NOT EXISTS name_orig text;
ALTER TABLE fds.transactions ADD COLUMN IF NOT EXISTS name_dest text;
ALTER TABLE fds.transactions ADD COLUMN IF NOT EXISTS request_payload jsonb;
CREATE INDEX IF NOT EXISTS transactions_origin_step_idx ON fds.transactions(name_orig, step);
CREATE INDEX IF NOT EXISTS transactions_destination_step_idx ON fds.transactions(name_dest, step);
