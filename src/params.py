"""商業假設集中地——改參數不改邏輯（PC-001）。

以下皆為 H2 預設值，尚未經用戶定案（prepare.md 待討論 #1）；
報告中一律標示為「假設」。金額單位 USD（Hillstrom 原始幣別）。
"""

GROSS_MARGIN = 0.30            # 毛利率
SEND_COST_PER_MSG = 0.005      # 每則發送成本（推播直接成本趨近零，取保守小值）
OPT_OUT_RATE_MAX = 0.02        # Q3 敏感度掃描上限（資料無退訂欄，見報告限制章節）
OPT_OUT_RATE_STEPS = 41        # 掃描點數（0% ~ 2%）
PUSHES_PER_YEAR = 12           # 推導「單用戶未來 12 個月可觸達價值」的年推播檔數
