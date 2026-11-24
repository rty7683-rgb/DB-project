# 01 DB 설계 및 데이터 입력

## SQL Developer 시연

SQL Developer는 Oracle DB에 접속하는 GUI 도구입니다. SQL 파일을 GitHub에서 내려받아 SQL Worksheet에서 열고 F5(Run Script)로 실행할 수 있습니다.

- 기존 DB 사용: 접속 후 Tables에서 AIRLINE, WEATHER, FLIGHT, FLIGHT_OPERATION, FLIGHT_WEATHER, MODEL_RESULT 확인. `03_verify.sql` 실행.
- 빈 연습용 스키마: `01_create_tables.sql` → `02_insert_sample.sql` → `03_verify.sql` 순서로 실행. 각각 4건 예시가 입력됩니다.
- 실제 데이터 복원: 빈 스키마에서 `01_create_tables.sql`만 실행 후 아래 복원 보조 코드 실행. 샘플 데이터를 먼저 넣지 않습니다.
- 원본 SQL은 `original_phase1.sql`로 보존했습니다. **처음에 DROP TABLE을 실행하여 기존 테이블과 데이터를 삭제하므로 현장 실제 DB에서 전체 실행하지 마세요.**
- 원본 DDL의 FLIGHT_OPERATION.flight_id는 UNIQUE 제약이 있고, FLIGHT_WEATHER.prediction_time은 VARCHAR2(20)입니다. 기존 DB 구조를 확인하고, 실제 적재에 맞춘 별도 DDL 원본이 있으면 교체하세요.

## Oracle 환경

기존 팀원 DB가 이미 있으면 그 접속 정보를 이용하세요. Docker 환경은 포트 1521, 서비스 FREEPDB1 예시이며 비밀번호는 따로 관리합니다.
새 스키마가 필요하면 DBA가 전용 사용자 및 데이터 저장용 테이블스페이스/권한을 생성한 뒤 해당 사용자로 접속합니다. SYSTEM 계정에 프로젝트 테이블을 만드는 방식은 피합니다.

## 실제 데이터 복원 보조 (원본 적재 코드 미확보)

`data/model_raw_from_oracle.csv`에 기존 DB에서 추출한 34,776행 CSV를 별도로 넣습니다. 저장소 루트에서:

```powershell
.\.venv\Scripts\python.exe 01_database/demo_restore_snapshot.py
```

이 코드는 이미 매칭된 Oracle JOIN 결과를 이용해 관계형 테이블을 다시 구성합니다. 모든 원시 기상 기록이 아니라 기존 항공편과 매핑된 기상값만 복원하고, 항공사명은 코드로 대체합니다. MODEL_RESULT에는 가짜 값을 넣지 않습니다. 원본 02/03 적재·기상 매핑 스크립트를 받으면 해당 원본을 별도로 추가합니다.

## 수집 원본

`collection/collector_core.py`, `collect_manual.py`, `collect_auto.py` 보존.
실시간 수집은 선택 사항이며 발표 때는 고정 스냅샷 사용을 권장합니다.
수집 시에만 DATA_GO_KR_KEY, KMA_API_KEY 환경변수를 실제 키로 설정합니다(커밋 금지).
