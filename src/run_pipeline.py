"""一鍵 pipeline：SQL 依編號執行 → 統計檢核 → （P3 起）ROI → （P4 起）REPORT.md。

用法：
    .venv/bin/python src/run_pipeline.py            # 全流程
    .venv/bin/python src/run_pipeline.py --from 01  # 從編號 01 起重跑 SQL
    .venv/bin/python src/run_pipeline.py --dry-run  # 只驗證 SQL 可執行，不跑統計

防呆（CLAUDE.md，不得移除）：SRM 檢核不過 → 中止，不產報告。
"""

import argparse
import sys
from pathlib import Path

import duckdb

import analysis
import figures
import report
import roi
import stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = PROJECT_ROOT / "sql"
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"


def runSqlFiles(conn, fromStage):
    for sqlFile in sorted(SQL_DIR.glob("*.sql")):
        stage = sqlFile.name[:2]
        if stage < fromStage:
            print(f"[skip] {sqlFile.name}")
            continue
        print(f"[sql ] {sqlFile.name}")
        conn.execute(sqlFile.read_text(encoding="utf-8"))


def checkSrm(conn):
    rows = conn.execute("SELECT segment, n FROM t01GroupCounts").fetchall()
    groupCounts = dict(rows)
    chi2, pValue, passed = stats.srmTest(groupCounts)
    print(f"[srm ] 組數 {groupCounts} · chi2={chi2:.3f} · p={pValue:.4f}")
    if not passed:
        print(f"[srm ] ❌ p < {stats.SRM_ALPHA}：隨機分組失衡，增量數字無效——中止，不產報告")
        sys.exit(1)
    print("[srm ] ✅ 通過：分組符合 1/3 等比例設計")


def printBalance(conn):
    balance = conn.execute("SELECT * FROM t01Balance").fetchdf()
    print("[bal ] 共變數平衡表（各組應近似）：")
    print(balance.to_string(index=False))


def printOverallLift(conn, overall):
    funnel = conn.execute("SELECT * FROM t02Funnel").fetchdf()
    print("[fnl ] 各組漏斗：")
    print(funnel.to_string(index=False))
    for arm, r in overall.items():
        s = r["spend"]
        print(
            f"[lift] {arm} vs 對照：visit +{r['visit']['diff']:.2%} (p={r['visit']['pValue']:.2e}) · "
            f"conversion +{r['conversion']['diff']:.2%} (p={r['conversion']['pValue']:.2e}) · "
            f"spend/人 +${s['diff']:.4f} [95% CI {s['ciLow']:.4f}, {s['ciHigh']:.4f}] "
            f"(bootstrap [{s['bootCiLow']:.4f}, {s['bootCiHigh']:.4f}], p={s['pValue']:.2e})"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="fromStage", default="00", help="從此編號起重跑 SQL")
    parser.add_argument("--dry-run", action="store_true", help="只驗證 SQL 可執行")
    args = parser.parse_args()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(DB_PATH))
    conn.execute(f"SET file_search_path = '{PROJECT_ROOT}'")

    runSqlFiles(conn, args.fromStage)
    if args.dry_run:
        print("[done] dry-run：SQL 全數可執行")
        return

    checkSrm(conn)
    printBalance(conn)
    overall = analysis.overallLift(conn)  # 含 bootstrap，算一次重複使用（P2 展示 + P3 ROI）
    printOverallLift(conn, overall)
    segments, roiSummary = printSegmentsAndRoi(conn, overall)
    reportPath = renderReport(conn, overall, segments, roiSummary)
    print(f"[done] P4 完成：{reportPath}")


def printSegmentsAndRoi(conn, overall):
    segments = analysis.segmentLift(conn)
    print("[seg ] 分群增量（合併實驗組 vs 對照，spend/人）：")
    for s in segments:
        t = s["spend"]
        flag = "  " if s["significant"] else "△ "  # △ = CI 跨零，不下定論
        print(
            f"  {flag}{s['dim']}={s['dimValue']:<12} +${t['diff']:.4f} "
            f"[{t['ciLow']:.4f}, {t['ciHigh']:.4f}] · MDE ${t['mde']:.4f} · n={s['nTreated']:,}"
        )
    summary = roi.roiSummary(overall)
    print(f"[roi ] 單用戶年觸達價值（合併推導）：${summary['reachValue']:.2f}")
    for arm, r in summary["arms"].items():
        lo, hi = r["incProfitCi"]
        print(
            f"[roi ] {arm}：增量利潤 ${r['incProfit']:,.0f} [{lo:,.0f}, {hi:,.0f}] · "
            f"增量 ROI {r['incRoi']:.1f}x · 天真 ROI {r['naiveRoi']:.1f}x"
            f"（人均高估 {r['overstatement']:.2f}×）· 臨界退訂率 {r['breakEvenOptOut']:.2%}"
        )
    return segments, summary


def renderReport(conn, overall, segments, roiSummary):
    funnelDf = conn.execute("SELECT * FROM t02Funnel").fetchdf()
    figPaths = {
        "funnel": figures.plotFunnel(funnelDf),
        "overallLift": figures.plotOverallLift(overall),
        "roiComparison": figures.plotRoiComparison(roiSummary),
        "segmentLift": figures.plotSegmentLift(segments),
        "optOut": figures.plotOptOutSensitivity(roiSummary),
    }
    print(f"[fig ] 五張圖表輸出至 {figures.FIG_DIR}")
    return report.buildReport(conn, overall, segments, roiSummary, figPaths)


if __name__ == "__main__":
    main()
