> 繼承根目錄共用規則（Claude Code 已自動載入，勿重複讀取 ../CLAUDE.md）

# push-campaign-roi

作品集專案四：推播活動 ROI 增量分析（Appier AIQUA 對映）。
主軸：**天真 ROI vs 增量 ROI 並列，每個結論接一個金額化決策**。
規劃書見 prepare.md 頂部連結。

## 技術棧與指令

- Python 3.12 + venv（`.venv/`），依賴見 `requirements.txt`
- 分析引擎：DuckDB（重邏輯用 SQL）＋ pandas（輕整形）＋ matplotlib（靜態圖）＋ scipy（檢定）
- 資料下載：`.venv/bin/python scripts/download_data.py`（MineThatData 直接下載，免憑證）
- 一鍵跑 pipeline：`.venv/bin/python src/run_pipeline.py`（輸出 reports/REPORT.md 與 reports/figures/）

## 專案規則（與根規則的差異）

- `data/` 不進 git；原始 CSV 一律視為唯讀，任何清理都在 SQL view 層做
- 金額口徑統一為 `spend` 欄（兩週觀察窗內消費）；改動口徑必須記入 `prepare.md`
- 三組分組欄 `segment`（Mens E-Mail / Womens E-Mail / No E-Mail），No E-Mail 恆為對照組
- 商業假設參數（毛利率、每則成本、退訂率區間、單用戶觸達價值）集中 `src/params.py`，改參數不改邏輯
- `sql/` 檔名編號即執行順序，每檔開頭註解標明回答規劃書的哪個 Q（Q1 續辦／Q2 推給誰／Q3 退訂翻盤）
- SRM 檢核（`01_validation.sql`）不過 → pipeline 中止，不產報告；此防呆不得移除
- 統計原則：每個金額結論附 95% CI；CI 跨零不寫成定論；分群報 MDE，樣本不足標灰
