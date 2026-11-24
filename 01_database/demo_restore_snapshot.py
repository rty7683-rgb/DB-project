"""기존 Oracle JOIN CSV로 빈 프로젝트 스키마를 재구성하는 시연용 코드.
원본 원천 CSV 전체 적재 코드가 아니며, 기존 데이터에 덮어쓰지 않는다.
"""
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02_preprocessing"))
from db_config import connect

SOURCE = Path(__file__).parent / "data" / "model_raw_from_oracle.csv"
TABLES = ("AIRLINE", "WEATHER", "FLIGHT", "FLIGHT_OPERATION", "FLIGHT_WEATHER", "MODEL_RESULT")
W = ["weather_id", "station_id", "observation_time", "temperature", "humidity", "rainfall", "visibility", "pressure", "wind_speed", "wind_direction"]
F = ["flight_id", "airline_code", "flight_number", "flight_date", "scheduled_datetime", "direction", "line_type", "regular_type", "use_code", "passenger_yn"]
O = ["flight_id", "status_code", "delay_code", "gate", "spot", "collected_at"]

def value(v):
    if pd.isna(v):
        return None
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime()
    if hasattr(v, "item"):
        return v.item()
    return v

def insert(cur, table, columns, rows):
    rows = [tuple(value(v) for v in row) for row in rows]
    binds = ", ".join(":" + str(i) for i in range(1, len(columns) + 1))
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({binds})"
    for i in range(0, len(rows), 1000):
        cur.executemany(sql, rows[i:i+1000])
    print(table, len(rows))

def main():
    df = pd.read_csv(SOURCE, low_memory=False, dtype={"flight_id": str, "airline_code": str, "flight_number": str, "direction": str, "line_type": str, "regular_type": str, "use_code": str, "passenger_yn": str, "status_code": str, "delay_code": str, "gate": str, "spot": str, "station_id": str})
    if df["flight_id"].duplicated().any():
        raise ValueError("스냅샷의 항공편 ID가 중복됨")
    for col in ("flight_date", "scheduled_datetime", "collected_at", "observation_time"):
        df[col] = pd.to_datetime(df[col], errors="raise")
    weather = df[W].drop_duplicates()
    if weather["weather_id"].duplicated().any():
        raise ValueError("weather_id 중복/충돌")
    with connect() as con, con.cursor() as cur:
        for table in TABLES:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            if cur.fetchone()[0]:
                raise RuntimeError(f"{table}에 기존 데이터가 있습니다. 빈 스키마에서만 실행하세요.")
        try:
            codes = sorted(df["airline_code"].dropna().unique())
            insert(cur, "AIRLINE", ["airline_code", "airline_name"], [(c, c) for c in codes])
            insert(cur, "WEATHER", W, weather.itertuples(index=False, name=None))
            insert(cur, "FLIGHT", F, df[F].itertuples(index=False, name=None))
            insert(cur, "FLIGHT_OPERATION", ["operation_id"] + O, [(i, *r) for i, r in enumerate(df[O].itertuples(index=False, name=None), 1)])
            # 원본 1단계 DDL의 prediction_time은 VARCHAR2(20).
            # ISO 19자 문자열을 넣고 추출 후 pandas datetime으로 변환한다.
            mapping = df[["flight_id", "weather_id", "prediction_time"]].copy()
            mapping["prediction_time"] = pd.to_datetime(mapping["prediction_time"], errors="raise").dt.strftime("%Y-%m-%d %H:%M:%S")
            insert(cur, "FLIGHT_WEATHER", ["flight_weather_id", "flight_id", "weather_id", "prediction_time"], [(i, *r) for i, r in enumerate(mapping.itertuples(index=False, name=None), 1)])
            con.commit()
        except Exception:
            con.rollback()
            raise
    print("복원 완료. MODEL_RESULT는 비워 둡니다.")

if __name__ == "__main__":
    main()
