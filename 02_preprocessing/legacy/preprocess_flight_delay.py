"""
인천공항 국제선 출발 여객편 지연예측 - 1차 전처리

입력
- flight_project_all(1).csv : 국제선/출발/여객편 필터 완료 누적 데이터
- weather_all(1).csv        : 인천공항 AMOS 분 단위 기상 데이터

출력
- flight_preprocessed_core.csv : 모델링 직전 핵심 데이터
- preprocessing_report.txt     : 전처리 결과 요약

주의
- msDelay 0(정상), 1(지연)만 사용. 2(결항), 3(회항)은 제외.
- 예측시점 = 예정출발 1시간 전.
- 기상은 예측시점과 같거나 이전 관측값만 사용하여 미래정보 누수를 방지.
- 기상 관측값이 예측시점보다 60분을 초과해 오래된 경우 매칭하지 않음.
- Gate/Spot, collected_at, msSid, msDelay 원본 등은 모델 입력에서 제외.
- departure_count_60m(혼잡도)는 EDA/파생변수 담당자가 별도 생성 후 합치는 것을 전제로 함.
"""

from __future__ import annotations

import csv
import math
from bisect import bisect_right
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FLIGHT_PATH = BASE_DIR / "flight_project_all(1).csv"
WEATHER_PATH = BASE_DIR / "weather_all(1).csv"
OUTPUT_PATH = BASE_DIR / "flight_preprocessed_core.csv"
REPORT_PATH = BASE_DIR / "preprocessing_report.txt"

WEATHER_TOLERANCE_MIN = 60


def parse_dt(value: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    return datetime.strptime(value.strip(), fmt)


def to_float(value: str):
    value = (value or "").strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_weather():
    weather_rows = []
    with WEATHER_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            obs = parse_dt(row["observation_time"])
            weather_rows.append({
                "observation_time": obs,
                "temperature": to_float(row["temperature"]),
                "humidity": to_float(row["humidity"]),
                "rainfall": to_float(row["rainfall"]),
                "visibility": to_float(row["left_visibility"]),
                "pressure": to_float(row["sea_level_pressure"]),
                "wind_direction": to_float(row["wind_dir_10min"]),
                "wind_speed": to_float(row["wind_speed_10min"]),
            })

    weather_rows.sort(key=lambda x: x["observation_time"])
    weather_times = [r["observation_time"] for r in weather_rows]
    return weather_rows, weather_times


def find_previous_weather(prediction_time, weather_rows, weather_times):
    # prediction_time 이후 관측값을 절대 사용하지 않음
    idx = bisect_right(weather_times, prediction_time) - 1
    if idx < 0:
        return None, None

    row = weather_rows[idx]
    age_min = (prediction_time - row["observation_time"]).total_seconds() / 60.0
    if age_min < 0 or age_min > WEATHER_TOLERANCE_MIN:
        return None, age_min
    return row, age_min


def cyclical_direction(deg):
    if deg is None:
        return None, None
    rad = math.radians(deg % 360)
    return math.sin(rad), math.cos(rad)


def main():
    weather_rows, weather_times = load_weather()

    source_rows = 0
    excluded_cancel = 0
    excluded_divert = 0
    bad_datetime = 0
    weather_unmatched = 0
    matched_ages = []
    class_counts = Counter()
    output_rows = []

    with FLIGHT_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            source_rows += 1
            delay_code = (row.get("msDelay") or "").strip()

            if delay_code == "2":
                excluded_cancel += 1
                continue
            if delay_code == "3":
                excluded_divert += 1
                continue
            if delay_code not in {"0", "1"}:
                continue

            try:
                scheduled = parse_dt(row["scheduled_datetime"])
            except Exception:
                bad_datetime += 1
                continue

            prediction_time = scheduled - timedelta(hours=1)
            weather, weather_age = find_previous_weather(
                prediction_time, weather_rows, weather_times
            )

            if weather is None:
                weather_unmatched += 1
                continue

            matched_ages.append(weather_age)
            wind_sin, wind_cos = cyclical_direction(weather["wind_direction"])
            target = int(delay_code)
            class_counts[target] += 1

            # 월요일=0 ~ 일요일=6
            weekday = scheduled.weekday()

            output_rows.append({
                # 추적/검증용 ID (모델 입력에서는 제외)
                "flight_key": f"{row['msDate']}_{row['flightNum']}_{row['msStime']}",
                "flight_number": row["flightNum"].strip(),
                "flight_date": scheduled.strftime("%Y-%m-%d"),
                "scheduled_datetime": scheduled.strftime("%Y-%m-%d %H:%M:%S"),
                "prediction_time": prediction_time.strftime("%Y-%m-%d %H:%M:%S"),

                # 운항 특성 후보
                "airline_iata": row["airline_iata"].strip(),
                "regular_type": int(row["msRegul"]) if row["msRegul"].strip() in {"0", "1"} else "",
                "hour": scheduled.hour,
                "weekday": weekday,
                "is_weekend": 1 if weekday >= 5 else 0,

                # 기상 특성 후보
                "temperature": weather["temperature"],
                "humidity": weather["humidity"],
                "rainfall": weather["rainfall"],
                "visibility": weather["visibility"],
                "pressure": weather["pressure"],
                "wind_speed": weather["wind_speed"],
                "wind_direction": weather["wind_direction"],
                "wind_dir_sin": wind_sin,
                "wind_dir_cos": wind_cos,

                # 감사(audit)용: 모델 입력에서는 기본적으로 제외 권장
                "weather_observation_time": weather["observation_time"].strftime("%Y-%m-%d %H:%M:%S"),
                "weather_age_min": round(weather_age, 1),

                # 정답
                "delay_target": target,
            })

    output_rows.sort(key=lambda r: r["scheduled_datetime"])

    fieldnames = [
        "flight_key", "flight_number", "flight_date", "scheduled_datetime", "prediction_time",
        "airline_iata", "regular_type", "hour", "weekday", "is_weekend",
        "temperature", "humidity", "rainfall", "visibility", "pressure",
        "wind_speed", "wind_direction", "wind_dir_sin", "wind_dir_cos",
        "weather_observation_time", "weather_age_min", "delay_target"
    ]

    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    if matched_ages:
        sorted_ages = sorted(matched_ages)
        age_mean = sum(matched_ages) / len(matched_ages)
        age_p95 = sorted_ages[min(len(sorted_ages)-1, int(len(sorted_ages)*0.95))]
        age_max = max(matched_ages)
    else:
        age_mean = age_p95 = age_max = float("nan")

    total_kept = len(output_rows)
    delayed = class_counts[1]
    normal = class_counts[0]
    delayed_rate = (delayed / total_kept * 100) if total_kept else 0

    report = f"""인천공항 지연예측 1차 전처리 결과
====================================
입력 항공편: {source_rows:,}건
결항 제외(msDelay=2): {excluded_cancel:,}건
회항 제외(msDelay=3): {excluded_divert:,}건
날짜 파싱 실패: {bad_datetime:,}건
기상 매칭 실패(최대 {WEATHER_TOLERANCE_MIN}분): {weather_unmatched:,}건
최종 출력: {total_kept:,}건

정상(0): {normal:,}건
지연(1): {delayed:,}건
지연률: {delayed_rate:.2f}%

기상 매칭 age 평균: {age_mean:.2f}분
기상 매칭 age 95% 지점: {age_p95:.2f}분
기상 매칭 age 최대: {age_max:.2f}분

모델 입력 권장 컬럼
- airline_iata
- regular_type
- hour / weekday / is_weekend
- temperature / humidity / rainfall / visibility / pressure / wind_speed
- wind_dir_sin / wind_dir_cos
- (추후 팀원 A가 생성) departure_count_60m

모델 입력 제외 권장
- flight_key, flight_number: 식별용
- flight_date, scheduled_datetime, prediction_time: 분리/검증용
- weather_observation_time, weather_age_min: 데이터 품질 확인용
- wind_direction: sin/cos로 변환했으므로 중복 입력 불필요
- msDelay/delay_label: target 자체이므로 입력 금지
- Gate/Spot/msSid/collected_at: 시점 불확실/결측/상수 문제로 1차 모델 제외

다음 단계
1) 팀원 A의 departure_count_60m 및 EDA 결과를 이 파일에 합치기
2) scheduled_datetime 기준 시간순 Train/Test 분리
3) airline_iata는 Train 기준 OneHotEncoder(handle_unknown='ignore')
4) Logistic Regression / Random Forest / XGBoost 비교
5) 클래스 불균형은 class_weight 또는 scale_pos_weight로 처리 (SMOTE는 우선 사용하지 않음)
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"OUTPUT={OUTPUT_PATH}")
    print(f"REPORT={REPORT_PATH}")


if __name__ == "__main__":
    main()
