# LightGBM 기준 모델 Validation 결과

실행 ID `20261119T072526Z-09107167`에서 특징 실행 `20261117T090124Z-c769f595`를 재사용한다. Train 3,820,599건으로 학습하고 Validation 1,248,498건으로 조기 종료와 임계값 선택을 수행한다.

| 정책 | 임계값 | Precision | Recall | F1 | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| 기본 | 0.5 | 0.854167 | 0.591864 | 0.699225 | 0.758815 |
| Validation F1 최대 | 0.290304 | 0.794793 | 0.681102 | 0.733569 | 0.758815 |

PR-AUC는 PR 곡선의 사다리꼴 적분으로 계산한다. Average Precision은 별도로 0.758877을 기록한다. 선택 임계값에서 TP 519건, FP 134건, FN 243건, TN 1,247,602건을 확인한다.

Validation을 모델 선택과 임계값 선택에 사용하므로 위 성능은 선택용 성능으로 해석한다. 후속 Test 평가에서는 모델과 임계값을 고정한다.

모델과 입력 스키마는 `artifacts/models/20261119T072526Z-09107167/`에 저장한다. 지표 CSV와 그래프는 같은 실행 ID의 `artifacts/reports/`에 저장한다. 두 폴더의 생성 파일은 Git에서 제외한다.

실행 노트북은 [03_lightgbm_baseline.ipynb](../notebooks/03_lightgbm_baseline.ipynb)를 사용한다. macOS의 `libomp.dylib` 누락 오류는 `brew install libomp`로 OpenMP 런타임을 설치해 해결한다.
