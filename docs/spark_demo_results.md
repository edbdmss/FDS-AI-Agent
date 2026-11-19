# Spark executor 시연 실행 결과

실행 ID: `20261117T053742Z-09ddeaeb`
실행 모드: `local-cluster[2,1,1024]`
동일 컴퓨터 안에 Spark worker 2개와 executor JVM 2개를 실행했다. 실제 여러 서버로 구성된 클러스터 실행은 아니다.
Spark application ID: `app-20261117143743-0000`

## 작업 할당 결과

| Executor | Host | Core | 완료 task | 실패 task | 입력 읽기 누계 | Shuffle 읽기 | Shuffle 쓰기 |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | `127.0.0.1:57127` | 1 | 54 | 0 | 2115.5 MiB | 881.8 MiB | 832.6 MiB |
| 1 | `127.0.0.1:57126` | 1 | 61 | 0 | 1969.6 MiB | 881.6 MiB | 930.8 MiB |

Spark는 **45개 job**, **45개 stage**, **115개 task**를 worker executor 2개에 배분했다. executor에서 실패한 task는 0개다.
입력 읽기 누계에는 같은 CSV를 Spark 작업에서 여러 번 읽은 양이 반영된다.
shuffle 읽기·쓰기는 groupBy, 분할 저장 등에서 Spark가 파티션 사이에 데이터를 재배치한 양을 나타낸다.

## 발표용 시각화

- [CSV 및 집계 단계별 파티션 작업량](/Users/yueun/Desktop/FDS-AI-Agent/artifacts/reports/20261117T053742Z-09ddeaeb/spark_partitions.png)
- [executor별 완료 task 및 shuffle 처리량](/Users/yueun/Desktop/FDS-AI-Agent/artifacts/reports/20261117T053742Z-09ddeaeb/spark_executors.png)
- [stage별 병렬 task 수](/Users/yueun/Desktop/FDS-AI-Agent/artifacts/reports/20261117T053742Z-09ddeaeb/spark_stages.png)
- [전체 Spark UI REST 실행 기록](/Users/yueun/Desktop/FDS-AI-Agent/artifacts/reports/20261117T053742Z-09ddeaeb/spark_ui_metrics.json)
- [Spark event log 디렉터리](/Users/yueun/Desktop/FDS-AI-Agent/artifacts/reports/20261117T053742Z-09ddeaeb/spark-events)

Spark UI REST snapshot과 event log는 Git에서 제외된 보고서 폴더에 보관한다. 노트북을 실행하는 동안 표시된 Spark UI 링크를 열면 Jobs·Stages·Executors 화면을 볼 수 있다.
Parquet 분할 및 행 보존 검증도 동일 application에서 함께 실행했다.
동일 원본의 전체 6,362,620건에 대한 시간순 분할과 양방향 전체 행 대조가 통과했다.
