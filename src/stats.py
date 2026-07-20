"""統計檢定工具：SRM 卡方、兩比例 z 檢定、Welch t、bootstrap CI、MDE。

原則（CLAUDE.md）：每個金額結論附 95% CI；CI 跨零不寫成定論；
分群報 MDE（80% 檢定力），樣本不足標灰。
"""

import math

import numpy as np
from scipy import stats as scipyStats

SRM_ALPHA = 0.01  # SRM 用嚴格門檻：這是「實驗壞了」警報，不是效果檢定
Z975 = scipyStats.norm.ppf(0.975)
Z80 = scipyStats.norm.ppf(0.80)


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


def twoPropDiff(x1, n1, x0, n0):
    """比例差（實驗 − 對照）：合併變異 z 檢定 + 未合併 Wald 95% CI。"""
    p1, p0 = x1 / n1, x0 / n0
    diff = p1 - p0
    pooled = (x1 + x0) / (n1 + n0)
    sePooled = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n0))
    z = diff / sePooled
    se = math.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    return {
        "rate1": p1,
        "rate0": p0,
        "diff": diff,
        "ciLow": diff - Z975 * se,
        "ciHigh": diff + Z975 * se,
        "pValue": 2 * scipyStats.norm.sf(abs(z)),
    }


def welchMeanDiff(mean1, var1, n1, mean0, var0, n0):
    """平均差（實驗 − 對照）：Welch t + 95% CI + 80% 檢定力 MDE。

    spend 這種右偏零膨脹分佈靠大樣本 CLT；整體層另以 bootstrap 交叉驗證 CI。
    """
    diff = mean1 - mean0
    se = math.sqrt(var1 / n1 + var0 / n0)
    df = (var1 / n1 + var0 / n0) ** 2 / (
        (var1 / n1) ** 2 / (n1 - 1) + (var0 / n0) ** 2 / (n0 - 1)
    )
    t = diff / se
    return {
        "diff": diff,
        "se": se,
        "ciLow": diff - Z975 * se,
        "ciHigh": diff + Z975 * se,
        "pValue": 2 * scipyStats.t.sf(abs(t), df),
        "mde": (Z975 + Z80) * se,
    }


def bootstrapMeanDiffCi(sample1, sample0, iters=2000, batch=250, seed=42):
    """平均差的 bootstrap percentile 95% CI（分批向量化，控記憶體）。"""
    rng = np.random.default_rng(seed)
    diffs = np.empty(iters)
    pos = 0
    while pos < iters:
        b = min(batch, iters - pos)
        idx1 = rng.integers(0, sample1.size, (b, sample1.size))
        idx0 = rng.integers(0, sample0.size, (b, sample0.size))
        diffs[pos:pos + b] = sample1[idx1].mean(axis=1) - sample0[idx0].mean(axis=1)
        pos += b
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return float(lo), float(hi)
