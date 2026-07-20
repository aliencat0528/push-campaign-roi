-- Q1（增量底座）：各組矩統計，供兩比例 z 檢定 / Welch t / MDE 使用（src/stats.py）。
-- 增量一律「實驗組 − No E-Mail 對照組」，檢定在 Python 層做。

CREATE OR REPLACE TABLE t03Arms AS
SELECT
    segment,
    count(*) AS n,
    sum(visit) AS visits,
    sum(conversion) AS conversions,
    avg(spend) AS meanSpend,
    var_samp(spend) AS varSpend
FROM vCustomers
GROUP BY segment;
