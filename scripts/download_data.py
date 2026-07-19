"""下載 Hillstrom E-Mail Analytics Challenge 資料集並校驗（冪等，可重跑）。

來源：MineThatData 官網直載，免 Kaggle 憑證（PC-001）。
校驗三關：SHA256（首次下載後回填 EXPECTED_SHA256）、筆數 64,000、欄位名完全一致。
"""

import hashlib
import sys
from pathlib import Path

import requests

DATA_URL = (
    "http://www.minethatdata.com/"
    "Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"
)
RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "hillstrom.csv"

# 首次成功下載後回填實測值；之後每次執行都比對，防來源被換檔
EXPECTED_SHA256 = "0e5893329d8b93cefecc571777672028290ab69865718020c78c7284f291aece"
EXPECTED_ROWS = 64_000
EXPECTED_COLUMNS = [
    "recency", "history_segment", "history", "mens", "womens",
    "zip_code", "newbie", "channel", "segment", "visit", "conversion", "spend",
]


def sha256Of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download():
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"下載 {DATA_URL}")
    resp = requests.get(DATA_URL, timeout=120)
    resp.raise_for_status()
    RAW_PATH.write_bytes(resp.content)
    print(f"已寫入 {RAW_PATH}（{RAW_PATH.stat().st_size:,} bytes）")


def validate():
    with open(RAW_PATH, encoding="utf-8") as f:
        header = f.readline().strip().split(",")
        rows = sum(1 for _ in f)

    problems = []
    if header != EXPECTED_COLUMNS:
        problems.append(f"欄位不符：{header}")
    if rows != EXPECTED_ROWS:
        problems.append(f"筆數 {rows:,} ≠ 預期 {EXPECTED_ROWS:,}")

    actualSha = sha256Of(RAW_PATH)
    if EXPECTED_SHA256 is None:
        print(f"[首次下載] SHA256 = {actualSha}\n→ 請回填 EXPECTED_SHA256 後 commit")
    elif actualSha != EXPECTED_SHA256:
        problems.append(f"SHA256 不符：{actualSha}")

    if problems:
        print("校驗失敗：\n- " + "\n- ".join(problems))
        sys.exit(1)
    print(f"校驗通過：{rows:,} 筆、12 欄位")


def main():
    if RAW_PATH.exists():
        print(f"{RAW_PATH} 已存在，跳過下載，僅校驗")
    else:
        download()
    validate()


if __name__ == "__main__":
    main()
