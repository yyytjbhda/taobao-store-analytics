"""经营建议：根据数据自动给出可执行的运营建议。"""

import streamlit as st

from core import insights, metrics, storage, ui

LEVEL_STYLE = {
    "高": ("🔴", "#dc2626"),
    "中": ("🟠", "#d97706"),
    "低": ("🟡", "#ca8a04"),
}


def render() -> None:
    mode, orders, products = ui.load_data()
    st.title("💡 经营建议")
    st.caption("系统根据订单、商品、营销、客户数据自动生成的经营结论与建议，供复盘和决策参考。")

    if orders.empty:
        st.info("当前数据源暂无订单数据，无法生成建议。")
        return

    marketing = storage.load_marketing(mode)

    summary = metrics.compute_summary(orders, products)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总销售额", ui.fmt_money(summary["销售额"]))
    c2.metric("总毛利", ui.fmt_money(summary["毛利"]))
    c3.metric("毛利率", ui.fmt_pct(summary["毛利率"]))
    c4.metric("退款率", ui.fmt_pct(summary["退款率"]))
    if not marketing.empty:
        ms = metrics.marketing_summary(marketing)
        c4.metric("推广 ROI", f"{ms['ROI']:.2f}")

    all_insights = insights.generate_insights(orders, products, marketing)
    if not all_insights:
        st.success("当前数据表现健康，暂无特别建议。")
        return

    st.subheader("建议列表")
    for item in all_insights:
        icon, color = LEVEL_STYLE.get(item["级别"], ("⚪", "#666666"))
        st.markdown(
            f"### {icon} [{item['类别']}] {item['标题']}",
        )
        st.markdown(f"**数据依据**：{item['数据']}")
        st.markdown(f"**建议**：{item['建议']}")
        st.divider()

    st.caption(f"共 {len(all_insights)} 条建议，按严重程度排序。建议基于规则自动生成，仅供参考。")


render()
