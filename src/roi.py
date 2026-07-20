"""ROI 模型：天真 vs 增量並列（Q1）＋ 退訂率敏感度（Q3）。

- 天真口徑：把實驗組全部營收記給活動（業界常見錯誤，僅供對照）
- 增量口徑：只認（實驗組人均 − 對照組人均）× 實驗組人數
- 退訂成本：發送數 × 退訂率 × 單用戶未來可觸達價值（reachValue）
- reachValue 用「合併實驗組的增量利潤/則 × 年推播檔數」推導，兩組共用同一把尺，
  避免自我參照（各組用自己的利潤推 reachValue 會讓臨界退訂率恆等於 1/年檔數）
"""

import numpy as np

import params


def pooledReachValue(overall):
    """單用戶未來 12 個月可觸達價值（USD/人/年），由合併增量利潤推導。"""
    nTotal = sum(r["n"] for r in overall.values())
    pooledDiff = sum(r["spend"]["diff"] * r["n"] for r in overall.values()) / nTotal
    profitPerSend = pooledDiff * params.GROSS_MARGIN - params.SEND_COST_PER_MSG
    return profitPerSend * params.PUSHES_PER_YEAR


def armRoi(r, reachValue):
    """單一實驗組 ROI 彙整。r：analysis.overallLift 單組結果。"""
    n = r["n"]
    diff = r["spend"]["diff"]
    sendCost = n * params.SEND_COST_PER_MSG

    naiveRevenue = n * r["meanSpend"]
    naiveProfit = naiveRevenue * params.GROSS_MARGIN - sendCost

    incRevenue = diff * n
    incProfit = incRevenue * params.GROSS_MARGIN - sendCost
    incProfitCi = tuple(
        bound * n * params.GROSS_MARGIN - sendCost
        for bound in (r["spend"]["ciLow"], r["spend"]["ciHigh"])
    )

    rates = np.linspace(0, params.OPT_OUT_RATE_MAX, params.OPT_OUT_RATE_STEPS)
    sensitivity = []
    for rate in rates:
        optOutCost = n * float(rate) * reachValue
        profit = incProfit - optOutCost
        cost = sendCost + optOutCost
        sensitivity.append({"optOutRate": float(rate), "profit": profit, "roi": profit / cost})

    return {
        "n": n,
        "sendCost": sendCost,
        "naiveRevenue": naiveRevenue,
        "naiveProfit": naiveProfit,
        "naiveRoi": naiveProfit / sendCost,
        "incRevenue": incRevenue,
        "incProfit": incProfit,
        "incProfitCi": incProfitCi,
        "incRoi": incProfit / sendCost,
        "overstatement": r["meanSpend"] / diff,  # 天真營收高估倍數（人均口徑）
        "breakEvenOptOut": incProfit / (n * reachValue) if reachValue > 0 else None,
        "sensitivity": sensitivity,
    }


def roiSummary(overall):
    """全部實驗組的 ROI 彙整。overall：analysis.overallLift 輸出。"""
    reachValue = pooledReachValue(overall)
    return {
        "reachValue": reachValue,
        "arms": {arm: armRoi(r, reachValue) for arm, r in overall.items()},
    }
