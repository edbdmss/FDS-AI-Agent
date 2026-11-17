# 설계 기준

## 처리 흐름

PaySim CSV → PySpark 정제·특징 생성 → Parquet → LightGBM 학습·검증
→ 저장된 모델 → 테스트 거래 배치 재생 → 위험도 예측
→ 고위험 거래 LangGraph 조사 → PostgreSQL 결과 저장 → FastAPI / React

Spark는 데이터 가공을, LightGBM은 모델 학습과 추론을 담당합니다.
LLM 공급자와 모델은 아직 정하지 않았습니다.

## 데이터와 평가 원칙

- `step` 시간순으로 Train / Validation / Test 목표 비율 60 / 20 / 20을 적용합니다.
- 같은 `step`은 분할 경계를 넘지 않습니다. 실제 비율과 사기 건수를 기록합니다.
- 과거 이력은 `history.step < transaction.step`만 허용합니다.
- `isFraud`는 학습 정답과 평가에만 사용하고 추론·Agent 입력에서 제거합니다.
- `isFlaggedFraud`, 거래 이후 잔액은 초기 모델 입력에서 제외합니다.
- 계좌 ID는 조회와 과거 특징 생성에 사용합니다.
- 검증 구간으로 하이퍼파라미터와 임계값을 선택하고 테스트는 최종 평가에 사용합니다.
- 모델: Precision, Recall, F1, PR-AUC. Agent: 근거 정확성, 완료율, 처리 시간.
- Agent와 모델을 각각 평가합니다. 보고서 생성이 탐지 정확도 향상을 뜻하지는 않습니다.

## MVP 범위

공개 합성 데이터로 거래 유입을 재현합니다. 배치 크기·주기는 추후 설정합니다.
실제 계좌 차단, 자동 재학습, 복잡한 계좌 그래프 분석은 포함하지 않습니다.
