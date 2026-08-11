"""交易分析：趋势、退款、时段、店铺维度。"""

import streamlit as st
import plotly.express as px

from core import metrics, ui

FREQ_LABELS = {"D": "按日", "W": "按周", "M": "按月"}


def render() -> None:
    _, orders, _ = ui.load_data()
    st.title("📈 交易分析")

    if orders.empty:
        st.info("当前数据源暂无订单数据。")
        return

    ui.data_range_hint(orders)

    st.subheader("销售趋势")
    freq = st.radio("汇总维度", ["D", "W", "M"], format_func=lambda f: FREQ_LABELS[f], horizontal=True, key="trend_freq")
    trend = metrics.trend_by_period(orders, freq)
    if not trend.empty:
        fig = px.line(trend, x="期间", y=metrics.SALES, markers=True, title="销售额趋势")
        fig.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, width="stretch")
        st.dataframe(trend, width="stretch", hide_index=True)

    st.subheader("退款分析")
    refund_by_day = metrics.refund_rate_by_day(orders)
    if not refund_by_day.empty:
        fig = px.bar(refund_by_day, x="日期", y=metrics.REFUND_RATE, title="每日退款率")
        fig.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, width="stretch")
    refund_detail = metrics.refund_analysis(orders)
    st.caption(f"退款订单明细（{len(refund_detail)} 条）")
    if not refund_detail.empty:
        st.dataframe(
            refund_detail[["订单号", "成交时间", "商品名称", "数量", "实付金额"]],
            width="stretch",
            hide_index=True,
            column_config={"实付金额": st.column_config.NumberColumn(format="¥%.2f")},
        )

    st.subheader("下单时段分布")
    hours = metrics.hour_distribution(orders)
    if not hours.empty:
        fig = px.bar(hours, x="时段", y=metrics.ORDER_CNT, title="各时段订单量")
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, width="stretch")

    st.subheader("店铺维度对比")
    store = metrics.store_summary(orders)
    if not store.empty and len(store) > 1:
        fig = px.bar(store, x="店铺", y=metrics.SALES, title="各店铺销售额")
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, width="stretch")
    else:
        st.caption("演示数据不含多店铺字段，暂无法对比（后续可扩展）。")


render()

