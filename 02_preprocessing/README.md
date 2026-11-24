# 02 DB 접속 및 전처리

## 실행 순서

저장소 루트에서 PowerShell 실행:

```powershell
$env:ORACLE_USER = "AIRPORT"
$env:ORACLE_DSN = "localhost:1521/FREEPDB1"
.\.venv\Scripts\python.exe 02_preprocessing/demo_00_connect.py
.\.venv\Scripts\python.exe 02_preprocessing/demo_04_export_from_oracle.py
.\.venv\Scripts\python.exe 02_preprocessing/demo_05_preprocess.py
```

DB 접속 비밀번호는 각 실행 시 입력합니다. 출력은 `02_preprocessing/output/`에 생성됩니다.

- demo_00_connect.py: 실제 Oracle 세션 및 테이블 목록 확인.
- demo_04_export_from_oracle.py: 4개 테이블 JOIN을 실행하여 pandas DataFrame 생성, CSV 저장.
- demo_05_preprocess.py: 정상/지연만 선별, 시간·기상 품질 점검, 풍향 sin/cos, 혼잡도 ±30분 계산, 학습 데이터 생성.
- legacy/preprocess_flight_delay.py: 이전에 작성한 **CSV 기반 초기 전처리 원본**. Oracle 연동 이전 버전이며 실제 최종 학습 데이터와 다름. 실행하려면 flight_project_all(1).csv, weather_all(1).csv를 해당 폴더에 복사. 최대 기상 허용 시간은 코드의 상수와 일치하는 60분입니다.

## 원본과 시연용 파일 구분

당시 최종 PyCharm 스크립트 원문은 미확보. demo_ 파일은 별도로 재구성한 보조 코드입니다.
실제 DB를 통한 적재·추출 통합 테스트는 시연 전 팀원 PC에서 수행하세요.
모델 입력에는 delay_target(정답), ID/편명, 날짜 자체, 실제 운항 결과 등을 넣지 않습니다.
학습/검증 분리, 범주형 인코딩, 필요 시 정규화는 모델링 담당자가 진행합니다.

## 검증 기준

- 출발 기준 1시간 전과 같거나 이전의 기상 관측만 사용 (최대 60분 이전).
- departure_count_60m: 예정 출발시각 ±30분(양끝 포함)의 예정 출발편 수, 자기 자신 포함.
- 복원 데이터 기반으로 계산하는 혼잡도는 해당 스냅샷에 들어 있는 항공편만 세므로 전체 공항 혼잡도와 같지는 않습니다. 결항 여부 등 실제 결과로 스케줄 집합을 제한하지 않고 계산 후 정상/지연을 선별합니다.
- 최초 데이터 추출은 34,776행, 정상/지연은 34,760행. 발표 모델 33,964행과 동일한 파일이 아님.
