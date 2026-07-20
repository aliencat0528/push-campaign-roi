"""分析層：從 DuckDB 表取數，產出整體與分群增量結果（原始精度，四捨五入只在報告層）。"""

import stats

CONTROL = "No E-Mail"
TREATMENT_ARMS = ["Mens E-Mail", "Womens E-Mail"]


def fetchArms(conn):
    rows = conn.execute(
        "SELECT segment, n, visits, conversions, meanSpend, varSpend FROM t03Arms"
    ).fetchall()
    return {
        r[0]: {"n": r[1], "visits": r[2], "conversions": r[3], "meanSpend": r[4], "varSpend": r[5]}
        for r in rows
    }


def spendArray(conn, segment):
    return conn.execute(
        "SELECT spend FROM vCustomers WHERE segment = ?", [segment]
    ).fetchnumpy()["spend"]


def overallLift(conn):
    """Q1：兩個實驗組 vs 對照組的 visit / conversion / spend 增量與檢定。"""
    arms = fetchArms(conn)
    ctl = arms[CONTROL]
    ctlSpend = spendArray(conn, CONTROL)
    results = {}
    for arm in TREATMENT_ARMS:
        t = arms[arm]
        spendTest = stats.welchMeanDiff(
            t["meanSpend"], t["varSpend"], t["n"], ctl["meanSpend"], ctl["varSpend"], ctl["n"]
        )
        bootLo, bootHi = stats.bootstrapMeanDiffCi(spendArray(conn, arm), ctlSpend)
        results[arm] = {
            "n": t["n"],
            "controlN": ctl["n"],
            "meanSpend": t["meanSpend"],
            "controlMeanSpend": ctl["meanSpend"],
            "visit": stats.twoPropDiff(t["visits"], t["n"], ctl["visits"], ctl["n"]),
            "conversion": stats.twoPropDiff(t["conversions"], t["n"], ctl["conversions"], ctl["n"]),
            "spend": spendTest | {"bootCiLow": bootLo, "bootCiHigh": bootHi},
        }
    return results


def combineTreated(rows):
    """合併兩個 email 組的矩統計（加權平均 + 合併變異數公式）。"""
    n = sum(r["n"] for r in rows)
    mean = sum(r["n"] * r["meanSpend"] for r in rows) / n
    ss = sum(
        (r["n"] - 1) * r["varSpend"] + r["n"] * (r["meanSpend"] - mean) ** 2 for r in rows
    )
    return {
        "n": n,
        "meanSpend": mean,
        "varSpend": ss / (n - 1),
        "conversions": sum(r["conversions"] for r in rows),
    }


def segmentLift(conn):
    """Q2：各分群「合併實驗組 vs 對照」的 spend 增量與檢定；CI 跨零者標不顯著。"""
    df = conn.execute("SELECT * FROM t04Segments").fetchdf()
    results = []
    for (dim, val), g in df.groupby(["dim", "dimValue"], sort=False):
        ctl = g[g["segment"] == CONTROL].to_dict("records")[0]
        tr = combineTreated(g[g["segment"] != CONTROL].to_dict("records"))
        test = stats.welchMeanDiff(
            tr["meanSpend"], tr["varSpend"], tr["n"],
            ctl["meanSpend"], ctl["varSpend"], ctl["n"],
        )
        results.append({
            "dim": dim,
            "dimValue": val,
            "nTreated": tr["n"],
            "nControl": ctl["n"],
            "spend": test,
            "conversion": stats.twoPropDiff(
                tr["conversions"], tr["n"], ctl["conversions"], ctl["n"]
            ),
            "significant": not (test["ciLow"] <= 0 <= test["ciHigh"]),
        })
    return results
