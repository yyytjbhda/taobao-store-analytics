"""客户分析：复购率、RFM 客户分层。"""

import plotly.express as px
import streamlit as st

from core import metrics, ui


def render() -> None:
    mode, orders, _ = ui.load_data()
    st.title("👥 客户分析")
    st.caption("基于订单中的「买家ID」分析复购与客户价值。订单导入时请填写买家ID。")

    if orders.empty:
        st.info("当前数据源暂无订单数据。")
        return

    rfm = metrics.customer_rfm(orders)
    if rfm.empty:
        st.warning("订单数据中没有「买家ID」字段，无法进行客户分析。请导入包含买家ID的订单 Excel。")
        return

    repurchase = metrics.repurchase_rate(orders)
    total_customers = len(rfm)
    repeat_customers = int((rfm["购买次数"] >= 2).sum())
    avg_amount = rfm["总金额"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("客户总数", f"{total_customers} 人")
    c2.metric("复购客户", f"{repeat_customers} 人")
    c3.metric("复购率", ui.fmt_pct(repurchase))
    c4.metric("人均消费", ui.fmt_money(avg_amount))

    st.subheader("客户价值分层（RFM）")
    segments = metrics.rfm_segments(orders)
    if not segments.empty:
        fig = px.bar(
            segments.sort_values("客户数"),
            x="客户数", y="客户分层", orientation="h", color="客户分层",
        )
        fig.update_layout(height=380, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(segments, use_container_width=True, hide_index=True)
        st.caption("分层逻辑：R=最近购买时间、F=购买次数、M=消费金额，按中位数划分高低。")

    st.subheader("高价值客户明细")
    high_value = rfm[rfm["客户分层"].isin(["重要价值客户", "重要保持客户", "重要发展客户", "重要挽留客户"])]
    show = high_value[["买家ID", "最近购买", "购买次数", "总金额", "客户分层"]]
    st.dataframe(
        show,
        use_container_width=True,
        hide_index=True,
        column_config={"总金额": st.column_config.NumberColumn(format="¥%.2f")},
    )

    st.subheader("客户明细（全部）")
    st.dataframe(
        rfm[["买家ID", "最近购买", "购买次数", "总金额", "最近天数", "客户分层"]],
        use_container_width=True,
        hide_index=True,
        column_config={"总金额": st.column_config.NumberColumn(format="¥%.2f")},
    )


render()
