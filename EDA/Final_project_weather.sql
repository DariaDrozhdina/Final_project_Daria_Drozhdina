-- Adding missing values for weather from another table 

UPDATE england_weather ew
SET tsun = eew.sun_min
FROM england_exta_weather_sun eew
WHERE 
    LEFT(ew.date, 7) = eew."Year"
    AND ew.station_name = eew.city
    AND ew.tsun IS NULL;


UPDATE england_weather ew
SET prcp = eew.rain_mm
FROM england_exta_weather_sun eew
WHERE 
    LEFT(ew.date, 7) = eew."Year"
    AND ew.station_name = eew.city
    AND ew.prcp IS NULL;
 
-- Creating a new table with both England and Spain

CREATE TABLE all_weather AS
SELECT * FROM england_weather
UNION ALL
SELECT * FROM spain_weather;

-- Calculating avarages for some missing values 

CREATE TABLE all_weather_clean AS
SELECT 
    ew.date,
    ew.tavg,
    ew.tmin,
    ew.tmax,
    COALESCE(ew.prcp, avg_data.avg_prcp) as prcp,
    ew.wspd,
    ew.pres,
    COALESCE(ew.tsun, avg_data.avg_tsun) as tsun,
    ew.station_id,
    ew.station_name
FROM all_weather ew
LEFT JOIN (
    SELECT 
        station_name,
        EXTRACT(MONTH FROM date::timestamp) as month,
        AVG(tsun) as avg_tsun,
        AVG(prcp) as avg_prcp
    FROM all_weather
    WHERE tsun IS NOT NULL OR prcp IS NOT NULL
    GROUP BY station_name, EXTRACT(MONTH FROM date::timestamp)
) avg_data 
ON ew.station_name = avg_data.station_name
AND EXTRACT(MONTH FROM ew.date::timestamp) = avg_data.month;

-- Rounding the numbers 

UPDATE all_weather_clean
SET 
    tsun = ROUND(tsun::numeric),
    prcp = ROUND(prcp::numeric);

-- More avarages for temperatur 

UPDATE all_weather_clean ew
SET 
    tavg = ROUND(((prev.tavg + next.tavg) / 2)::numeric, 1),
    tmin = ROUND(((prev.tmin + next.tmin) / 2)::numeric, 1),
    tmax = ROUND(((prev.tmax + next.tmax) / 2)::numeric, 1),
FROM all_weather_clean prev
JOIN all_weather_clean next
    ON prev.station_name = next.station_name
WHERE ew.station_name = prev.station_name
AND prev.date::timestamp = (ew.date::timestamp - INTERVAL '1 month')
AND next.date::timestamp = (ew.date::timestamp + INTERVAL '1 month')
AND prev.tavg IS NOT NULL 
AND next.tavg IS NOT NULL
AND ew.tavg IS NULL;

-- Deleting unnecesary columns 

ALTER TABLE all_weather_clean 
DROP COLUMN wspd,
DROP COLUMN station_id;

-- Changin date format for year and month 


UPDATE all_weather_clean
SET date = LEFT(date, 7);

-- Changin formats for numeric values just in case 

ALTER TABLE all_weather_clean
ALTER COLUMN tavg TYPE FLOAT USING tavg::float,
ALTER COLUMN tmin TYPE FLOAT USING tmin::float,
ALTER COLUMN tmax TYPE FLOAT USING tmax::float,
ALTER COLUMN prcp TYPE FLOAT USING prcp::float,
ALTER COLUMN pres TYPE FLOAT USING pres::float,
ALTER COLUMN tsun TYPE FLOAT USING tsun::float;

UPDATE all_weather_clean
SET 
    tavg = ROUND(tavg::numeric, 1),
    tmin = ROUND(tmin::numeric, 1),
    tmax = ROUND(tmax::numeric, 1),
    prcp = ROUND(prcp::numeric, 1),
    pres = ROUND(pres::numeric, 1),
    tsun = ROUND(tsun::numeric, 1);