import os
import json
import math
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import pandas as pd
import requests


# ============================================================
# 0. 사용자 설정
# ============================================================

# 반드시 실제 인증키로 변경
DATA_GO_KR_KEY = os.environ.get("DATA_GO_KR_KEY", "")
KMA_API_KEY = os.environ.get("KMA_API_KEY", "")

# 인천공항 AMOS 지점번호
ICN_AMOS_STATION = "113"

# 현재 확보한 상세 API는 도착편 상세정보임.
# 보조자료로 계속 모으고 싶으면 True
COLLECT_ARRIVAL_DETAIL = True

# API 요청 사이 기본 대기시간
REQUEST_INTERVAL = 0.5


# ============================================================
# 1. 인증키 검사
# ============================================================

if (
    not DATA_GO_KR_KEY.strip()
    or "인증키" in DATA_GO_KR_KEY
):
    raise ValueError(
        "DATA_GO_KR_KEY에 실제 공공데이터포털 인증키를 입력하세요."
    )

if (
    not KMA_API_KEY.strip()
    or "인증키" in KMA_API_KEY
):
    raise ValueError(
        "KMA_API_KEY에 실제 기상청 API허브 인증키를 입력하세요."
    )


# Encoding 인증키를 넣었을 경우 처리
DATA_GO_KR_KEY = unquote(
    DATA_GO_KR_KEY
)


# ============================================================
# 2. 저장 폴더 설정
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent

BASE_DIR = (
    SCRIPT_DIR
    / "airport_project_data"
)

RAW_DIR = BASE_DIR / "raw"
LATEST_DIR = BASE_DIR / "latest"
CUMULATIVE_DIR = BASE_DIR / "cumulative"
LOG_DIR = BASE_DIR / "logs"

for folder in [
    RAW_DIR,
    LATEST_DIR,
    CUMULATIVE_DIR,
    LOG_DIR
]:
    folder.mkdir(
        parents=True,
        exist_ok=True
    )


# ============================================================
# 3. API URL
# ============================================================

CLOSING_URL = (
    "https://apis.data.go.kr/"
    "B551177/FlightClosingInfoSpot/"
    "getFlightClosingInfoSpot"
)

DETAIL_ARRIVAL_URL = (
    "https://apis.data.go.kr/"
    "B551177/statusOfAllFltDeOdp/"
    "getFltArrivalsDeOdp"
)

AMOS_URL = (
    "https://apihub.kma.go.kr/"
    "api/typ01/url/amos.php"
)


# ============================================================
# 4. 공통 함수
# ============================================================

def current_strings():

    now = datetime.now()

    return {
        "now": now,
        "date": now.strftime(
            "%Y%m%d"
        ),
        "datetime": now.strftime(
            "%Y%m%d_%H%M%S"
        )
    }


def write_log(message):

    now = datetime.now()

    log_path = (
        LOG_DIR
        / f"{now:%Y%m%d}.log"
    )

    line = (
        f"[{now:%Y-%m-%d %H:%M:%S}] "
        f"{message}"
    )

    print(line)

    with open(
        log_path,
        "a",
        encoding="utf-8"
    ) as f:
        f.write(
            line + "\n"
        )


def safe_request(
    url,
    params,
    label="API",
    timeout=30,
    max_retries=3
):
    """
    API 공통 요청 함수.

    자동 재시도:
    - HTTP 429
    - HTTP 500
    - HTTP 502
    - HTTP 503
    - HTTP 504
    - Timeout
    - ConnectionError

    인증키가 오류 로그 URL에
    노출되지 않도록 URL 자체는 출력하지 않음.
    """

    retry_codes = {
        429,
        500,
        502,
        503,
        504
    }

    for attempt in range(
        1,
        max_retries + 1
    ):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=timeout
            )

            # 정상
            if (
                response.status_code
                == 200
            ):
                return response

            # 재시도 가능한 서버 오류
            if (
                response.status_code
                in retry_codes
            ):

                if (
                    attempt
                    < max_retries
                ):

                    wait_seconds = (
                        2 ** attempt
                    )

                    write_log(
                        f"[RETRY] {label}: "
                        f"HTTP "
                        f"{response.status_code} "
                        f"({attempt}/"
                        f"{max_retries}) "
                        f"- {wait_seconds}초 후 "
                        f"재시도"
                    )

                    time.sleep(
                        wait_seconds
                    )

                    continue

                raise RuntimeError(
                    f"{label}: "
                    f"HTTP "
                    f"{response.status_code} "
                    f"오류가 "
                    f"{max_retries}회 "
                    f"연속 발생했습니다."
                )

            # 인증 오류 등
            raise RuntimeError(
                f"{label}: "
                f"HTTP "
                f"{response.status_code} "
                f"오류"
            )

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ):

            if (
                attempt
                < max_retries
            ):

                wait_seconds = (
                    2 ** attempt
                )

                write_log(
                    f"[RETRY] {label}: "
                    f"네트워크 오류 "
                    f"({attempt}/"
                    f"{max_retries}) "
                    f"- {wait_seconds}초 후 "
                    f"재시도"
                )

                time.sleep(
                    wait_seconds
                )

                continue

            raise RuntimeError(
                f"{label}: "
                f"네트워크 요청이 "
                f"{max_retries}회 "
                f"연속 실패했습니다."
            )

    raise RuntimeError(
        f"{label}: API 요청 실패"
    )


def save_json(
    data,
    path
):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    write_log(
        f"JSON 저장: "
        f"{path.resolve()}"
    )


def save_csv(
    df,
    path
):

    df.to_csv(
        path,
        index=False,
        encoding="utf-8-sig"
    )

    write_log(
        f"CSV 저장: "
        f"{path.resolve()}"
    )


def parse_public_data_json(
    data
):

    response_data = data.get(
        "response",
        data
    )

    header = response_data.get(
        "header",
        {}
    )

    body = response_data.get(
        "body",
        {}
    )

    result_code = str(
        header.get(
            "resultCode",
            ""
        )
    )

    result_message = header.get(
        "resultMsg",
        ""
    )

    if (
        result_code
        and result_code != "00"
    ):
        raise RuntimeError(
            f"API 응답 오류: "
            f"{result_code} / "
            f"{result_message}"
        )

    total_count = int(
        body.get(
            "totalCount",
            0
        )
    )

    items = body.get(
        "items",
        []
    )

    if isinstance(
        items,
        dict
    ):
        items = items.get(
            "item",
            []
        )

    if items is None:
        items = []

    if isinstance(
        items,
        dict
    ):
        items = [items]

    return (
        total_count,
        items
    )


# ============================================================
# 5. 누적 CSV 관리
# ============================================================

def upsert_csv(
    new_df,
    path,
    key_columns
):
    """
    신규 데이터를 기존 누적 CSV와 병합.

    key_columns가 동일한 행이 있으면
    새로 수집한 값이 기존 값을 대체함.
    """

    if new_df.empty:
        return new_df

    new_data = (
        new_df
        .copy()
        .fillna("")
        .astype(str)
    )

    if path.exists():

        old_data = pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False
        )

        combined = pd.concat(
            [
                old_data,
                new_data
            ],
            ignore_index=True
        )

    else:

        combined = new_data

    valid_keys = [
        column
        for column
        in key_columns
        if column
        in combined.columns
    ]

    if valid_keys:

        combined = (
            combined
            .drop_duplicates(
                subset=valid_keys,
                keep="last"
            )
            .reset_index(
                drop=True
            )
        )

    combined.to_csv(
        path,
        index=False,
        encoding="utf-8-sig"
    )

    write_log(
        f"누적 CSV 갱신: "
        f"{path.resolve()} "
        f"({len(combined)}건)"
    )

    return combined


# ============================================================
# 6. 운항마감정보
# ============================================================

def collect_flight_closing():

    write_log(
        "운항마감정보 수집 시작"
    )

    rows_per_page = 1000

    params = {
        "serviceKey":
            DATA_GO_KR_KEY,

        "type":
            "json",

        "numOfRows":
            rows_per_page,

        "pageNo":
            1
    }

    response = safe_request(
        CLOSING_URL,
        params,
        label="운항마감 API"
    )

    try:
        first_data = (
            response.json()
        )

    except Exception:

        raise RuntimeError(
            "운항마감 API 응답이 "
            "JSON 형식이 아닙니다."
        )

    (
        total_count,
        first_items
    ) = parse_public_data_json(
        first_data
    )

    write_log(
        f"운항마감 전체 건수: "
        f"{total_count}"
    )

    if total_count == 0:
        return pd.DataFrame()

    total_pages = math.ceil(
        total_count
        / rows_per_page
    )

    all_items = list(
        first_items
    )

    for page in range(
        2,
        total_pages + 1
    ):

        params["pageNo"] = page

        response = safe_request(
            CLOSING_URL,
            params,
            label=(
                "운항마감 API "
                f"{page}페이지"
            )
        )

        data = response.json()

        _, items = (
            parse_public_data_json(
                data
            )
        )

        all_items.extend(
            items
        )

        write_log(
            f"운항마감 "
            f"{page}/{total_pages}페이지 "
            f"누적 {len(all_items)}건"
        )

        time.sleep(
            REQUEST_INTERVAL
        )

    info = current_strings()

    # 원본 JSON
    json_path = (
        RAW_DIR
        / (
            "flight_closing_"
            f"{info['datetime']}.json"
        )
    )

    save_json(
        all_items,
        json_path
    )

    # DataFrame
    df = pd.DataFrame(
        all_items
    )

    df["collected_at"] = (
        info["now"].strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    # RAW CSV
    raw_csv_path = (
        RAW_DIR
        / (
            "flight_closing_"
            f"{info['datetime']}.csv"
        )
    )

    save_csv(
        df,
        raw_csv_path
    )

    # Latest
    latest_path = (
        LATEST_DIR
        / "flight_closing_latest.csv"
    )

    save_csv(
        df,
        latest_path
    )

    # 전체 누적
    upsert_csv(
        df,
        (
            CUMULATIVE_DIR
            / "flight_closing_all.csv"
        ),
        [
            "msDate",
            "msIo",
            "flightNum",
            "msStime"
        ]
    )

    # ========================================================
    # 프로젝트 대상 필터
    #
    # D = 출발
    # I = 국제선
    # mgUsecode 0 = 여객
    # ========================================================

    required_columns = {
        "msIo",
        "msLine",
        "mgUsecode"
    }

    if not required_columns.issubset(
        df.columns
    ):

        write_log(
            "프로젝트 필터에 필요한 "
            "컬럼이 없습니다."
        )

        return df

    project_df = df[
        (
            df["msIo"]
            .astype(str)
            == "D"
        )
        &
        (
            df["msLine"]
            .astype(str)
            == "I"
        )
        &
        (
            df["mgUsecode"]
            .astype(str)
            == "0"
        )
    ].copy()

    # 항공편명 앞 2자리에서 항공사 IATA 코드 추출
    project_df["airline_iata"] = (
        project_df["flightNum"]
        .astype(str)
        .str.strip()
        .str.extract(r"^([A-Z0-9]{2})", expand=False)
    )

    # 예정 출발 일시
    if {
        "msDate",
        "msStime"
    }.issubset(
        project_df.columns
    ):

        project_df[
            "scheduled_datetime"
        ] = pd.to_datetime(
            (
                project_df[
                    "msDate"
                ]
                .astype(str)
                +
                project_df[
                    "msStime"
                ]
                .astype(str)
                .str.zfill(4)
            ),
            format="%Y%m%d%H%M",
            errors="coerce"
        )

    # 지연 라벨
    if (
        "msDelay"
        in project_df.columns
    ):

        delay_map = {
            "0": "정상",
            "1": "지연",
            "2": "결항",
            "3": "회항"
        }

        project_df[
            "delay_label"
        ] = (
            project_df[
                "msDelay"
            ]
            .astype(str)
            .map(
                delay_map
            )
        )

    # 원본 프로젝트 필터 CSV
    project_raw_path = (
        RAW_DIR
        / (
            "flight_project_"
            f"{info['datetime']}.csv"
        )
    )

    save_csv(
        project_df,
        project_raw_path
    )

    # latest
    project_latest_path = (
        LATEST_DIR
        / "flight_project_latest.csv"
    )

    save_csv(
        project_df,
        project_latest_path
    )

    # 누적
    cumulative_project = (
        upsert_csv(
            project_df,
            (
                CUMULATIVE_DIR
                / "flight_project_all.csv"
            ),
            [
                "msDate",
                "msIo",
                "flightNum",
                "msStime"
            ]
        )
    )

    write_log(
        "출발 국제선 여객기 "
        f"오늘 {len(project_df)}건 / "
        f"누적 "
        f"{len(cumulative_project)}건"
    )

    return df


# ============================================================
# 7. 도착편 상세정보
# ============================================================

def collect_arrival_detail(
    search_date=None
):

    if not COLLECT_ARRIVAL_DETAIL:

        write_log(
            "도착 상세 수집 설정 OFF"
        )

        return pd.DataFrame()

    if search_date is None:

        search_date = (
            datetime.now()
            .strftime(
                "%Y%m%d"
            )
        )

    write_log(
        f"도착편 상세정보 "
        f"수집 시작: "
        f"{search_date}"
    )

    rows_per_page = 1000

    params = {
        "serviceKey":
            DATA_GO_KR_KEY,

        "pageNo":
            1,

        "numOfRows":
            rows_per_page,

        "searchdtCode":
            "S",

        "searchDate":
            search_date,

        "searchFrom":
            "0000",

        "searchTo":
            "2400",

        "passengerOrCargo":
            "P",

        "type":
            "json"
    }

    response = safe_request(
        DETAIL_ARRIVAL_URL,
        params,
        label="도착편 상세 API"
    )

    try:

        first_data = (
            response.json()
        )

    except Exception:

        raise RuntimeError(
            "도착편 상세 API 응답이 "
            "JSON이 아닙니다."
        )

    (
        total_count,
        first_items
    ) = parse_public_data_json(
        first_data
    )

    write_log(
        "도착편 상세정보 "
        f"전체 건수: "
        f"{total_count}"
    )

    if total_count == 0:
        return pd.DataFrame()

    total_pages = math.ceil(
        total_count
        / rows_per_page
    )

    all_items = list(
        first_items
    )

    for page in range(
        2,
        total_pages + 1
    ):

        params["pageNo"] = page

        response = safe_request(
            DETAIL_ARRIVAL_URL,
            params,
            label=(
                "도착 상세 API "
                f"{page}페이지"
            )
        )

        data = response.json()

        _, items = (
            parse_public_data_json(
                data
            )
        )

        all_items.extend(
            items
        )

        write_log(
            f"도착편 상세 "
            f"{page}/{total_pages} "
            f"누적 "
            f"{len(all_items)}건"
        )

        time.sleep(
            REQUEST_INTERVAL
        )

    info = current_strings()

    df = pd.DataFrame(
        all_items
    )

    df["collected_at"] = (
        info["now"].strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    json_path = (
        RAW_DIR
        / (
            "arrival_detail_"
            f"{search_date}_"
            f"{info['datetime']}.json"
        )
    )

    csv_path = (
        RAW_DIR
        / (
            "arrival_detail_"
            f"{search_date}_"
            f"{info['datetime']}.csv"
        )
    )

    latest_path = (
        LATEST_DIR
        / "arrival_detail_latest.csv"
    )

    save_json(
        all_items,
        json_path
    )

    save_csv(
        df,
        csv_path
    )

    save_csv(
        df,
        latest_path
    )

    if (
        "fid"
        in df.columns
    ):

        upsert_csv(
            df,
            (
                CUMULATIVE_DIR
                / "arrival_detail_all.csv"
            ),
            ["fid"]
        )

    if (
        "remark"
        in df.columns
    ):

        print(
            "\n[도착 상세 remark 분포]"
        )

        print(
            df[
                "remark"
            ].value_counts(
                dropna=False
            )
        )

    return df


# ============================================================
# 8. AMOS 컬럼
# ============================================================

AMOS_COLUMNS = [
    "station_id",
    "observation_time",

    "left_visibility",
    "right_visibility",

    "left_rvr",
    "right_rvr",

    "cloud_base_height",

    "temperature",
    "dew_point",
    "humidity",

    "sea_level_pressure",
    "station_pressure",

    "rainfall",

    "reserved_1",
    "reserved_2",

    "wind_dir_2min",
    "wind_dir_2min_max",
    "wind_dir_2min_min",

    "wind_speed_2min",
    "wind_speed_2min_max",
    "wind_speed_2min_min",

    "wind_dir_10min",
    "wind_dir_10min_max",
    "wind_dir_10min_min",

    "wind_speed_10min",
    "wind_speed_10min_max",
    "wind_speed_10min_min"
]


# ============================================================
# 9. AMOS 텍스트 파서
# ============================================================

def parse_amos_text(
    text
):

    rows = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        values = line.split()

        if (
            len(values)
            < len(
                AMOS_COLUMNS
            )
        ):
            continue

        rows.append(
            values[
                :len(
                    AMOS_COLUMNS
                )
            ]
        )

    df = pd.DataFrame(
        rows,
        columns=AMOS_COLUMNS
    )

    if df.empty:
        return df

    numeric_columns = [
        column
        for column
        in AMOS_COLUMNS
        if column not in {
            "station_id",
            "observation_time"
        }
    ]

    for column in numeric_columns:

        df[column] = (
            pd.to_numeric(
                df[column],
                errors="coerce"
            )
        )

        # 기상청 결측코드
        df.loc[
            df[column]
            <= -99990,
            column
        ] = float("nan")

    df[
        "observation_time"
    ] = pd.to_datetime(
        df[
            "observation_time"
        ],
        format="%Y%m%d%H%M",
        errors="coerce"
    )

    # 0.1 단위 → 실제 단위
    scale_columns = [
        "temperature",
        "dew_point",

        "sea_level_pressure",
        "station_pressure",

        "rainfall",

        "wind_speed_2min",
        "wind_speed_2min_max",
        "wind_speed_2min_min",

        "wind_speed_10min",
        "wind_speed_10min_max",
        "wind_speed_10min_min"
    ]

    for column in scale_columns:

        df[column] = (
            df[column]
            / 10.0
        )

    # API 자체 중복 제거
    df = (
        df
        .drop_duplicates(
            subset=[
                "station_id",
                "observation_time"
            ],
            keep="last"
        )
        .sort_values(
            "observation_time"
        )
        .reset_index(
            drop=True
        )
    )

    return df


# ============================================================
# 10. AMOS 하루 전체 수집
# ============================================================

def collect_amos_day(
    target_date=None
):

    now = datetime.now()

    if target_date is None:

        target_date = (
            now.strftime(
                "%Y%m%d"
            )
        )

    today = (
        now.strftime(
            "%Y%m%d"
        )
    )

    query_times = []

    # 오늘 자료
    if target_date == today:

        current_hour = now.hour

        # 끝난 시간
        for hour in range(
            current_hour
        ):

            query_times.append(
                f"{target_date}"
                f"{hour:02d}59"
            )

        # 현재 시간
        query_times.append(
            now.strftime(
                "%Y%m%d%H%M"
            )
        )

    # 과거 날짜 자료
    else:

        for hour in range(24):

            query_times.append(
                f"{target_date}"
                f"{hour:02d}59"
            )

    write_log(
        f"AMOS 하루자료 수집 시작: "
        f"{target_date} / "
        f"{len(query_times)}회 요청"
    )

    all_frames = []
    raw_blocks = []

    for index, tm in enumerate(
        query_times,
        start=1
    ):

        params = {
            "tm":
                tm,

            "dtm":
                60,

            "stn":
                ICN_AMOS_STATION,

            "help":
                0,

            "authKey":
                KMA_API_KEY
        }

        try:

            response = safe_request(
                AMOS_URL,
                params,
                label=(
                    f"AMOS {tm}"
                ),
                timeout=30,
                max_retries=3
            )

            raw_text = (
                response.text
            )

            raw_blocks.append(
                (
                    f"\n"
                    f"===== tm={tm} =====\n"
                    f"{raw_text}"
                )
            )

            temp_df = (
                parse_amos_text(
                    raw_text
                )
            )

            if not temp_df.empty:

                all_frames.append(
                    temp_df
                )

            write_log(
                f"AMOS "
                f"{index}/"
                f"{len(query_times)} "
                f"완료: {tm}"
            )

        except Exception as e:

            write_log(
                f"[WARNING] "
                f"AMOS {tm} "
                f"최종 실패: {e}"
            )

        time.sleep(
            REQUEST_INTERVAL
        )

    if not all_frames:

        write_log(
            "AMOS 데이터 없음"
        )

        return pd.DataFrame()

    df = pd.concat(
        all_frames,
        ignore_index=True
    )

    before = len(df)

    df = (
        df
        .drop_duplicates(
            subset=[
                "station_id",
                "observation_time"
            ],
            keep="last"
        )
        .sort_values(
            "observation_time"
        )
        .reset_index(
            drop=True
        )
    )

    # 해당 날짜만 남김
    df = df[
        (
            df[
                "observation_time"
            ]
            .dt.strftime(
                "%Y%m%d"
            )
            == target_date
        )
    ].copy()

    after = len(df)

    write_log(
        f"AMOS 중복 제거: "
        f"{before} → "
        f"{after}건"
    )

    info = current_strings()

    # 원본 TXT
    raw_txt_path = (
        RAW_DIR
        / (
            "amos_raw_"
            f"{target_date}_"
            f"{info['datetime']}.txt"
        )
    )

    with open(
        raw_txt_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "\n".join(
                raw_blocks
            )
        )

    write_log(
        f"AMOS 원본 저장: "
        f"{raw_txt_path.resolve()}"
    )

    # RAW 정제 CSV
    csv_path = (
        RAW_DIR
        / (
            "weather_"
            f"{target_date}_"
            f"{info['datetime']}.csv"
        )
    )

    save_csv(
        df,
        csv_path
    )

    # 최신
    latest_path = (
        LATEST_DIR
        / "weather_latest.csv"
    )

    save_csv(
        df,
        latest_path
    )

    # 누적
    cumulative_df = (
        upsert_csv(
            df,
            (
                CUMULATIVE_DIR
                / "weather_all.csv"
            ),
            [
                "station_id",
                "observation_time"
            ]
        )
    )

    # 확인용
    show_columns = [
        "observation_time",
        "temperature",
        "humidity",
        "rainfall",
        "wind_speed_10min",
        "left_visibility",
        "sea_level_pressure"
    ]

    print(
        "\n[정제된 AMOS 최근 10건]"
    )

    print(
        df[
            show_columns
        ]
        .tail(10)
        .to_string(
            index=False
        )
    )

    write_log(
        f"오늘 AMOS: "
        f"{len(df)}건 / "
        f"전체 누적 "
        f"{len(cumulative_df)}건"
    )

    return df


# ============================================================
# 11. 전체 실행
# ============================================================

def _run_all_impl():

    print()
    print("=" * 70)
    print("저장 기본 폴더")
    print(
        BASE_DIR.resolve()
    )
    print("=" * 70)
    print()

    write_log(
        "=" * 60
    )

    write_log(
        "인천공항 데이터 "
        "수집 작업 시작"
    )

    # 반드시 먼저 초기화
    closing_df = (
        pd.DataFrame()
    )

    arrival_detail_df = (
        pd.DataFrame()
    )

    weather_df = (
        pd.DataFrame()
    )

    # --------------------------------------------------------
    # 운항마감
    # --------------------------------------------------------

    try:

        closing_df = (
            collect_flight_closing()
        )

    except Exception as e:

        write_log(
            f"[ERROR] "
            f"운항마감 실패: "
            f"{e}"
        )

    # --------------------------------------------------------
    # 도착 상세
    # --------------------------------------------------------

    try:

        arrival_detail_df = (
            collect_arrival_detail()
        )

    except Exception as e:

        write_log(
            f"[ERROR] "
            f"도착 상세 실패: "
            f"{e}"
        )

    # --------------------------------------------------------
    # AMOS
    # --------------------------------------------------------

    try:

        weather_df = (
            collect_amos_day()
        )

    except Exception as e:

        write_log(
            f"[ERROR] "
            f"AMOS 실패: "
            f"{e}"
        )

    # --------------------------------------------------------
    # 실행 결과
    # --------------------------------------------------------

    write_log(
        "-" * 60
    )

    write_log(
        "오늘 수집 결과"
    )

    write_log(
        f"운항마감: "
        f"{len(closing_df)}건"
    )

    write_log(
        f"도착 상세: "
        f"{len(arrival_detail_df)}건"
    )

    write_log(
        f"기상자료: "
        f"{len(weather_df)}건"
    )

    write_log(
        "인천공항 데이터 "
        "수집 작업 종료"
    )

    write_log(
        "=" * 60
    )

    print()
    print("=" * 70)
    print("CSV 파일 위치")
    print("=" * 70)

    print(
        "\n[최신 파일]"
    )

    print(
        LATEST_DIR.resolve()
    )

    print(
        "\n[누적 파일]"
    )

    print(
        CUMULATIVE_DIR.resolve()
    )

    print(
        "\n[원본 파일]"
    )

    print(
        RAW_DIR.resolve()
    )

# ============================================================
# 12. 수동/자동 공용 실행 잠금
# ============================================================

# 수동 실행과 자동 실행이 동시에 시작되는 것을 방지합니다.
# 비정상 종료로 잠금파일이 남더라도 3시간 이상 지난 파일은
# 오래된 잠금으로 판단해 자동으로 정리합니다.
LOCK_PATH = BASE_DIR / "collection.lock"
LOCK_STALE_SECONDS = 3 * 60 * 60


def acquire_collection_lock(source="manual"):
    if LOCK_PATH.exists():
        try:
            age_seconds = (
                datetime.now().timestamp()
                - LOCK_PATH.stat().st_mtime
            )

            if age_seconds > LOCK_STALE_SECONDS:
                write_log(
                    "[WARNING] 오래된 collection.lock을 삭제합니다."
                )
                LOCK_PATH.unlink(missing_ok=True)

        except Exception as e:
            write_log(
                f"[WARNING] 잠금파일 상태 확인 실패: {e}"
            )

    try:
        with open(
            LOCK_PATH,
            "x",
            encoding="utf-8"
        ) as f:
            f.write(
                f"source={source}\n"
                f"started_at={datetime.now():%Y-%m-%d %H:%M:%S}\n"
            )

        return True

    except FileExistsError:
        write_log(
            f"[SKIP] 이미 다른 수집 작업이 실행 중입니다. "
            f"요청 실행 방식: {source}"
        )
        return False


def release_collection_lock():
    try:
        LOCK_PATH.unlink(missing_ok=True)
    except Exception as e:
        write_log(
            f"[WARNING] 잠금파일 삭제 실패: {e}"
        )


def run_all(source="manual"):
    """
    수동/자동 실행이 공통으로 호출하는 진입점입니다.

    source:
        "manual" - 사용자가 직접 실행
        "auto"   - Windows 작업 스케줄러에서 실행
    """

    if not acquire_collection_lock(source):
        return False

    try:
        write_log(
            f"실행 방식: {source}"
        )

        _run_all_impl()
        return True

    finally:
        release_collection_lock()
