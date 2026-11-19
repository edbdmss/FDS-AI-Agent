# 데이터 저장 위치

- `raw/`: Kaggle PaySim 원본 ZIP·CSV (원본 보존)
- `interim/`: 향후 정제·특징 생성 중간 산출물
- `processed/paysim_time_split/<run_id>/`: 실행별 시간순 분할 Parquet과 manifest

원본과 생성 데이터는 Git에서 제외한다.
출처: https://www.kaggle.com/datasets/ealaxi/paysim1
공개 다운로드: https://www.kaggle.com/api/v1/datasets/download/ealaxi/paysim1

`notebooks/01_paysim_eda_time_split.ipynb`에서 원본을 점검하고 분할한다.
ZIP의 CRC 검사와 CSV SHA-256 기록을 수행하며, 실제 파일명·크기는 실행 manifest에서 확인한다.
`.part`는 다운로드 중인 파일로 관리한다. 다운로드 완료 후 노트북의 ZIP 검증을 통과하면 이름을 변경한다.

분할 경계는 사기 레이블 없이 step별 누적 건수로 결정한다.
같은 step은 한 구간에만 속하며 실제 거래 건수 비율은 목표 60:20:20과 다를 수 있다.
연구용 Parquet에는 `isFraud` 등이 포함되므로 모델·Agent 입력으로 직접 넘기지 않는다.
