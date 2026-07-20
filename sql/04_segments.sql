-- Q2：分群 × 組矩統計。維度：recency 桶 / 歷史消費段 / 新客 / 渠道。
-- 分群層檢定用「合併實驗組（任一 email）vs 對照」保檢定力，合併矩在 src/analysis.py。

CREATE OR REPLACE TABLE t04Segments AS
WITH base AS (
    SELECT
        segment,
        spend,
        conversion,
        CASE WHEN recency <= 3 THEN '1-3 月' WHEN recency <= 6 THEN '4-6 月'
             WHEN recency <= 9 THEN '7-9 月' ELSE '10-12 月' END AS recencyBucket,
        historySegment,
        CASE newbie WHEN 1 THEN '新客' ELSE '舊客' END AS newbieFlag,
        channel
    FROM vCustomers
)
SELECT 'recency' AS dim, recencyBucket AS dimValue, segment,
       count(*) AS n, sum(conversion) AS conversions,
       avg(spend) AS meanSpend, var_samp(spend) AS varSpend
FROM base GROUP BY dimValue, segment
UNION ALL
SELECT 'historySegment', historySegment, segment,
       count(*), sum(conversion), avg(spend), var_samp(spend)
FROM base GROUP BY historySegment, segment
UNION ALL
SELECT 'newbie', newbieFlag, segment,
       count(*), sum(conversion), avg(spend), var_samp(spend)
FROM base GROUP BY newbieFlag, segment
UNION ALL
SELECT 'channel', channel, segment,
       count(*), sum(conversion), avg(spend), var_samp(spend)
FROM base GROUP BY channel, segment;
