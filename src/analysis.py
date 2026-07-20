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
