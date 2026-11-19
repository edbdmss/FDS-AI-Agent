# 개발 순서

- [x] Python 패키지 구조, 개발 환경, FastAPI health 엔드포인트
- [x] PaySim 확보 및 컬럼·결측·step별 정상/사기 분포 확인
- [x] PySpark 품질 점검, 시간순 분할, Parquet 저장·재검증
- [x] 과거 step 이력만 사용하는 특징 생성 노트북
- [x] LightGBM 기준 모델 학습·Validation 평가·임계값 선택과 모델 저장
- [x] 거래 전 잔액 특징 추가 및 세 후보 비교로 모델 고도화
- [x] 내부 시간순 튜닝으로 평가 편향 수정 및 잔액 특징 의존도 점검
- [x] 고정 모델과 임계값으로 Test 최종 평가
- [ ] 테스트 거래 배치 재생과 추론 파이프라인
- [ ] PostgreSQL 스키마 및 시간 제한 거래 조회 도구
- [ ] LangGraph 조사 흐름과 근거 기반 보고서
- [ ] FastAPI 탐지·조사 API 및 React 대시보드
- [ ] 처리 성능, 모델 성능, Agent 품질 비교 실험

다음 작업은 테스트 거래 배치 재생과 추론 파이프라인을 구현한다. 고정 모델의 결과와 한계는 [Test 평가 결과](test_evaluation_results.md)와 [평가 편향 점검 결과](bias_audit_results.md)를 참고한다.

실행 중 발생한 문제와 해결 과정은 [트러블슈팅 기록](troubleshooting.md)에 정리한다.
