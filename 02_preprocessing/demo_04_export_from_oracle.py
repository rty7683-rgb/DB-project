"""DB JOIN → DataFrame → CSV 시연용 (재작성)."""
from pathlib import Path
import pandas as pd
from db_config import connect

SQL = """
SELECT f.flight_id, f.airline_code, f.flight_number, f.flight_date,
       f.scheduled_datetime, f.direction, f.line_type, f.regular_type,
       f.use_code, f.passenger_yn,
       fo.status_code, fo.delay_code, fo.gate, fo.spot, fo.collected_at,
       fw.prediction_time, w.weather_id, w.station_id, w.observation_time,
       w.temperature, w.humidity, w.rainfall, w.visibility, w.pressure,
       w.wind_speed, w.wind_direction
FROM FLIGHT f
JOIN FLIGHT_OPERATION fo ON f.flight_id = fo.flight_id
JOIN FLIGHT_WEATHER fw ON f.flight_id = fw.flight_id
JOIN WEATHER w ON fw.weather_id = w.weather_id
WHERE f.direction = 'D' AND f.line_type = 'I' AND f.use_code = '0'
ORDER BY f.scheduled_datetime, f.flight_id
"""

def main():
    with connect() as con, con.cursor() as cur:
        cur.execute(SQL)
        columns = [c[0].lower() for c in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=columns)
    if df.empty:
        raise RuntimeError("실제 국제선 여객 출발편이 없습니다. 샘플 DB가 아닌 실제 DB인지 확인하세요.")
    out = Path(__file__).parent / "output"
    out.mkdir(exist_ok=True)
    df.to_csv(out / "model_raw_from_oracle.csv", index=False, encoding="utf-8-sig")
    print("DataFrame shape:", df.shape)
    print(df.head().to_string(index=False))
    print("CSV 저장:", out / "model_raw_from_oracle.csv")

if __name__ == "__main__":
    main()
