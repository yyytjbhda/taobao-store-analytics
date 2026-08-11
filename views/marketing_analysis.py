"""营销分析：推广花费、ROI、渠道效果。"""

import pandas as pd
import plotly.express as px
import streamlit as st

from core import metrics, storage, ui


def add_form() -> None:
    with st.expander("＋ 手动新增推广记录"):
        with st.form("add_marketing_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            d = c1.date_input("日期 *")
            channel = c2.text_input("渠道 *（如：直通车、淘宝客、引力魔方）")
            spend = c1.number_input("花费 *", min_value=0.0, value=0.0, step=0.01)
            revenue = c2.number_input("成交金额", min_value=0.0, value=0.0, step=0.01)
            note = st.text_input("备注")
            submitted = st.form_submit_button("保存")
        if submitted:
            if not channel.strip():
                st.error("请填写渠道。")
                return
            row = pd.DataFrame([{
                "日期": d.strftime("%Y-%m-%d"), "渠道": channel.strip(),
                "花费": spend, "成交金额": revenue, "备注": note,
            }])
            existing = storage.load_marketing(storage.MODE_USER)
            storage.save_marketing(pd.concat([existing, row], ignore_index=True), storage.MODE_USER)
            st.success("推广记录已保存到「我的数据」。")
            st.rerun()


def import_section() -> None:
    with st.expander("📥 Excel 导入推广记录"):
        col1, col2 = st.columns([3, 1])
        with col1:
            file = st.file_uploader("上传推广 Excel（按模板格式）", type=["xlsx"], key="mkt_upload")
        with col2:
            st.download_button(
                "下载推广模板",
                data=storage.make_marketing_template_bytes(),
                file_name="推广记录模板.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_mkt_tpl",
            )
        if file is not None:
            df, errors = storage.import_marketing_excel(file)
            if errors:
                st.error("导入失败：")
                for e in errors:
                    st.markdown(f"- {e}")
            else:
                existing = storage.load_marketing(storage.MODE_USER)
                merged = pd.concat([existing, df], ignore_index=True)
                storage.save_marketing(merged, storage.MODE_USER)
                st.success(f"导入成功：{len(df)} 条已保存到「我的数据」。")
                st.rerun()


def render() -> None:
    mode, _, _ = ui.load_data()
    st.title("📣 营销分析")
    st.caption("记录推广花费与归因成交，自动计算 ROI。ROI = 成交金额 ÷ 花费")

    marketing = storage.load_marketing(mode)
    if marketing.empty:
        st.info("当前数据源暂无推广记录。可切换到演示数据，或录入/导入推广数据。")
        add_form()
        import_section()
        return

    summary = metrics.marketing_summary(marketing)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总花费", ui.fmt_money(summary["总花费"]))
    c2.metric("总成交金额", ui.fmt_money(summary["总成交金额"]))
    c3.metric("整体 ROI", f"{summary['ROI']:.2f}")
    c4.metric("记录数", f"{summary['记录数']} 条")
    ui.data_range_hint(marketing.rename(columns={"日期": "成交时间"}))

    st.subheader("渠道效果对比")
    by_channel = metrics.marketing_by_channel(marketing)
    if not by_channel.empty:
        fig = px.bar(by_channel, x="渠道", y="成交金额", title="各渠道成交金额", color="渠道")
        fig.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(by_channel, use_container_width=True, hide_index=True)

    st.subheader("每日花费与 ROI 趋势")
    trend = metrics.marketing_trend(marketing)
    if not trend.empty:
        fig = px.line(trend, x="日期", y="ROI", markers=True, title="每日 ROI")
        fig.add_hline(y=1.0, line_dash="dash", line_color="red")
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(trend, use_container_width=True, hide_index=True)

    if mode == storage.MODE_USER:
        add_form()
        import_section()
    else:
        st.caption("提示：录入/导入推广数据需切换到「我的数据」数据源（左侧）。")


render()
