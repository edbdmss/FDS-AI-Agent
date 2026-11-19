# PaySim 시간 이력 특징 생성 결과

## 실행 정보

- 실행 ID: `20261117T090124Z-c769f595`
- 입력 분할 실행 ID: `20261117T053742Z-09ddeaeb`
- 입력·출력 행 수: 6,362,620건
- PySpark 버전 및 master: Spark 4.0.1, `local-cluster[2,1,1024]`
- Spark 처리량: 43 jobs, 43 stages, executor task 134건 완료, 실패 0건
- 특징 Parquet: `artifacts/features/paysim_temporal/20261117T090124Z-c769f595/transactions`
- 실행 manifest: `artifacts/features/paysim_temporal/20261117T090124Z-c769f595/manifest.json`
- Spark 지표: `artifacts/reports/20261117T090124Z-c769f595/spark_ui_metrics.json`

## 분할 검증

| 분할 | 거래 수 | 사기 거래 수 | step 범위 |
| --- | ---: | ---: | ---: |
| Train | 3,820,599 | 3,193 | 1–281 |
| Validation | 1,248,498 | 762 | 282–354 |
| Test | 1,293,523 | 4,258 | 355–743 |

원본 분할의 행 수와 정답 건수를 저장 결과에서 다시 대조하고 모두 일치함을 확인한다. 계좌별 이전 특징의 null이 없음을 확인한다.

## 생성 특징과 누수 방지

송금자와 수취자 각각에 대해 과거 거래 건수·금액 합계·평균·활성 step 수·마지막 거래 이후 step 간격을 계산한다. 현재 거래의 step보다 작은 이력만 Spark window 집계에 포함한다. 동일 step과 미래 step은 이력에서 제외하고, 사기 정답은 이력 집계에 넣지 않는다.

모델 허용 입력에는 거래 step·유형·금액·로그 금액·거래 전 잔액 및 송수신자 과거 특징을 포함한다. `isFraud`는 정답으로 분리하고, `isFlaggedFraud`, 거래 후 잔액, 계좌 ID는 모델 입력에서 제외한다. 계좌 ID는 조사 추적 목적으로만 산출물에 유지한다.

노트북은 계산 결과를 Parquet으로 기록하고 다시 읽은 집계 요약을 원본과 대조한다. 결과 manifest는 `verified: true`를 기록한다.

## 다음 작업

검증된 특징 Parquet을 입력으로 LightGBM 기준 모델을 학습하고 Validation 분할에서 임계값과 평가 지표를 정한다. Test 분할은 최종 평가에 사용한다.
