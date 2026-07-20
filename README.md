# push-campaign-roi - 推播活動 ROI 增量分析

以 Hillstrom 真實隨機實驗資料（64,000 名客戶）示範推播活動 ROI 的正確算法：
用對照組算**增量**，並列天真 ROI 揭露高估幅度，找出「推了反而虧」的族群，
並以退訂成本敏感度分析檢驗結論是否翻盤。

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 功能特色 【必要】

- **增量 ROI vs 天真 ROI 並列**——量化「把收件者營收全記給活動」高估了幾倍
- **分群增量分析**——依 recency / 歷史消費 / 新客 / 渠道切分，標出負增量（sleeping dogs）族群
- **退訂成本敏感度**——掃描 0–2% 退訂率區間，找出 ROI 翻負的臨界點
- **會拒絕的 pipeline**——隨機分組檢核（SRM）不過即中止，不出報告
- 一鍵重跑：改 `src/params.py` 商業假設 → 報告與圖表全部重生

## 快速開始 【必要】

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# 預期：Successfully installed duckdb-... pandas-... matplotlib-... scipy-... requests-...

.venv/bin/python scripts/download_data.py
# 預期：data/raw/hillstrom.csv 64,000 筆 · 欄位與 SHA256 校驗通過

.venv/bin/python src/run_pipeline.py
# 預期：reports/REPORT.md 與 reports/figures/*.png 產出，終端印出各階段摘要
```

## 使用方式 【必要】

- **全流程重跑**：`.venv/bin/python src/run_pipeline.py`
- **從特定階段重跑**（改了下游邏輯時）：`.venv/bin/python src/run_pipeline.py --from 04`
- **只驗證 SQL 可執行**：`.venv/bin/python src/run_pipeline.py --dry-run`
- **改商業假設**：編輯 `src/params.py`（毛利率、每則成本、退訂率區間、觸達價值）後重跑

## 專案結構 【必要】

```
scripts/download_data.py   # 資料下載 + 校驗（冪等）
sql/00–05_*.sql            # 編號即執行順序；每檔註解對應規劃書 Q1/Q2/Q3
src/params.py              # 商業假設集中地——改參數不改邏輯
src/stats.py               # z 檢定 / Welch t / bootstrap CI / MDE
src/analysis.py            # 整體增量 / 分群增量
src/roi.py                 # ROI 模型 + 退訂率敏感度掃描
src/figures.py             # 五張圖表（dataviz skill 色票）
src/report.py              # 組出 reports/REPORT.md
src/run_pipeline.py        # 一鍵：SQL → 統計 → ROI → 圖表 → REPORT.md
reports/REPORT.md          # 主交付物（產物，勿手改）
```

模組職責與資料流細節 → `docs/ARCHITECTURE.md`

## 測試 【必要】

```bash
.venv/bin/python src/run_pipeline.py --dry-run
```

## 版本歷史 【必要】

### v1.0.0 (2026-07-20)

- **P0–P4 完整交付** — 隨機性檢核（SRM）、漏斗與整體增量、天真 vs 增量 ROI、
  分群增量、退訂成本敏感度、五張圖表、`reports/REPORT.md`
- 主要結論：兩組推播增量 ROI 45.2x／24.5x（天真 ROI 高估 1.85×／2.54×）；
  臨界退訂率 10.8%／5.9%，遠高於業界常見退訂率，結論穩健

### v0.1.0 (2026-07-20)

- **Phase 0 骨架** — 專案結構、資料下載腳本、規劃書定稿

## 授權 【必要】

MIT License

---

## 相關文件

- 完整規劃書（商業觀念、Phase、出口條件）→ `prepare.md` 頂部連結
- 決策記錄 → `prepare.md`（前綴 `PC-`）
- 系統架構、模組職責、資料流 → `docs/ARCHITECTURE.md`
