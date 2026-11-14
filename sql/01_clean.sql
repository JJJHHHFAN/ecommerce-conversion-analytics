-- All event times are UTC. transactionid is expected to be NULL for non-purchases.
CREATE OR REPLACE TABLE events_clean AS
SELECT DISTINCT
    TRY_CAST(timestamp AS BIGINT) AS timestamp_ms,
    TRY_CAST(visitorid AS BIGINT) AS visitorid,
    event,
    TRY_CAST(itemid AS BIGINT) AS itemid,
    TRY_CAST(transactionid AS BIGINT) AS transactionid,
    to_timestamp(TRY_CAST(timestamp AS DOUBLE) / 1000) AS event_time
FROM read_csv('data/raw/events.csv', header=true, all_varchar=true)
WHERE TRY_CAST(timestamp AS BIGINT) IS NOT NULL
  AND TRY_CAST(visitorid AS BIGINT) IS NOT NULL
  AND TRY_CAST(itemid AS BIGINT) IS NOT NULL
  AND event IN ('view', 'addtocart', 'transaction');

COPY events_clean TO 'data/processed/events_clean.parquet' (FORMAT PARQUET);
