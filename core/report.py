"""Excel and image report export (weekly/monthly)."""

from __future__ import annotations

import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd

from core import metrics


def export_report_xlsx(
    orders: pd.DataFrame,
    products: pd.DataFrame,
    marketing: pd.DataFrame,
    period_label: str,
) -> bytes:
    """Build a multi-sheet Excel report and return its bytes."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        summary = metrics.compute_summary(orders, products)
        overview_rows = [
            ["统计周期", period_label],
            ["总销售额", round(summary["销售额"], 2)],
            ["订单量", summary["订单量"]],
            ["客单价", round(summary["客单价"], 2)],
            ["退款率", f"{summary['退款率'] * 100:.1f}%"],
            ["毛利率", f"{summary['毛利率'] * 100:.1f}%"],
            ["总毛利", round(summary["毛利"], 2)],
        ]
        rfm = metrics.customer_rfm(orders)
        if not rfm.empty:
            overview_rows.append(["客户数", len(rfm)])
            overview_rows.append(["复购率", f"{metrics.repurchase_rate(orders) * 100:.1f}%"])
        if not marketing.empty:
            ms = metrics.marketing_summary(marketing)
            overview_rows.append(["推广总花费", round(ms["总花费"], 2)])
            overview_rows.append(["推广ROI", round(ms["ROI"], 2)])
        pd.DataFrame(overview_rows, columns=["指标", "数值"]).to_excel(writer, index=False, sheet_name="概览")

        trend = metrics.trend_by_period(orders, "D")
        if not trend.empty:
            trend.to_excel(writer, index=False, sheet_name="每日趋势")

        top = metrics.top_products(orders, products, metrics.SALES, 20)
        if not top.empty:
            top.to_excel(writer, index=False, sheet_name="TOP商品")

        cat = metrics.category_summary(orders, products)
        if not cat.empty:
            cat.to_excel(writer, index=False, sheet_name="类目分析")

        if not rfm.empty:
            metrics.rfm_segments(orders).to_excel(writer, index=False, sheet_name="客户分层")

        if not marketing.empty:
            metrics.marketing_by_channel(marketing).to_excel(writer, index=False, sheet_name="营销渠道")

    return buf.getvalue()


def _setup_chinese_font() -> None:
    for font in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf"]:
        try:
            if Path(font).exists():
                fm.fontManager.addfont(font)
        except Exception:  # noqa: BLE001
            pass
    plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei"]
    plt.rcParams["axes.unicode_minus"] = False


def render_report_image(
    orders: pd.DataFrame,
    products: pd.DataFrame,
    marketing: pd.DataFrame,
    period_label: str,
) -> bytes:
    """Render a PNG one-page visual report (weekly/monthly)."""
    _setup_chinese_font()
    summary = metrics.compute_summary(orders, products)

    fig, axes = plt.subplots(3, 2, figsize=(16, 20))
    fig.suptitle(f"{period_label} 经营报告", fontsize=22, fontweight="bold", y=0.985)

    header = (
        f"销售额 ¥{summary['销售额']:,.0f}   订单 {summary['订单量']}   客单价 ¥{summary['客单价']:,.0f}   "
        f"退款率 {summary['退款率']*100:.1f}%   毛利率 {summary['毛利率']*100:.1f}%   毛利 ¥{summary['毛利']:,.0f}"
    )
    fig.text(0.5, 0.955, header, ha="center", fontsize=13, color="#444444")

    ax = axes[0][0]
    trend = metrics.trend_by_period(orders, "D")
    if not trend.empty:
        ax.plot(trend["期间"], trend["销售额"], marker="o", linewidth=2, color="#e84343")
        ax.set_title("每日销售额趋势", fontsize=13)
        ax.tick_params(axis="x", rotation=45, labelsize=9)
        ax.grid(axis="y", alpha=0.3)
    else:
        ax.set_title("每日销售额趋势（暂无数据）", fontsize=13)

    ax = axes[0][1]
    top = metrics.top_products(orders, products, metrics.SALES, 10)
    if not top.empty:
        data = top.sort_values("销售额").tail(10)
        ax.barh(data["商品名称"], data["销售额"], color="#f59e0b")
        ax.set_title("TOP10 商品（销售额）", fontsize=13)
        ax.tick_params(axis="y", labelsize=9)
        ax.grid(axis="x", alpha=0.3)
    else:
        ax.set_title("TOP10 商品（暂无数据）", fontsize=13)

    ax = axes[1][0]
    cat = metrics.category_summary(orders, products)
    if not cat.empty:
        ax.pie(cat["销售额"], labels=cat["类目"], autopct="%.1f%%", startangle=90)
        ax.set_title("类目销售占比", fontsize=13)
    else:
        ax.set_title("类目分析（需商品数据）", fontsize=13)

    ax = axes[1][1]
    if not marketing.empty:
        by_channel = metrics.marketing_by_channel(marketing).sort_values("ROI")
        ax.barh(by_channel["渠道"], by_channel["ROI"], color="#2563eb")
        ax.axvline(1.0, color="red", linestyle="--", linewidth=1.5)
        ax.set_title("各渠道 ROI（红线=盈亏线1.0）", fontsize=13)
        ax.tick_params(axis="y", labelsize=9)
    else:
        ax.set_title("营销 ROI（暂无推广数据）", fontsize=13)

    ax = axes[2][0]
    rfm = metrics.customer_rfm(orders)
    if not rfm.empty:
        segments = metrics.rfm_segments(orders).sort_values("客户数")
        ax.barh(segments["客户分层"], segments["客户数"], color="#10b981")
        ax.set_title("客户价值分层（RFM）", fontsize=13)
        ax.tick_params(axis="y", labelsize=9)
    else:
        ax.set_title("客户分层（需买家ID）", fontsize=13)

    ax = axes[2][1]
    bands = metrics.price_band_analysis(orders)
    if not bands.empty:
        ax.bar(bands["价格带"], bands["销售额"], color="#8b5cf6")
        ax.set_title("价格带销售额分布", fontsize=13)
        ax.tick_params(axis="x", labelsize=9)
    else:
        ax.set_title("价格带分析（暂无数据）", fontsize=13)

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()
