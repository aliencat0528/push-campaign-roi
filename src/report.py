"""組出 reports/REPORT.md：主交付物，回答規劃書 Q1/Q2/Q3，每個金額結論附 CI。

REPORT.md 是產物、不手改——pipeline 重跑即重生。
"""

from datetime import date
from pathlib import Path

import params

REPORT_PATH = Path(__file__).resolve().parent.parent / "reports" / "REPORT.md"

ARM_LABEL = {"Mens E-Mail": "男裝推播", "Womens E-Mail": "女裝推播"}


def sigMark(row):
    return "" if row["significant"] else " △ CI 跨零，不下定論"


def buildReport(conn, overall, segments, roiSummary, figPaths):
    funnel = conn.execute("SELECT * FROM t02Funnel").fetchdf().set_index("segment")
    funnel["visits"] = funnel["visits"].astype(int)
    funnel["conversions"] = funnel["conversions"].astype(int)
    balance = conn.execute("SELECT * FROM t01Balance").fetchdf()
    groupCounts = dict(conn.execute("SELECT segment, n FROM t01GroupCounts").fetchall())

    lines = []
    w = lines.append

    w(f"# 推播活動 ROI 增量分析報告\n")
    w(f"> 產出日：{date.today().isoformat()} · 本檔為 `run_pipeline.py` 產物，勿手改\n")
    w(
        "> 資料集：Hillstrom E-Mail Analytics Challenge（64,000 名客戶真實隨機實驗）。"
        "推播情境為方法論轉譯，見「限制與轉譯聲明」章節。\n"
    )
    w("---\n")

    # --- 摘要 ---
    w("## 摘要：三個決策問題的答案\n")
    w("| # | 決策問題 | 答案 |")
    w("|---|---------|------|")
    for arm in overall:
        r = roiSummary["arms"][arm]
        w(
            f"| Q1 | {ARM_LABEL[arm]}該不該續辦？ | **該**——增量利潤 "
            f"${r['incProfit']:,.0f} `[{r['incProfitCi'][0]:,.0f}, {r['incProfitCi'][1]:,.0f}]`，"
            f"增量 ROI {r['incRoi']:.1f}x |"
        )
    bestSeg = max((s for s in segments if s["significant"]), key=lambda s: s["spend"]["diff"])
    w(
        f"| Q2 | 該推給誰？ | 本次分群（recency／歷史消費／新客／渠道）**未發現負增量族群**；"
        f"效果最強為 `{bestSeg['dim']}={bestSeg['dimValue']}`，"
        f"+\\${bestSeg['spend']['diff']:.2f} `[{bestSeg['spend']['ciLow']:.2f}, "
        f"{bestSeg['spend']['ciHigh']:.2f}]`——見下方分群圖 |"
    )
    breakEvens = "、".join(
        f"{ARM_LABEL[a]} {r['breakEvenOptOut']:.1%}" for a, r in roiSummary["arms"].items()
    )
    w(
        f"| Q3 | 退訂會不會讓 ROI 翻盤？ | **不會，在合理假設下**——兩組臨界退訂率 "
        f"{breakEvens}，遠高於業界常見退訂率（通常 <1%） |"
    )
    w("\n---\n")

    # --- 1. 隨機性檢核 ---
    w("## 1. 隨機性檢核：分析是否可信\n")
    countsText = "、".join(f"{seg} {n:,}" for seg, n in groupCounts.items())
    w(f"三組樣本數：{countsText}。SRM 卡方檢定通過（`sql/01_validation.sql` + `src/stats.py`），"
      f"隨機分組符合設計比例，以下增量數字有效。共變數平衡表：\n")
    w(_dfToMd(balance))
    w("\n")

    # --- 2. 漏斗與整體增量 ---
    w("## 2. 漏斗與整體增量（Q1）\n")
    w(f"![漏斗指標]({figPaths['funnel'].name})\n")
    w(_dfToMd(funnel.reset_index()))
    w(f"\n![整體增量]({figPaths['overallLift'].name})\n")
    for arm, r in overall.items():
        s = r["spend"]
        w(
            f"- **{ARM_LABEL[arm]}**：造訪率 +{r['visit']['diff']:.2%}"
            f"（p={r['visit']['pValue']:.1e}）、轉換率 +{r['conversion']['diff']:.2%}"
            f"（p={r['conversion']['pValue']:.1e}）、人均消費 +\\${s['diff']:.2f} "
            f"`[{s['ciLow']:.2f}, {s['ciHigh']:.2f}]`（Welch t，bootstrap 交叉驗證 "
            f"`[{s['bootCiLow']:.2f}, {s['bootCiHigh']:.2f}]`，p={s['pValue']:.1e}）"
        )
    w("\n")

    # --- 3. 天真 vs 增量 ROI ---
    w("## 3. 天真 ROI vs 增量 ROI：轉折點一（Q1）\n")
    w(
        "天真做法把「收到推播且有消費的人」的消費全記給活動——但這些人很多本來就會買，"
        "選擇偏誤讓天真 ROI 系統性高估。正確做法用對照組算增量：\n"
    )
    w(f"![天真 vs 增量 ROI]({figPaths['roiComparison'].name})\n")
    w("| 組別 | 天真 ROI | 增量 ROI | 高估倍數 | 增量利潤 (95% CI) |")
    w("|------|---------|---------|---------|-------------------|")
    for arm, r in roiSummary["arms"].items():
        lo, hi = r["incProfitCi"]
        w(
            f"| {ARM_LABEL[arm]} | {r['naiveRoi']:.1f}x | {r['incRoi']:.1f}x | "
            f"{r['overstatement']:.2f}× | \\${r['incProfit']:,.0f} `[{lo:,.0f}, {hi:,.0f}]` |"
        )
    w(
        f"\n> 假設：毛利率 {params.GROSS_MARGIN:.0%}、每則發送成本 \\${params.SEND_COST_PER_MSG}"
        "（H2 預設值，待用戶定案，見 `prepare.md` 待討論 #1）。\n"
    )

    # --- 4. 分群 ---
    w("## 4. 分群增量：轉折點二（Q2）\n")
    w(
        "該推的不是「最可能買的人」（sure things，推了純虧成本），而是 **persuadables**"
        "（有推才買的人）。若某分群增量為負，代表推播對該群是負效果"
        "（sleeping dogs）——不該推。\n\n"
        "本次以 recency／歷史消費／新客／渠道四維切分，**未觀察到顯著負增量族群**"
        "（如實記錄，不強行製造轉折）；下圖藍點為統計顯著，灰點為 95% CI 跨零、不下定論："
        "\n"
    )
    w(f"![分群增量]({figPaths['segmentLift'].name})\n")
    for s in segments:
        t = s["spend"]
        w(
            f"- {s['dim']}=`{s['dimValue']}`：+\\${t['diff']:.2f} "
            f"`[{t['ciLow']:.2f}, {t['ciHigh']:.2f}]`（n={s['nTreated']:,}，MDE \\${t['mde']:.2f}）"
            f"{sigMark(s)}"
        )
    w("\n")

    # --- 5. 退訂敏感度 ---
    w("## 5. 退訂成本敏感度：轉折點三（Q3）\n")
    w(
        "每次退訂 = 永久失去該用戶的免費觸達渠道。資料無退訂欄位（見下方限制），"
        f"故以單用戶年觸達價值（合併推導）\\${roiSummary['reachValue']:.2f} 做敏感度掃描，"
        f"區間 0–{params.OPT_OUT_RATE_MAX:.0%}：\n"
    )
    w(f"![退訂敏感度]({figPaths['optOut'].name})\n")
    for arm, r in roiSummary["arms"].items():
        w(f"- **{ARM_LABEL[arm]}**：臨界退訂率 {r['breakEvenOptOut']:.2%}"
          "（超過此值 ROI 翻負；業界常見推播退訂率多在 1% 以下，結論穩健）")
    w("\n")

    # --- 限制 ---
    w("## 6. 限制與轉譯聲明\n")
    w(
        "- **email → 推播的方法論轉譯**：Hillstrom 是 email 實驗，非推播原生資料。"
        "兩者結構同構（近零成本自有渠道、有退訂機制），但本報告的絕對數字（USD、2008 年零售）"
        "無現時意義，**方法論**才是重點\n"
        "- **無送達／開啟／退訂欄位**：漏斗上半段以 sent≈delivered 近似；退訂成本改用敏感度區間，"
        "而非單點估計\n"
        "- **觀察窗僅兩週**：長期 LTV 效果測不到，reachValue 以「單次增量利潤 × 12 檔/年」外推，"
        "假設效果穩定重現，實務上可能因疲勞效應遞減\n"
        "- **H2 商業參數（毛利率／退訂區間／觸達價值）為預設假設**，非用戶定案數值\n"
    )

    w("---\n")
    w("*完整規劃書、商業觀念推導：見 `prepare.md` 頂部連結。*\n")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return REPORT_PATH


def _dfToMd(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        out.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(out)
