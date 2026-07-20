-- Q1/Q3：ROI 輸入彙整。金額計算與退訂敏感度在 src/roi.py（商業參數見 src/params.py）。

CREATE OR REPLACE TABLE t05RoiInputs AS
SELECT
    segment,
    n,
    meanSpend,
    varSpend,
    n * meanSpend AS totalSpend
FROM t03Arms;
