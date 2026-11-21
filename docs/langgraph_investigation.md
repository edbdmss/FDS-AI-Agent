# LangGraph 의심 거래 조사

`POST /v1/transactions/{transaction_id}/investigate`를 호출해 저장 거래를 조사한다. DB의 거래·모델 판단과 두 계좌에 관련된 이전 step 거래 최대 100건을 조회한다. 결과에 근거 거래 ID, 위험 점수, 임계값, 모델 ID, 조사 단계, 한계를 포함한다.

LangGraph는 근거 조회 → 계좌 정보 유무에 따른 분석 또는 정보 부족 분기 → 보고서 생성을 수행한다. 동일 step과 미래 step의 거래는 근거에서 제외한다. 정답과 거래 후 잔액은 조사 근거로 조회하지 않는다. 모델 경보, 전액 거래 여부, 이전 수취 거래를 관측 사실로 설명한다. 특징 기여도나 사기 확정으로 표현하지 않는다.

보고서 생성 다음 단계에 Groq의 `openai/gpt-oss-120b` 설명 생성 노드를 연결한다. 위험 점수·임계값·조사 상태·관측 근거·근거 거래 ID만 전달한다. 계좌 식별자와 원시 거래 이력은 전달하지 않는다. 모델은 JSON 스키마에 맞춰 한국어 설명을 생성한다. 기존 LightGBM 점수와 판정은 변경하지 않는다.

각 설명의 근거 코드와 거래 ID가 원본 근거와 일치하는지 검증한다. 누락·중복·존재하지 않는 인용·추가 필드·문체 오류를 거부한다. 이 검사는 인용 무결성과 형식을 확인하며 문장 의미의 진실성까지 보장하지 않는다. 담당자가 생성 설명을 검토한다.

성공 시 `generation_mode=llm_assisted`, `explanation_status=generated`와 설명을 반환한다. 키 미설정은 `not_configured`, 호출 오류는 `provider_error`, 출력 검증 실패는 `invalid_output`, 근거 부족은 `insufficient_evidence`로 구분한다. 이 경우 `generation_mode=deterministic`과 기존 보고서를 유지한다. 호출 제한 시간은 30초로 설정하고 자동 재시도는 수행하지 않는다. 예외 본문이나 API 키를 응답에 노출하지 않는다.

프로젝트 루트의 `.env`에 다음 설정을 추가한다. 키는 Groq Console에서 발급하고 Git에 커밋하지 않는다. 설정 변경 후 API 서버와 노트북 커널을 재시작한다.

```dotenv
FDS_GROQ_API_KEY=발급받은_Groq_API_키
FDS_LLM_MODEL=openai/gpt-oss-120b
```

[Groq의 구조화 출력 문서](https://console.groq.com/docs/structured-outputs)를 기준으로 엄격한 JSON 스키마를 적용한다. API는 `fds.investigation_reports`에 당시 근거와 설명을 저장한 뒤 `report_id`, `created_at`을 추가해 반환한다. 저장 실패 시 성공으로 응답하지 않고 503을 반환한다. `sql/003_investigation_reports.sql`을 먼저 적용한다. 09 노트북은 JSON과 그래프 정의를 로컬 보고서 폴더에도 저장한다.

`GET /v1/investigations/{report_id}`로 저장 보고서를 조회한다. 조회 시 LLM과 조사 그래프를 다시 실행하지 않는다. 조사 POST를 반복하면 새로운 실행과 보고서를 생성하므로 기존 결과 확인에는 GET을 사용한다. 현재 저장 API는 요청 재시도의 중복을 제거하지 않는다. 테이블은 서버 전용 스키마에서 RLS를 적용하고 브라우저 역할의 접근 권한을 제거한다. API 자체의 인증은 별도로 구현해야 하므로 로컬 시연 범위로 사용한다.

시연 거래 ID는 `b677a82f-3ce6-5fdf-8309-6f06b1befee3`을 사용한다. 실행은 [09_langgraph_investigation.ipynb](../notebooks/09_langgraph_investigation.ipynb)를 참고한다. API 실행 의존성에 `agent`를 포함해 설치한다.

단위 검증에서 근거 ID, 동일·미래 시점 차단, 계좌 정보 부족 분기, 설명 검증 실패, 호출 시간 초과, 기존 예측 보존을 확인한다. 단위 검증은 실제 API를 호출하지 않는다. 실제 Supabase 시연 거래를 조사하는 노트북 실행에서 근거 시점, 근거 ID 존재, 없는 거래의 404 응답을 확인한다. API 키를 설정한 경우에만 실제 LLM 생성 결과를 확인한다. 공개 배포 전 인증과 사용자별 접근 제한을 추가한다.
