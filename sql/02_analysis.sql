-- Run after 01_clean.sql. Event counts are distinct from ordered visitor funnels.
SELECT event, COUNT(*) AS event_count, COUNT(DISTINCT visitorid) AS visitors
FROM events_clean GROUP BY event ORDER BY event_count DESC;

SELECT CAST(event_time AS DATE) AS event_date, event, COUNT(*) AS events
FROM events_clean GROUP BY 1, 2 ORDER BY 1, 2;

SELECT COUNT(*) AS clean_events, COUNT(DISTINCT visitorid) AS visitors,
       COUNT(DISTINCT itemid) AS items, MIN(event_time) AS first_utc,
       MAX(event_time) AS last_utc
FROM events_clean;
