"""仪表盘：经营总况一屏概览（KPI 卡片含同环比与口径标注）。"""

import streamlit as st
import pandas as pd
import plotly.express as px

from core import metrics, storage, ui

PERIODS = ["全部", "近7天", "近30天", "本月"]


def split_windows(
    orders: pd.DataFrame, period: str
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (current, previous, year-over-year) windows for the period."""
    if orders.empty:
        return orders, orders, orders
    now = orders["成交时间"].max()
    if period == "全部":
        empty = pd.DataFrame(columns=orders.columns)
        return orders, empty, empty
    if period == "近7天":
        cur_start = now - pd.Timedelta(days=7)
        prev_start = cur_start - pd.Timedelta(days=7)
    elif period == "近30天":
        cur_start = now - pd.Timedelta(days=30)
        prev_start = cur_start - pd.Timedelta(days=30)
    else:  # 本月
        cur_start = now.replace(day=1)
        prev_start = (cur_start - pd.Timedelta(days=1)).replace(day=1)

    cur = orders[orders["成交时间"] >= cur_start]
    prev = orders[(orders["成交时间"] >= prev_start) & (orders["成交时间"] < cur_start)]
    yoy = orders[
        (orders["成交时间"] >= cur_start - pd.Timedelta(days=365))
        & (orders["成交时间"] < now - pd.Timedelta(days=365))
    ]
    return cur, prev, yoy


def _delta_html(label: str, delta, is_rate: bool, bad_when_up: bool) -> str:
    """Colored mom/yoy chip: green up unless the metric is bad when rising."""
    if delta is None:
        return f'<span class="flat">{label} —</span>'
    text = f"{label} {delta:+.1f}pp" if is_rate else f"{label} {delta:+.1f}%"
    if abs(delta) < 0.05:
        cls = "flat"
    else:
        rises_bad = (delta > 0) == bad_when_up
        cls = "down" if rises_bad else "up"
    return f'<span class="{cls}">{text}</span>'


def kpi_cards_html(summary: dict, compare: dict) -> str:
    cards = [
        ("总销售额", metrics.SALES, ui.fmt_money(summary[metrics.SALES]), "Σ实付金额（剔除退款）"),
        ("订单量", metrics.ORDER_CNT, f"{summary[metrics.ORDER_CNT]} 单", "非退款订单数（订单号去重）"),
        ("客单价", metrics.AOV, ui.fmt_money(summary[metrics.AOV]), "销售额 ÷ 订单量"),
        ("退款率", metrics.REFUND_RATE, ui.fmt_pct(summary[metrics.REFUND_RATE]), "退款订单 ÷ 总订单"),
        ("毛利率", metrics.GROSS_MARGIN, ui.fmt_pct(summary[metrics.GROSS_MARGIN]), "毛利 ÷ 销售额"),
        ("总毛利", metrics.GROSS_PROFIT, ui.fmt_money(summary[metrics.GROSS_PROFIT]), "销售额 − Σ(成本×数量)"),
    ]
    parts = []
    for name, key, value, note in cards:
        is_rate = name in ("退款率", "毛利率")
        bad_when_up = name == "退款率"
        cmp = compare[key]
        delta_html = _delta_html("环比", cmp["mom"], is_rate, bad_when_up) + _delta_html(
            "同比", cmp["yoy"], is_rate, bad_when_up
        )
        parts.append(
            f'<div class="kpi-card"><div class="kpi-label">{name}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-delta">{delta_html}</div>'
            f'<div class="kpi-note">口径：{note}</div></div>'
        )
    return '<div class="kpi-grid">' + "".join(parts) + "</div>"


def render() -> None:
    mode, orders, products = ui.load_data()
    st.title("📊 经营仪表盘")

    if orders.empty:
        ui.data_range_hint(orders)
        return

    ui.data_range_hint(orders)
    period = st.radio("统计范围", PERIODS, horizontal=True, key="dash_period")
    cur, prev, yoy = split_windows(orders, period)

    summary = metrics.compute_summary(cur, products)
    compare = metrics.compare_summaries(summary, metrics.compute_summary(prev, products))
    yoy_cmp = metrics.compare_summaries(summary, metrics.compute_summary(yoy, products))
    for key in compare:
        compare[key]["yoy"] = yoy_cmp[key]["mom"]

    st.markdown(kpi_cards_html(summary, compare), unsafe_allow_html=True)
    st.caption("环比=较上一统计周期 ｜ 同比=较去年同期；环比/同比无可比数据时显示 —。")

    with st.container(border=True):
        st.subheader("销售趋势")
        trend = metrics.trend_by_period(cur, "D")
        if not trend.empty:
            fig = px.line(trend, x="期间", y="销售额", markers=True)
            fig.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, width="stretch")
            lo, hi = trend["期间"].iloc[0], trend["期间"].iloc[-1]
            st.caption(f"统计口径：实付金额合计（剔除退款），单位：元｜时间范围 {lo} ~ {hi}")
        else:
            st.info("当前统计范围暂无销售数据。")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader("TOP 10 商品（销售额）")
            top = metrics.top_products(cur, products, metrics.SALES, 10)
            if not top.empty:
                fig = px.bar(
                    top.sort_values("销售额"),
                    x="销售额",
                    y="商品名称",
                    orientation="h",
                )
                fig.update_layout(height=360, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, width="stretch")
                st.caption("口径：实付金额合计（剔除退款），单位：元")
            else:
                st.info("当前统计范围暂无销售数据。")
    with right:
        with st.container(border=True):
            st.subheader("类目销售占比")
            cat = metrics.category_summary(cur, products)
            if cat.empty:
                st.caption("需先导入商品数据（含类目）")
            else:
                fig = px.pie(cat, names="类目", values="销售额", hole=0.4)
                fig.update_layout(height=360, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, width="stretch")
                st.caption(
                    f"类目销售额合计 {ui.fmt_money(cat['销售额'].sum())}，单位：元｜占比按类目销售额计算"
                )

    with st.container(border=True):
        st.subheader("库存预警")
        alerts = metrics.inventory_alert(products)
        if alerts.empty:
            st.success("暂无库存预警，库存均在安全水平。")
        else:
            show = alerts[["商品ID", "商品名称", "库存数量", "库存预警阈值"]]
            st.dataframe(show, width="stretch", hide_index=True)
        st.caption("预警规则：库存数量 ≤ 库存预警阈值时触发。")

    if summary["退款订单数"] > 0:
        st.warning(f"当前范围有 {summary['退款订单数']} 笔退款订单，详见「交易分析」。")
    else:
        st.caption("当前范围退款订单 0 笔。")


render()