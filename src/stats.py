"""統計檢定工具：SRM 卡方、兩比例 z 檢定、Welch t、bootstrap CI、MDE。

原則（CLAUDE.md）：每個金額結論附 95% CI；CI 跨零不寫成定論；
分群報 MDE，樣本不足標灰。P2 起逐步補齊，P1 先落 SRM。
"""

from scipy import stats as scipyStats

SRM_ALPHA = 0.01  # SRM 用嚴格門檻：這是「實驗壞了」警報，不是效果檢定


def srmTest(groupCounts):
    """SRM 檢核：觀測組數 vs 等比例設計（1/3 : 1/3 : 1/3）。

    groupCounts: {segment: n}
    回傳 (chi2, pValue, passed)；p < SRM_ALPHA 視為隨機分組失衡。
    """
    observed = list(groupCounts.values())
    total = sum(observed)
    expected = [total / len(observed)] * len(observed)
    chi2, pValue = scipyStats.chisquare(observed, f_exp=expected)
    return chi2, pValue, pValue >= SRM_ALPHA
