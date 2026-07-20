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


def printOverallLift(conn):
    funnel = conn.execute("SELECT * FROM t02Funnel").fetchdf()
    print("[fnl ] 各組漏斗：")
    print(funnel.to_string(index=False))
    for arm, r in analysis.overallLift(conn).items():
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
    printOverallLift(conn)
    print("[done] P2 完成（分群與 ROI 見 P3）")


if __name__ == "__main__":
    main()
