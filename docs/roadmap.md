# 개발 순서

- [x] Python 패키지 구조, 개발 환경, FastAPI health 엔드포인트
- [x] PaySim 확보 및 컬럼·결측·step별 정상/사기 분포 확인
- [x] PySpark 품질 점검, 시간순 분할, Parquet 저장·재검증
- [x] 과거 step 이력만 사용하는 특징 생성 노트북
- [x] LightGBM 기준 모델 학습·Validation 평가·임계값 선택과 모델 저장
- [x] 거래 전 잔액 특징 추가 및 세 후보 비교로 모델 고도화
- [x] 내부 시간순 튜닝으로 평가 편향 수정 및 잔액 특징 의존도 점검
- [x] 고정 모델과 임계값으로 Test 최종 평가
- [x] 저장 모델 거래 점수화 및 사기 판단 API
- [x] 저장된 Spark 특징을 사용하는 시간순 거래 배치 재생과 추론
- [x] DB 저장 거래 기반 계좌 이력 자동 조회·신규 거래 저장·ID 중복 방지
- [x] PostgreSQL 스키마 및 과거 step 제한 거래 조회 API
- [x] Supabase 발표용 거래 6건과 반복 실행 가능한 시연 노트북
- [x] Supabase 연결·거래 및 예측 테이블·원자적 저장 API
- [x] LangGraph 근거 조회·조건 분기·규칙 기반 조사 보고서
- [x] Groq 설명 생성·근거 인용 검증과 조사 보고서 DB 저장·조회
- [ ] FastAPI 탐지·조사 API 및 React 대시보드
- [ ] 처리 성능, 모델 성능, Agent 품질 비교 실험

다음 작업은 테스트 거래 배치 재생과 추론 파이프라인을 구현한다. 고정 모델의 결과와 한계는 [Test 평가 결과](test_evaluation_results.md)와 [평가 편향 점검 결과](bias_audit_results.md)를 참고한다.

추론 API 사용 방법과 입력 계약은 [README](../README.md)의 빠른 시작을 참고한다.

실행 중 발생한 문제와 해결 과정은 [트러블슈팅 기록](troubleshooting.md)에 정리한다.
