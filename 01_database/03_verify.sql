-- 1단계 원본 JOIN 조회 + 테이블별 건수 확인.
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

SELECT 'AIRLINE' AS table_name, COUNT(*) AS row_count FROM AIRLINE
UNION ALL SELECT 'WEATHER', COUNT(*) FROM WEATHER
UNION ALL SELECT 'FLIGHT', COUNT(*) FROM FLIGHT
UNION ALL SELECT 'FLIGHT_OPERATION', COUNT(*) FROM FLIGHT_OPERATION
UNION ALL SELECT 'FLIGHT_WEATHER', COUNT(*) FROM FLIGHT_WEATHER
UNION ALL SELECT 'MODEL_RESULT', COUNT(*) FROM MODEL_RESULT;
