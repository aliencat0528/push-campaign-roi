-- Q 前置：載入原始 CSV、型別與衍生欄位。
-- 原始檔唯讀，任何清理只在 view 層做（CLAUDE.md 專案規則）。

CREATE OR REPLACE VIEW vRaw AS
SELECT * FROM read_csv_auto('data/raw/hillstrom.csv', header = true);

CREATE OR REPLACE VIEW vCustomers AS
SELECT
    row_number() OVER () AS customerId,
    recency,                                  -- 距上次購買月數
    history_segment AS historySegment,        -- 歷史消費分段（$0-$100 ... $1000+）
    history,                                  -- 歷史消費金額
    mens,                                     -- 過去 12 個月買過男裝
    womens,                                   -- 過去 12 個月買過女裝
    zip_code AS zipCode,
    newbie,                                   -- 近 12 個月新客
    channel,                                  -- Web / Phone / Multichannel
    segment,                                  -- 分組：Mens E-Mail / Womens E-Mail / No E-Mail
    (segment != 'No E-Mail')::INT AS treated, -- No E-Mail 恆為對照組
    visit,                                    -- 兩週內造訪
    conversion,                               -- 兩週內轉換
    spend                                     -- 兩週內消費金額（金額口徑，PC-001）
FROM vRaw;
