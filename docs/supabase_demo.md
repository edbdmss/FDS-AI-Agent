# Supabase 발표용 시연

`08_supabase_demo.ipynb`에서 발표 전용 계좌와 거래 6건을 저장한다. `demo_v1_` 접두사의 계좌를 사용하고 고정 UUID로 재실행 중복을 방지한다. 이 데이터는 손으로 작성한 시나리오이며 정확도 평가용 데이터로 취급하지 않는다.

모델은 소액 PAYMENT·일반 TRANSFER 4건에 약 0.000782517, 잔액 전액 TRANSFER·CASH_OUT 2건에 약 1.0의 점수를 반환한다. 점수는 고정 임계값 0.006350361245177384와 비교한다. 실제 금융 사기를 확정하는 판단으로 해석하지 않는다.

## 시연 순서

1. `http://127.0.0.1:8000/docs`를 연다.
2. `GET /v1/transactions`에 `account=demo_v1_alice`를 입력해 거래와 예측을 조회한다.
3. `before_step=12`를 추가해 step 12보다 이전인 세 거래만 조회함을 확인한다.
4. `GET /v1/transactions/{transaction_id}`에 `b677a82f-3ce6-5fdf-8309-6f06b1befee3`를 입력해 의심 거래의 저장 당시 특징과 결과를 확인한다.
5. Supabase Table Editor에서 `fds` 스키마의 `transactions`와 `predictions` 테이블을 확인한다.

첫 두 거래는 같은 step 10이므로 서로를 과거 이력에 포함하지 않는다. step 11의 송금 이력은 2건, step 12의 송금 이력은 3건으로 계산한다. 동일 ID 재요청은 기존 결과를 반환한다. 이 동작과 과거 시점 필터를 실행으로 검증한다.

CSV와 검증 요약은 `artifacts/reports/demo_v1/`에 저장한다. 공개 배포 전 조회·저장 API에 인증과 사용자별 권한을 적용한다.
