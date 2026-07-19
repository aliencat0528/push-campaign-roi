-- Q 前置（信度關卡）：SRM 樣本比例檢核 + 共變數平衡表。
-- 設計比例 1/3 : 1/3 : 1/3；SRM 卡方 p < 0.01 → pipeline 中止不出報告（CLAUDE.md 防呆）。

CREATE OR REPLACE TABLE t01GroupCounts AS
SELECT segment, count(*) AS n
FROM vCustomers
GROUP BY segment
ORDER BY segment;

CREATE OR REPLACE TABLE t01Balance AS
SELECT
    segment,
    count(*) AS n,
    round(avg(recency), 3) AS avgRecency,
    round(avg(history), 2) AS avgHistory,
    round(avg(mens), 4) AS shareMens,
    round(avg(womens), 4) AS shareWomens,
    round(avg(newbie), 4) AS shareNewbie,
    round(avg((channel = 'Web')::INT), 4) AS shareWeb,
    round(avg((channel = 'Phone')::INT), 4) AS sharePhone,
    round(avg((channel = 'Multichannel')::INT), 4) AS shareMulti
FROM vCustomers
GROUP BY segment
ORDER BY segment;
