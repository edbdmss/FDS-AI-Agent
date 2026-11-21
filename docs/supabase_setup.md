# Supabase 연결과 예측 저장

`.env`의 `FDS_DATABASE_URL`을 서버에서 읽는다. 비밀번호의 URL 예약문자는 인코딩하고 비밀값을 Git·API 응답에 노출하지 않는다. 의존성은 `pip install -e '.[ml,data,db]'`로 설치한다.

`sql/001_transactions_predictions.sql`을 적용해 서버 전용 `fds` 스키마의 `transactions`, `predictions` 테이블을 생성한다. 브라우저 역할의 접근 권한을 제거하고 RLS를 활성화한다. Supabase Table Editor에서는 스키마 선택을 `fds`로 변경해 테이블을 확인한다.

`POST /v1/predict`는 점수만 반환한다. `POST /v1/predict-and-save`는 같은 입력으로 점수를 계산하고 거래 입력·모델 실행 ID·점수·임계값·판단을 하나의 DB 트랜잭션에서 저장한다. 응답의 `transaction_id`로 두 테이블의 행을 연결한다. 재요청은 새 거래로 저장하므로 재시도 중복 방지는 후속 작업으로 관리한다.

실제 Supabase 연결·스키마 생성·API 저장·두 테이블 조인 조회를 확인한다. 검증용으로 생성한 한 거래와 예측 행만 확인 후 삭제한다. 원본 PaySim 전체 데이터 업로드는 수행하지 않는다.

공개 배포 전에 API 인증과 사용자별 권한을 추가한다. 현재 API는 로컬 시연용으로 사용한다. 계좌 ID 기반 이력 조회·갱신과 재시도 중복 방지는 후속 작업으로 진행한다.
