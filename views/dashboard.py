"""仪表盘：经营总况一屏概览。"""

import streamlit as st
import pandas as pd
import plotly.express as px

from core import metrics, storage, ui


def filter_orders(orders: pd.DataFrame, period: str) -> pd.DataFrame:
    if orders.empty:
        return orders
    now = orders["成交时间"].max()
    if period == "近7天":
        start = now - pd.Timedelta(days=7)
    elif period == "近30天":
        start = now - pd.Timedelta(days=30)
    elif period == "本月":
        start = now.replace(day=1)
    else:
        return orders
    return orders[orders["成交时间"] >= start]


def render() -> None:
    mode, orders, products = ui.load_data()
    st.title("📊 经营仪表盘")

    if orders.empty:
        ui.data_range_hint(orders)
        st.info("当前数据源暂无订单数据。请到左侧「数据管理」页面导入 Excel，或切换数据源。")
        return

    ui.data_range_hint(orders)
    period = st.radio(
        "统计范围", ["全部", "近7天", "近30天", "本月"], horizontal=True, key="dash_period"
    )
    filtered = filter_orders(orders, period)

    summary = metrics.compute_summary(filtered, products)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("总销售额", ui.fmt_money(summary["销售额"]))
    c2.metric("订单量", f"{summary['订单量']} 单")
    c3.metric("客单价", ui.fmt_money(summary["客单价"]))
    c4.metric("退款率", ui.fmt_pct(summary["退款率"]))
    c5.metric("毛利率", ui.fmt_pct(summary["毛利率"]))
    c6.metric("总毛利", ui.fmt_money(summary["毛利"]))

    with st.container(border=True):
        st.subheader("销售趋势")
        trend = metrics.trend_by_period(filtered, "D")
        if not trend.empty:
            fig = px.line(trend, x="期间", y="销售额", markers=True)
            fig.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, width="stretch")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader("TOP 10 商品（销售额）")
            top = metrics.top_products(filtered, products, metrics.SALES, 10)
            if not top.empty:
                fig = px.bar(
                    top.sort_values("销售额"),
                    x="销售额",
                    y="商品名称",
                    orientation="h",
                )
                fig.update_layout(height=360, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, width="stretch")
    with right:
        with st.container(border=True):
            st.subheader("类目销售占比")
            cat = metrics.category_summary(filtered, products)
            if cat.empty:
                st.caption("需先导入商品数据（含类目）")
            else:
                fig = px.pie(cat, names="类目", values="销售额", hole=0.4)
                fig.update_layout(height=360, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, width="stretch")

    with st.container(border=True):
        st.subheader("库存预警")
        alerts = metrics.inventory_alert(products)
        if alerts.empty:
            st.success("暂无库存预警，库存均在安全水平。")
        else:
            show = alerts[["商品ID", "商品名称", "库存数量", "库存预警阈值"]]
            st.dataframe(show, width="stretch", hide_index=True)

    if summary["退款订单数"] > 0:
        st.warning(f"当前范围有 {summary['退款订单数']} 笔退款订单，详见「交易分析」。")
    else:
        st.caption(f"当前范围退款订单 0 笔。")


render()

