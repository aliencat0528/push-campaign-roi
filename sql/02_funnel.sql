-- Q1（漏斗底座）：各組漏斗指標。
-- 資料無送達/開啟欄 → sent ≈ delivered，漏斗上半段缺口見報告限制章節。

CREATE OR REPLACE TABLE t02Funnel AS
SELECT
    segment,
    count(*) AS n,
    sum(visit) AS visits,
    round(avg(visit), 4) AS visitRate,
    sum(conversion) AS conversions,
    round(avg(conversion), 4) AS convRate,
    round(sum(spend), 2) AS totalSpend,
    round(avg(spend), 4) AS spendPerCustomer,
    round(sum(spend) / nullif(sum(conversion), 0), 2) AS spendPerConverter,
    round(1000.0 * sum(spend) / count(*), 2) AS revenuePer1000Sent
FROM vCustomers
GROUP BY segment
ORDER BY segment;
