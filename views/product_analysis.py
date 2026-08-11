"""商品分析：TOP 排行、利润贡献、类目分析。"""

import streamlit as st
import plotly.express as px

from core import metrics, ui

METRIC_LABELS = {metrics.SALES: "销售额", metrics.ORDER_CNT: "订单量", metrics.GROSS_PROFIT: "毛利"}


def render() -> None:
    _, orders, products = ui.load_data()
    st.title("🏆 商品分析")

    if orders.empty:
        st.info("当前数据源暂无订单数据。")
        return

    st.subheader("TOP 商品排行")
    metric = st.radio("排行指标", [metrics.SALES, metrics.ORDER_CNT, metrics.GROSS_PROFIT],
                      format_func=lambda m: METRIC_LABELS[m], horizontal=True, key="top_metric")
    top_n = st.slider("展示数量", 5, 20, 10, key="top_n")
    top = metrics.top_products(orders, products, metric, top_n)
    if not top.empty:
        value_col = list(top.columns)[-1]
        fig = px.bar(top.sort_values(value_col), x=value_col, y="商品名称", orientation="h",
                     title=f"TOP {top_n} 商品（按{METRIC_LABELS.get(metric, value_col)}）")
        fig.update_layout(height=max(360, 40 * len(top)), margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, width="stretch")
        st.dataframe(top, width="stretch", hide_index=True)

    st.subheader("利润贡献分析（帕累托）")
    contrib = metrics.profit_contribution(orders, products)
    if not contrib.empty:
        fig = px.line(contrib, x="商品名称", y="累计利润占比", markers=True, title="累计利润占比曲线")
        fig.add_hline(y=0.8, line_dash="dash", line_color="red")
        fig.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, width="stretch")
        st.dataframe(contrib[["商品ID", "商品名称", "毛利", "累计利润占比"]], width="stretch", hide_index=True)
        top80 = contrib[contrib["累计利润占比"] <= 0.8]
        st.caption(f"前 {len(top80)} 个商品贡献了 80% 的利润（共 {len(contrib)} 个在售商品）。")

    st.subheader("类目分析")
    cat = metrics.category_summary(orders, products)
    if cat.empty:
        st.caption("需先导入商品数据（含类目）才能做类目分析。")
    else:
        fig = px.bar(cat, x="类目", y=metrics.SALES, title="各类目销售额")
        fig.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, width="stretch")
        st.dataframe(cat, width="stretch", hide_index=True)


    st.subheader("价格带分析")
    bands = metrics.price_band_analysis(orders)
    if not bands.empty:
        fig = px.bar(bands, x="价格带", y="销售额", title="各价格带销售额")
        fig.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, width="stretch")
        st.dataframe(bands, width="stretch", hide_index=True)

    st.subheader("滞销识别（建议清仓/下架）")
    slow = metrics.slow_movers(orders, products)
    if slow.empty:
        st.success("暂无滞销商品。")
    else:
        st.dataframe(slow.head(20), width="stretch", hide_index=True)
        st.caption(f"滞销定义：有库存且累计销量不足 3 件。共识别 {len(slow)} 个，展示前 20 个。")

render()


