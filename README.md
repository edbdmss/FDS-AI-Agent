# FDS-AI-Agent

빅데이터 기반 금융 이상거래 탐지 및 자동 조사 AI Agent.
PaySim을 PySpark로 처리하고 LightGBM으로 위험도를 예측한 뒤,
LangGraph Agent가 고위험 거래의 과거 이력을 조사하여 보고서를 생성한다.

## 현재 상태

개발 초기 골격과 실행 가능한 FastAPI `/health`, `/docs`를 구성했다.
PaySim 전체 데이터 점검·시간순 분할 노트북을 실행하고 Parquet 저장·재검증을 완료했다.
모델 학습, 조사, DB 연동, 프론트엔드는 아직 구현하지 않는다.

## 빠른 시작

프로젝트 루트에서 Python 3.11을 사용한다.

```bash
cd /Users/yueun/Desktop/FDS-AI-Agent
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
python -m uvicorn fds_agent.api.main:app --reload --host 127.0.0.1 --port 8000
```

- API 문서: http://127.0.0.1:8000/docs
- 프로세스 상태: http://127.0.0.1:8000/health
- `/health`는 모델·DB 연결을 확인하는 readiness 검사가 아닙니다.

## 폴더 구조

```text
src/fds_agent/
  api/          FastAPI 엔드포인트
  core/         공통 설정
  data/         PySpark 전처리와 시간순 분할
  features/     과거 거래 기반 특징 생성
  models/       LightGBM 학습·평가·추론
  agent/        LangGraph 조사 흐름
    tools/      거래 이력 조회와 패턴 분석 도구
  db/           데이터베이스 모델과 조회
  simulation/   테스트 거래 배치 재생
frontend/       React + TypeScript 대시보드 예정
configs/        실험·파이프라인 설정 예정
scripts/        데이터 처리·학습 실행 스크립트 예정
tests/          검증 코드
notebooks/      실행 가능한 데이터 분석·시간순 분할 노트북
data/           raw / interim / processed (Git 제외)
artifacts/      models / reports (Git 제외)
logs/           실행 로그 (Git 제외)
docs/           설계와 개발 계획
```

## 단계별 의존성

```bash
python -m pip install -e '.[data,ml]'
python -m pip install -e '.[agent,db]'
```

기본 환경에는 API와 개발 도구만 설치한다. 위 선택 의존성은 해당 단계에서 설치·검증한다.
PySpark 실행 전 설치한 버전에 맞는 Java 환경을 준비한다.
LLM 공급자 SDK와 API 키는 공급자 선택 후 추가한다.

```bash
python -m ruff check .
python -m ruff format --check .
```

데이터 준비는 [data/README.md](data/README.md),
설계 원칙은 [docs/architecture.md](docs/architecture.md),
개발 순서는 [docs/roadmap.md](docs/roadmap.md)를 참고한다.

참고: [FastAPI](https://fastapi.tiangolo.com/tutorial/first-steps/),
[PySpark 설치](https://spark.apache.org/docs/latest/api/python/getting_started/install.html)

## Jupyter 데이터 분석

[노트북 실행 안내](notebooks/README.md)를 따라
[PaySim 분포 확인·시간순 분할](notebooks/01_paysim_eda_time_split.ipynb)을 실행한다.

실행 결과: [PaySim 데이터 준비 결과](docs/data_preparation_results.md)

Spark worker 작업 분배 결과는 [발표용 시연 자료](docs/spark_demo_results.md)를 참고한다.

Spark worker 작업 분배 결과는 [발표용 시연 자료](docs/spark_demo_results.md)를 참고한다.

계좌별 과거 거래 특징 생성: [02_paysim_temporal features](notebooks/02_paysim_temporal_features.ipynb)
