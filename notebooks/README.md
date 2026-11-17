# 데이터 분석 노트북

## 실행 환경

프로젝트 루트에서 실행합니다. Python 3.11, Java 17, PySpark 4.0.1을 사용합니다.

```bash
source .venv/bin/activate
python -m pip install -e '.[data,notebook,dev]'
python -m ipykernel install --sys-prefix --name fds-ai-agent --display-name 'FDS AI Agent (Python 3.11)'
python -m jupyterlab notebooks/01_paysim_eda_time_split.ipynb
```

노트북에서 **FDS AI Agent (Python 3.11)** 커널을 선택하고 위에서 아래로 모두 실행하세요.
기존 API 서버 파일은 유지하며, 데이터 점검과 분할 로직은 `.ipynb` 안에 구현했습니다.

## 01_paysim_eda_time_split.ipynb

1. `data/raw/`의 ZIP 검증·CSV 추출, 컬럼·원본 SHA-256 기록
2. PySpark로 전체 데이터 로딩 및 품질 검사
3. 전체·거래 유형·step별 분포 표와 그래프 생성
4. 같은 step을 보존하며 누적 거래 건수 기준 60% / 80% 경계 선택
5. Train / Validation / Test Parquet 저장 및 전체 행 보존 검증
6. 실행 정보와 분할 요약을 manifest에 기록

데이터는 전체를 사용하며 Pandas에는 작은 집계 결과만 가져옵니다.
실행할 때마다 새 실행 ID를 만들어 기존 결과를 보존합니다.
중간 실패한 실행은 `manifest.json`이 없으므로 후속 학습에 사용하지 마세요.

## 산출물

- `data/processed/paysim_time_split/<run_id>/transactions/split=train/`
- `data/processed/paysim_time_split/<run_id>/transactions/split=validation/`
- `data/processed/paysim_time_split/<run_id>/transactions/split=test/`
- `data/processed/paysim_time_split/<run_id>/manifest.json`
- `artifacts/reports/<run_id>/`: 분포 CSV, 그래프 PNG, 분할 요약, manifest

연구용 Parquet에는 정답이 포함되어 있습니다. 모델·Agent용 입력은 별도 컬럼 선택이 필요합니다.
Parquet 저장 순서는 시간순을 보장하지 않으므로 재생 시 `step`으로 정렬하세요.
