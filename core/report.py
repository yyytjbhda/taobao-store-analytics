"""Excel report export (weekly/monthly)."""

from __future__ import annotations

import io

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
