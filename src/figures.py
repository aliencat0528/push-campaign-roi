"""靜態圖表（matplotlib），供 REPORT.md 內嵌。

配色依 dataviz skill 參考色票：類別色定序不循環，控制組固定用中性灰標示基準，
處理組依序取 slot1 藍 / slot3 洋紅；序列圖用單一藍色調由淺到深。
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

FIG_DIR = Path(__file__).resolve().parent.parent / "reports" / "figures"

SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

BLUE = "#2a78d6"      # 處理組 1（Mens E-Mail）——類別 slot 1
MAGENTA = "#e87ba4"   # 處理組 2（Womens E-Mail）——類別 slot 3
GRAY_CONTROL = "#898781"  # 對照組——基準線，故意用中性色不用類別色

ARM_COLORS = {"Mens E-Mail": BLUE, "Womens E-Mail": MAGENTA, "No E-Mail": GRAY_CONTROL}

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "text.color": INK_PRIMARY,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK_SECONDARY,
    "xtick.color": INK_MUTED,
    "ytick.color": INK_MUTED,
    "grid.color": GRIDLINE,
    "font.size": 11,
    "font.family": "sans-serif",
    "savefig.facecolor": SURFACE,
})


def _cleanAxes(ax):
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)
    ax.grid(axis="y", linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)


def plotFunnel(funnelDf, path=None):
    """三組漏斗指標並排長條：visitRate / convRate。"""
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    metrics = [("visitRate", "造訪率"), ("convRate", "轉換率")]
    for ax, (col, title) in zip(axes, metrics):
        rows = funnelDf.set_index("segment").loc[list(ARM_COLORS)]
        colors = [ARM_COLORS[s] for s in rows.index]
        bars = ax.bar(rows.index, rows[col], color=colors, width=0.55)
        for bar, v in zip(bars, rows[col]):
            ax.text(bar.get_x() + bar.get_width() / 2, v, f"{v:.1%}",
                    ha="center", va="bottom", fontsize=9, color=INK_PRIMARY)
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
        ax.set_title(title, fontsize=11, color=INK_PRIMARY, loc="left")
        ax.tick_params(axis="x", labelrotation=12)
        _cleanAxes(ax)
    fig.suptitle("漏斗指標：兩個推播組 vs 對照組", fontsize=12, color=INK_PRIMARY, x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return _save(fig, path, "01_funnel.png")


def plotOverallLift(overall, path=None):
    """人均消費增量：長條 + 95% CI 誤差線，零基準虛線。"""
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    arms = list(overall.keys())
    diffs = [overall[a]["spend"]["diff"] for a in arms]
    lo = [overall[a]["spend"]["diff"] - overall[a]["spend"]["ciLow"] for a in arms]
    hi = [overall[a]["spend"]["ciHigh"] - overall[a]["spend"]["diff"] for a in arms]
    colors = [ARM_COLORS[a] for a in arms]

    ax.axhline(0, color=BASELINE, linewidth=1)
    bars = ax.bar(arms, diffs, yerr=[lo, hi], capsize=4, color=colors, width=0.5,
                   error_kw={"ecolor": INK_SECONDARY, "linewidth": 1.2})
    for bar, v in zip(bars, diffs):
        ax.text(bar.get_x() + bar.get_width() / 2, v + max(hi) * 0.15,
                 f"+${v:.2f}", ha="center", fontsize=10, color=INK_PRIMARY, fontweight="medium")
    ax.set_ylabel("人均消費增量（USD，95% CI）")
    ax.set_title("整體增量：實驗組 − 對照組人均消費", fontsize=12, color=INK_PRIMARY, loc="left")
    _cleanAxes(ax)
    fig.tight_layout()
    return _save(fig, path, "02_overall_lift.png")


def plotRoiComparison(roiSummary, path=None):
    """天真 ROI vs 增量 ROI 分組長條：灰＝天真（高估、有問題），藍/洋紅＝增量（可信）。"""
    fig, ax = plt.subplots(figsize=(7, 3.8))
    arms = list(roiSummary["arms"].keys())
    x = range(len(arms))
    width = 0.32
    naive = [roiSummary["arms"][a]["naiveRoi"] for a in arms]
    inc = [roiSummary["arms"][a]["incRoi"] for a in arms]

    ax.bar([i - width / 2 for i in x], naive, width, label="天真 ROI（高估）", color=GRAY_CONTROL)
    bars = ax.bar([i + width / 2 for i in x], inc, width, label="增量 ROI（可信）",
                  color=[ARM_COLORS[a] for a in arms])
    for i, (n, v) in enumerate(zip(naive, inc)):
        ax.text(i - width / 2, n + 1.5, f"{n:.0f}x", ha="center", fontsize=9, color=INK_SECONDARY)
        ax.text(i + width / 2, v + 1.5, f"{v:.0f}x", ha="center", fontsize=9, color=INK_PRIMARY)
    ax.set_xticks(list(x))
    ax.set_xticklabels(arms)
    ax.set_ylabel("ROI（倍數）")
    ax.set_title("天真 ROI 高估幅度 vs 增量 ROI", fontsize=12, color=INK_PRIMARY, loc="left")
    ax.legend(frameon=False, loc="upper right", fontsize=9)
    _cleanAxes(ax)
    fig.tight_layout()
    return _save(fig, path, "03_roi_comparison.png")


def plotSegmentLift(segments, path=None):
    """分群增量森林圖：顯著＝藍、不顯著（CI 跨零）＝灰，由上而下依 diff 排序。"""
    ordered = sorted(segments, key=lambda s: s["spend"]["diff"])
    labels = [f"{s['dim']}={s['dimValue']}" for s in ordered]
    diffs = [s["spend"]["diff"] for s in ordered]
    los = [s["spend"]["diff"] - s["spend"]["ciLow"] for s in ordered]
    his = [s["spend"]["ciHigh"] - s["spend"]["diff"] for s in ordered]
    colors = [BLUE if s["significant"] else GRAY_CONTROL for s in ordered]

    fig, ax = plt.subplots(figsize=(7.5, 0.42 * len(ordered) + 1.2))
    y = range(len(ordered))
    ax.axvline(0, color=BASELINE, linewidth=1)
    ax.errorbar(diffs, y, xerr=[los, his], fmt="o", color=INK_PRIMARY,
                ecolor=INK_MUTED, elinewidth=1.4, capsize=3, markersize=5, zorder=3)
    for yi, c in zip(y, colors):
        ax.scatter(diffs[yi], yi, color=c, s=55, zorder=4)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("人均消費增量（USD，合併實驗組 vs 對照，95% CI）")
    ax.set_title("分群增量：藍＝統計顯著，灰＝CI 跨零（不下定論）",
                  fontsize=11, color=INK_PRIMARY, loc="left")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.grid(axis="x", linewidth=0.7, alpha=0.8, color=GRIDLINE)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return _save(fig, path, "04_segment_lift.png")


def plotOptOutSensitivity(roiSummary, path=None):
    """退訂率敏感度：利潤隨退訂率變化的折線，標示各組臨界退訂率。"""
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.axhline(0, color=BASELINE, linewidth=1)
    for arm, r in roiSummary["arms"].items():
        rates = [p["optOutRate"] for p in r["sensitivity"]]
        profits = [p["profit"] for p in r["sensitivity"]]
        color = ARM_COLORS[arm]
        ax.plot(rates, profits, color=color, linewidth=2, label=arm)
        be = r["breakEvenOptOut"]
        if be is not None and rates[0] <= be <= rates[-1]:
            ax.plot(be, 0, "o", color=color, markersize=7, zorder=5)
            ax.annotate(f"臨界 {be:.1%}", (be, 0), textcoords="offset points",
                        xytext=(6, 8), fontsize=9, color=color)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=1))
    ax.set_xlabel("假設退訂率")
    ax.set_ylabel("增量利潤（USD，扣退訂成本後）")
    ax.set_title("退訂成本敏感度：ROI 何時翻負", fontsize=12, color=INK_PRIMARY, loc="left")
    ax.legend(frameon=False, loc="upper right", fontsize=9)
    _cleanAxes(ax)
    fig.tight_layout()
    return _save(fig, path, "05_optout_sensitivity.png")


def _save(fig, path, defaultName):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    outPath = path or (FIG_DIR / defaultName)
    fig.savefig(outPath, dpi=150)
    plt.close(fig)
    return outPath
