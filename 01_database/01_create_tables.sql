-- 1단계 팀원 원본 DDL에서 분리. 빈 스키마에서만 실행.
-- 1. 테이블 생성 (DDL)
--------------------------------------------------------

-- 1-1. 항공사 정보 (AIRLINE)
CREATE TABLE AIRLINE (
    airline_code VARCHAR2(10)  NOT NULL,
    airline_name VARCHAR2(100) NOT NULL,
    CONSTRAINT PK_AIRLINE PRIMARY KEY (airline_code)
);

-- 1-2. 기상 정보 (WEATHER)
CREATE TABLE WEATHER (
    weather_id       NUMBER       NOT NULL,
    station_id       VARCHAR2(20) NOT NULL,
    observation_time TIMESTAMP    NOT NULL,
    temperature      NUMBER(5,2),
    humidity         NUMBER(5,2),
    rainfall         NUMBER(5,2),
    visibility       NUMBER(8,2),
    pressure         NUMBER(6,2),
    wind_speed       NUMBER(5,2),
    wind_direction   NUMBER(5,2),
    CONSTRAINT PK_WEATHER PRIMARY KEY (weather_id)
);

-- 1-3. 항공 운항 정보 (FLIGHT)
CREATE TABLE FLIGHT (
    flight_id          VARCHAR2(50) NOT NULL,
    airline_code       VARCHAR2(10) NOT NULL,
    flight_number      VARCHAR2(20) NOT NULL,
    flight_date        DATE         NOT NULL,
    scheduled_datetime TIMESTAMP    NOT NULL,
    direction          VARCHAR2(10),
    line_type          VARCHAR2(10),
    regular_type       VARCHAR2(10),
    use_code           VARCHAR2(10),
    passenger_yn       CHAR(1),
    CONSTRAINT PK_FLIGHT PRIMARY KEY (flight_id),
    CONSTRAINT FK_FLIGHT_AIRLINE FOREIGN KEY (airline_code) REFERENCES AIRLINE(airline_code)
);

-- 1-4. 운항 현황 (FLIGHT_OPERATION)
CREATE TABLE FLIGHT_OPERATION (
    operation_id NUMBER       NOT NULL,
    flight_id    VARCHAR2(50) NOT NULL,
    Status_code  VARCHAR2(10),
    Delay_code   VARCHAR2(10),
    Gate         VARCHAR2(10),
    Spot         VARCHAR2(10),
    collected_at TIMESTAMP,
    CONSTRAINT PK_FLIGHT_OPERATION PRIMARY KEY (operation_id),
    CONSTRAINT FK_FO_FLIGHT FOREIGN KEY (flight_id) REFERENCES FLIGHT(flight_id),
    CONSTRAINT UQ_FO_FLIGHT UNIQUE (flight_id)
);

-- 1-5. 운항별 기상 정보 매핑 (FLIGHT_WEATHER)
CREATE TABLE FLIGHT_WEATHER (
    flight_weather_id NUMBER       NOT NULL,
    flight_id         VARCHAR2(50) NOT NULL,
    weather_id        NUMBER       NOT NULL,
    prediction_time   VARCHAR2(20) NOT NULL,
    CONSTRAINT PK_FLIGHT_WEATHER PRIMARY KEY (flight_weather_id),
    CONSTRAINT FK_FW_FLIGHT FOREIGN KEY (flight_id) REFERENCES FLIGHT(flight_id),
    CONSTRAINT FK_FW_WEATHER FOREIGN KEY (weather_id) REFERENCES WEATHER(weather_id)
);

-- 1-6. 지연 예측 모델 결과 (MODEL_RESULT)
CREATE TABLE MODEL_RESULT (
    result_id         NUMBER       NOT NULL,
    flight_id         VARCHAR2(50) NOT NULL,
    model_name        VARCHAR2(50) NOT NULL,
    prediction_time   TIMESTAMP    NOT NULL,
    delay_probability NUMBER(5,4),
    predicted_label   VARCHAR2(10),
    actual_label      VARCHAR2(10),
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT PK_MODEL_RESULT PRIMARY KEY (result_id),
    CONSTRAINT FK_MR_FLIGHT FOREIGN KEY (flight_id) REFERENCES FLIGHT(flight_id)
);


--------------------------------------------------------
