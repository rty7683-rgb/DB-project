"""Oracle 추출 CSV 전처리 시연용 재작성. 발표 모델 v3 원본이 아님."""
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "output"
FEATURES = ["temperature", "humidity", "rainfall", "visibility", "pressure", "wind_speed", "wind_direction"]

def preprocess(df):
    df = df.copy()
    df.columns = df.columns.str.lower()
    df = df.drop_duplicates()
    if df["flight_id"].duplicated().any():
        raise ValueError("flight_id 중복: 운항/기상 매핑 JOIN을 점검하세요.")
    for col in ("scheduled_datetime", "prediction_time", "observation_time"):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df = df.dropna(subset=["scheduled_datetime"]).sort_values("scheduled_datetime").copy()
    # 결과 라벨/기상 품질 필터보다 먼저 전체 제공 스케줄 기준으로 혼잡도를 계산한다.
    times = df["scheduled_datetime"].to_numpy(dtype="datetime64[ns]")
    half = np.timedelta64(30, "m")
    df["departure_count_60m"] = np.searchsorted(times, times + half, side="right") - np.searchsorted(times, times - half, side="left")
    df["delay_target"] = pd.to_numeric(df["delay_code"], errors="coerce")
    df = df[df["delay_target"].isin([0, 1])].copy()
    df["delay_target"] = df["delay_target"].astype(int)
    age = (df["prediction_time"] - df["observation_time"]).dt.total_seconds() / 60
    lead = (df["scheduled_datetime"] - df["prediction_time"]).dt.total_seconds() / 60
    df = df[age.between(0, 60) & lead.eq(60) & pd.to_numeric(df["station_id"], errors="coerce").eq(113)].copy()
    for c in FEATURES + ["regular_type"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=FEATURES + ["regular_type", "airline_code"]).copy()
    df["hour"] = df["scheduled_datetime"].dt.hour
    df["weekday"] = df["scheduled_datetime"].dt.weekday
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)
    df["month"] = df["scheduled_datetime"].dt.month
    radians = np.deg2rad(df["wind_direction"] % 360)
    df["wind_direction_sin"] = np.sin(radians)
    df["wind_direction_cos"] = np.cos(radians)
    cols = ["flight_id", "flight_number", "scheduled_datetime", "airline_code", "regular_type", "hour", "weekday", "is_weekend", "month", "departure_count_60m", "temperature", "humidity", "rainfall", "visibility", "pressure", "wind_speed", "wind_direction_sin", "wind_direction_cos", "delay_target"]
    return df[cols].reset_index(drop=True)

def main():
    raw = pd.read_csv(OUT / "model_raw_from_oracle.csv", low_memory=False)
    df = preprocess(raw)
    if df.empty:
        raise RuntimeError("정상/지연 및 기상 조건에 맞는 데이터가 없습니다.")
    df.to_csv(OUT / "flight_preprocessed_demo.csv", index=False, encoding="utf-8-sig")
    print("전처리 전/후:", raw.shape, df.shape)
    print("라벨 분포:", df["delay_target"].value_counts().to_dict())
    print("혼잡도:", df["departure_count_60m"].describe())
    print("결측 개수:", df.isna().sum().sum())
    print("저장:", OUT / "flight_preprocessed_demo.csv")

if __name__ == "__main__":
    main()
