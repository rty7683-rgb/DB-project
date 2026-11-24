# 인천공항 국제선 출발 지연 예측

Oracle 관계형 DB 설계 → Python 데이터 추출/전처리 → 분석·모델링 과정을 시연하기 위한 저장소입니다.

## 폴더 구성 (실행 순서)

| 단계 | 폴더 | 내용 |
|---|---|---|
| 1 | [01_database](01_database/) | SQL Developer로 테이블 생성, 샘플 데이터 입력, JOIN 확인; 데이터 적재 및 수집 |
| 2 | [02_preprocessing](02_preprocessing/) | Oracle 접속, DataFrame 추출, 전처리 |
| 3 | [03_modeling](03_modeling/) | 팀원의 EDA, 모델 비교·최적화·저장 코드 및 모델 파일 추가 예정 |

## 발표 전 준비 (Windows)

1. Oracle Database와 SQL Developer 설치/실행. 팀원 PC의 기존 DB를 사용할 경우 새로 생성할 필요 없음.
2. SQL Developer에서 실제 Oracle 호스트/포트/서비스명으로 접속. 기존 XE의 SID와 Docker Free의 서비스명은 다를 수 있음.
3. 저장소 복제 및 Python 환경 준비:

```powershell
git clone https://github.com/rty7683-rgb/DB-project.git
cd DB-project
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. 실제 접속 정보를 현재 PowerShell에 설정(비밀번호는 실행 시 입력):

```powershell
$env:ORACLE_USER = "AIRPORT"
$env:ORACLE_DSN = "localhost:1521/FREEPDB1"
```

5. 각 폴더 README에 따라 시연. 기존 데이터가 있는 DB에는 DROP/샘플 INSERT를 실행하지 말 것.

## 데이터 및 코드 버전 주의

- 공개 저장소에 DB 비밀번호, API 인증키, 대용량 CSV, pkl, 실제 로그를 올리지 않습니다.
- 원본 SQL은 1단계 예시 데이터(테이블별 4건)용입니다. 샘플 예측값은 실제 모델 평가 결과가 아닙니다.
- 기존 Python 수집 코드 3개와 초기 CSV 기반 전처리 원본을 보존했습니다(인증키 제거 및 잘못된 설명 정정).
- 당시 PyCharm에서 실행한 01~05번 최종 코드 원문은 아직 미확보 상태입니다. `demo_` 파일은 확보한 데이터 구조를 기반으로 새로 작성한 시연 보조 코드이며, 원본과 동일하다고 주장하지 않습니다.
- 확보한 Oracle 추출본은 34,776행(2026-09-20~10-28), 정상/지연 34,760행입니다. 발표의 EDA/모델링 데이터는 33,964행(2026-09-20~10-27)으로 별도 스냅샷입니다. 실제 모델 담당자의 v3 데이터와 코드를 받기 전까지 동일한 평가 수치를 보장하지 않습니다.
- 혼잡도 수정 이전의 CSV는 사용하지 않습니다. 시연용 전처리에서는 예정 출발시간 ±30분을 정확히 다시 계산합니다.

## 시연 요약

SQL Developer에서 테이블/PK/FK 확인 → SQL JOIN 확인 → Python으로 접속 및 DataFrame 조회 → CSV 전처리 → 팀원 모델링 및 저장. 실제 데이터 적재는 시연 전에 완료해두고, 현장에서는 샘플 조회와 전처리 실행을 보여주는 것을 권장합니다.
