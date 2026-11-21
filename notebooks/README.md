# 데이터 분석 노트북

## 09_langgraph_investigation.ipynb

Supabase 시연 거래를 LangGraph로 조사하고 근거 ID·과거 시점·없는 거래 응답을 확인한다. 보고서 JSON과 그래프 정의를 실행별 보고서 폴더에 저장한다. LLM 호출 없이 규칙 기반으로 동작함을 명시한다.

## 08_supabase_demo.ipynb

발표 전용 계좌와 거래 6건을 저장하고 위험 점수와 과거 이력을 확인한다. 고정 거래 ID로 재실행 중복을 방지하고 같은 step 이력 제외·과거 시점 조회를 검증한다. 이 시나리오는 모델 성능 평가에 사용하지 않는다. 상세 절차는 [Supabase 시연](../docs/supabase_demo.md)을 참고한다.

## 07_transaction_replay.ipynb

Test 전체를 step 순으로 정렬하고 10,000건씩 저장 모델에 전달한다. 과거 이력은 Spark가 저장한 특징을 사용한다. 단건 API와 배치 점수의 일치, 전체 건수 보존, 고정 Test 평가와 혼동행렬의 일치를 확인한다. 예측 결과는 실행별 보고서 폴더에 저장한다.

## 06_frozen_model_test_evaluation.ipynb

내부 튜닝에서 선택한 모델과 임계값을 고정하고 Test 전체를 평가한다. 모델 해시와 입력 행 수·정답 수·시간 범위를 검증한다. 05 노트북에서 특징 함수만 추출하고 저장 모델로 예측한다. Test 결과로 모델이나 임계값을 변경하지 않는다. 최종 지표와 거래 유형별·step별 오류 분포, PR 곡선, 혼동행렬을 기록한다.

## 05_bias_audit_temporal_validation.ipynb

Train 내부의 시간순 분할에서 모델과 임계값을 선택하고 저장한 뒤, 기존 Validation에 고정 설정을 적용한다. 기준 특징·잔액 특징 추가·송금자 잔액 전체 제거 후보를 비교한다. Validation 결과에 따라 모델이나 임계값을 다시 선택하지 않는다. 과거에 관찰한 Validation이라는 한계를 명시하고 Test는 보존한다.

## 04_lightgbm_improvement.ipynb

기준 모델과 거래 전 잔액 기반 파생 특징을 사용하는 세 후보를 비교한다. Validation F1을 기준으로 모델과 임계값을 선택하고 PR 곡선과 거래 유형별 오류를 확인한다. 반복 선택에 사용한 Validation 성능은 선택용 성능으로 해석한다. 후속 추론에서는 노트북의 `enrich` 함수와 동일한 특징 계산을 적용한다.

## 03_lightgbm_baseline.ipynb

검증된 특징 Parquet의 Train과 Validation을 읽고 LightGBM 기준 모델을 학습한다. `pip install -e '.[ml]'`로 학습 의존성을 설치한다. macOS에서 OpenMP 라이브러리가 없으면 `brew install libomp`를 실행한다.

Validation Average Precision으로 조기 종료하고 F1이 최대인 임계값을 선택한다. Precision, Recall, F1, 사다리꼴 PR-AUC, Average Precision과 혼동행렬 건수를 기록한다. 기본 임계값 0.5와 비교하고 PR 곡선 및 임계값별 F1을 시각화한다. 모델·범주 목록·특징 순서·임계값은 `artifacts/models/<run_id>/`에 저장한다. Test는 후속 최종 평가에서 사용한다.

## 실행 환경

프로젝트 루트에서 Python 3.11, Java 17, PySpark 4.0.1을 사용한다.

```bash
source .venv/bin/activate
python -m pip install -e '.[data,notebook,dev]'
python -m ipykernel install --sys-prefix --name fds-ai-agent --display-name 'FDS AI Agent (Python 3.11)'
python -m jupyterlab notebooks/01_paysim_eda_time_split.ipynb
```

노트북에서 **FDS AI Agent (Python 3.11)** 커널을 선택하고 위에서 아래로 모두 실행한다.
기존 API 서버 파일은 유지하며, 데이터 점검과 분할 로직은 `.ipynb` 안에 구현한다.

## 01_paysim_eda_time_split.ipynb

1. `data/raw/`의 ZIP 검증·CSV 추출, 컬럼·원본 SHA-256 기록
2. PySpark로 전체 데이터 로딩 및 품질 검사
3. 전체·거래 유형·step별 분포를 집계해 표와 그래프로 표시
4. local-cluster worker 2개와 executor JVM을 실행하고, executor별 task·shuffle 지표를 시각화
5. Spark UI Jobs·Stages·Executors 기록과 물리 실행 계획을 확인
6. 동일 step을 보존하면서 누적 거래 건수 기준 60% / 80%로 시간순 분할
7. Train / Validation / Test Parquet을 저장하고 전체 행 보존을 검증
8. 실행 정보, 분할 요약, Spark UI 지표를 manifest와 보고서에 기록

데이터는 전체를 사용하며 Pandas에는 작은 집계 결과만 가져옵니다.
실행마다 새 실행 ID를 만들어 기존 결과를 보존한다.
중간 실패한 실행은 `manifest.json`이 없으므로 후속 학습에 사용하지 않는다.

## 산출물

- `data/processed/paysim_time_split/<run_id>/transactions/split=train/`
- `data/processed/paysim_time_split/<run_id>/transactions/split=validation/`
- `data/processed/paysim_time_split/<run_id>/transactions/split=test/`
- `data/processed/paysim_time_split/<run_id>/manifest.json`
- `artifacts/reports/<run_id>/`: 분포 CSV, 그래프 PNG, 분할 요약, manifest

연구용 Parquet에는 정답이 포함되어 있다. 모델·Agent 입력은 별도의 허용 컬럼을 선택한다.
Parquet 저장 순서는 시간순을 보장하지 않으므로 재생 시 `step`으로 정렬한다.

## 02_paysim_temporal_features.ipynb

시간순 분할 Parquet에서 `step`보다 앞선 계좌 이력 특징을 PySpark로 만든다. 동일 `step`과 미래 이력은 window에서 제외한다. 사기 레이블은 계좌 이벤트 집계에 포함하지 않는다. 분할별 행·정답 건수를 원본에 대조하고 Spark UI 기록과 run manifest를 저장한다.

## Spark 시연

노트북은 `local-cluster[2,1,1024]`에서 두 Spark worker와 executor JVM을 실행한다.
각 worker가 한 core를 사용하고 executor heap은 768 MiB로 제한한다. 한 머신 안에서 동작하는 로컬 클러스터이며 여러 서버로 된 클러스터는 아니다.
Spark UI 링크는 실행 중 Jobs·Stages·Executors 화면을 연다. 이벤트 로그, REST API snapshot, partition·executor·stage 그래프는 `artifacts/reports/<run_id>/`에 저장한다.
실행 계획에서는 CSV scan과 집계·shuffle 구간을 확인한다.

실제 작업 분배 수치는 [두 executor의 Spark 실행 결과](../docs/spark_demo_results.md)에 기록한다.

# 대화형 실행

`10_conversational_agent.ipynb`의 첫 설정 셀을 실행하고 마지막 입력 셀에서 자연어로 대화한다. 중간 시연 셀은 거래 검색·후속 조사·보고서 재조회를 실제 실행한다. 별도 API 서버 없이 프로젝트의 `.venv` 커널로 실행한다.
