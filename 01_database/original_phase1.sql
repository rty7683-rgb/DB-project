--------------------------------------------------------
-- 0. 기존 테이블 삭제 (초기화)
--------------------------------------------------------
DROP TABLE MODEL_RESULT CASCADE CONSTRAINTS PURGE;
DROP TABLE FLIGHT_WEATHER CASCADE CONSTRAINTS PURGE;
DROP TABLE FLIGHT_OPERATION CASCADE CONSTRAINTS PURGE;
DROP TABLE FLIGHT CASCADE CONSTRAINTS PURGE;
DROP TABLE WEATHER CASCADE CONSTRAINTS PURGE;
DROP TABLE AIRLINE CASCADE CONSTRAINTS PURGE;


--------------------------------------------------------
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
-- 2. 샘플 데이터 입력 (DML 4건)
--------------------------------------------------------

-- 2-1. 항공사 (AIRLINE) 4건
INSERT INTO AIRLINE VALUES ('KAL', '대한항공');
INSERT INTO AIRLINE VALUES ('AAR', '아시아나항공');
INSERT INTO AIRLINE VALUES ('JNA', '진에어');
INSERT INTO AIRLINE VALUES ('JJA', '제주항공');

-- 2-2. 기상 정보 (WEATHER) 4건
INSERT INTO WEATHER VALUES (101, 'RKSI', TO_TIMESTAMP('2026-10-01 10:00:00', 'YYYY-MM-DD HH24:MI:SS'), 22.5, 65.0, 0.0, 10000.0, 1013.25, 4.5, 180.0);
INSERT INTO WEATHER VALUES (102, 'RKSI', TO_TIMESTAMP('2026-10-01 11:00:00', 'YYYY-MM-DD HH24:MI:SS'), 20.0, 50.0, 0.0, 10000.0, 1015.00, 2.1, 120.0);
INSERT INTO WEATHER VALUES (103, 'RKSI', TO_TIMESTAMP('2026-10-01 14:00:00', 'YYYY-MM-DD HH24:MI:SS'), 18.5, 90.0, 15.5, 3000.0, 1005.10, 9.8, 270.0);
INSERT INTO WEATHER VALUES (104, 'RKSI', TO_TIMESTAMP('2026-10-01 16:00:00', 'YYYY-MM-DD HH24:MI:SS'), 19.2, 55.0, 0.0, 10000.0, 1012.80, 3.2, 150.0);
COMMIT;

-- 2-3. 운항 스케줄 (FLIGHT) 4건
INSERT INTO FLIGHT VALUES ('FL20261001_001', 'KAL', 'KE081', TO_DATE('2026-10-01', 'YYYY-MM-DD'), TO_TIMESTAMP('2026-10-01 10:30:00', 'YYYY-MM-DD HH24:MI:SS'), 'OUT', 'INT', 'REG', 'PAS', 'Y');
INSERT INTO FLIGHT VALUES ('FL20261001_002', 'AAR', 'OZ102', TO_DATE('2026-10-01', 'YYYY-MM-DD'), TO_TIMESTAMP('2026-10-01 11:10:00', 'YYYY-MM-DD HH24:MI:SS'), 'OUT', 'INT', 'REG', 'PAS', 'Y');
INSERT INTO FLIGHT VALUES ('FL20261001_003', 'JNA', 'LJ055', TO_DATE('2026-10-01', 'YYYY-MM-DD'), TO_TIMESTAMP('2026-10-01 14:15:00', 'YYYY-MM-DD HH24:MI:SS'), 'OUT', 'DOM', 'REG', 'PAS', 'Y');
INSERT INTO FLIGHT VALUES ('FL20261001_004', 'JJA', '7C105', TO_DATE('2026-10-01', 'YYYY-MM-DD'), TO_TIMESTAMP('2026-10-01 16:40:00', 'YYYY-MM-DD HH24:MI:SS'), 'OUT', 'DOM', 'REG', 'PAS', 'Y');

-- 2-4. 운항 현황 (FLIGHT_OPERATION) 4건
INSERT INTO FLIGHT_OPERATION VALUES (1, 'FL20261001_001', 'DELAY', 'D01', 'G12', 'S05', TO_TIMESTAMP('2026-10-01 10:45:00', 'YYYY-MM-DD HH24:MI:SS'));
INSERT INTO FLIGHT_OPERATION VALUES (2, 'FL20261001_002', 'ONTIME', NULL, 'G08', 'S02', TO_TIMESTAMP('2026-10-01 11:10:00', 'YYYY-MM-DD HH24:MI:SS'));
INSERT INTO FLIGHT_OPERATION VALUES (3, 'FL20261001_003', 'DELAY', 'D03', 'G22', 'S11', TO_TIMESTAMP('2026-10-01 14:50:00', 'YYYY-MM-DD HH24:MI:SS'));
INSERT INTO FLIGHT_OPERATION VALUES (4, 'FL20261001_004', 'ONTIME', NULL, 'G15', 'S07', TO_TIMESTAMP('2026-10-01 16:40:00', 'YYYY-MM-DD HH24:MI:SS'));

-- 2-5. 기상 매핑 (FLIGHT_WEATHER) 4건
INSERT INTO FLIGHT_WEATHER VALUES (1, 'FL20261001_001', 101, '10:00');
INSERT INTO FLIGHT_WEATHER VALUES (2, 'FL20261001_002', 102, '11:00');
INSERT INTO FLIGHT_WEATHER VALUES (3, 'FL20261001_003', 103, '14:00');
INSERT INTO FLIGHT_WEATHER VALUES (4, 'FL20261001_004', 104, '16:00');

-- 2-6. 예측 및 실제 결과 (MODEL_RESULT) 4건
INSERT INTO MODEL_RESULT VALUES (1, 'FL20261001_001', 'XGBoost_v2', TO_TIMESTAMP('2026-10-01 09:00:00', 'YYYY-MM-DD HH24:MI:SS'), 0.8520, 'DELAY', 'DELAY', SYSTIMESTAMP);
INSERT INTO MODEL_RESULT VALUES (2, 'FL20261001_002', 'XGBoost_v2', TO_TIMESTAMP('2026-10-01 10:00:00', 'YYYY-MM-DD HH24:MI:SS'), 0.1200, 'ONTIME', 'ONTIME', SYSTIMESTAMP);
INSERT INTO MODEL_RESULT VALUES (3, 'FL20261001_003', 'XGBoost_v2', TO_TIMESTAMP('2026-10-01 13:00:00', 'YYYY-MM-DD HH24:MI:SS'), 0.9410, 'DELAY', 'DELAY', SYSTIMESTAMP);
INSERT INTO MODEL_RESULT VALUES (4, 'FL20261001_004', 'XGBoost_v2', TO_TIMESTAMP('2026-10-01 15:00:00', 'YYYY-MM-DD HH24:MI:SS'), 0.1850, 'ONTIME', 'ONTIME', SYSTIMESTAMP);

-- DB에 영구 반영
COMMIT;


--------------------------------------------------------
-- 3. 최종 검증 조인 조회 쿼리 
--------------------------------------------------------
SELECT
    f.flight_id AS 운항ID,
    a.airline_name AS 항공사,
    f.flight_number AS 편명,
    fo.Status_code AS 운항상태,
    w.temperature AS 기온,
    w.rainfall AS 강수량,
    w.wind_direction AS 풍향,
    mr.delay_probability AS 지연확률,
    mr.predicted_label AS 예측결과,
    mr.actual_label AS 실제결과
FROM FLIGHT f
JOIN AIRLINE a ON f.airline_code = a.airline_code
LEFT JOIN FLIGHT_OPERATION fo ON f.flight_id = fo.flight_id
LEFT JOIN FLIGHT_WEATHER fw ON f.flight_id = fw.flight_id
LEFT JOIN WEATHER w ON fw.weather_id = w.weather_id
LEFT JOIN MODEL_RESULT mr ON f.flight_id = mr.flight_id
ORDER BY f.flight_id;
