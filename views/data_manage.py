"""数据管理：导入、切换、概览、质量检查、报表导出、清除。"""

from datetime import datetime

import pandas as pd
import streamlit as st

from core import quality, report, storage, ui


def overview(mode: str) -> None:
    st.subheader("当前数据概览")
    orders = storage.load_orders(mode)
    products = storage.load_products(mode)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("数据源", "演示数据" if mode == storage.MODE_DEMO else "我的数据")
    c2.metric("订单记录", len(orders))
    c3.metric("商品数", len(products))
    if orders.empty:
        c4.metric("时间范围", "—")
    else:
        c4.metric("时间范围", f"{orders['成交时间'].min():%Y-%m-%d} ~ {orders['成交时间'].max():%Y-%m-%d}")


def demo_status() -> None:
    st.subheader("演示数据状态")
    demo_orders = storage.load_orders(storage.MODE_DEMO)
    if demo_orders.empty:
        st.warning("演示数据尚未配置。请稍后在项目目录运行数据初始化脚本，或联系开发补充。")
    else:
        demo_products = storage.load_products(storage.MODE_DEMO)
        st.success(
            f"演示数据已就绪：{len(demo_orders)} 条订单、{len(demo_products)} 个商品。"
            "可在左侧数据源切换到「演示数据」查看。"
        )


def import_section() -> None:
    st.subheader("导入我的数据（Excel）")
    t1, t2 = st.tabs(["订单导入", "商品导入"])
    with t1:
        col1, col2 = st.columns([3, 1])
        with col1:
            file = st.file_uploader("上传订单 Excel（按模板格式）", type=["xlsx"], key="dm_order_upload")
        with col2:
            st.download_button(
                "下载订单模板",
                data=storage.make_order_template_bytes(),
                file_name="订单导入模板.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dm_dl_order",
            )
        if file is not None:
            df, errors = storage.import_orders_excel(file)
            if errors:
                st.error("导入失败：")
                for e in errors:
                    st.markdown(f"- {e}")
            else:
                existing = storage.load_orders(storage.MODE_USER)
                merged = pd.concat([existing, df], ignore_index=True).drop_duplicates(
                    subset=["订单号", "商品ID"], keep="last"
                )
                storage.save_orders(merged, storage.MODE_USER)
                st.success(f"订单导入成功：{len(df)} 条已保存到「我的数据」。")
                st.rerun()
    with t2:
        col1, col2 = st.columns([3, 1])
        with col1:
            file = st.file_uploader("上传商品 Excel（按模板格式）", type=["xlsx"], key="dm_product_upload")
        with col2:
            st.download_button(
                "下载商品模板",
                data=storage.make_product_template_bytes(),
                file_name="商品导入模板.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dm_dl_product",
            )
        if file is not None:
            df, errors = storage.import_products_excel(file)
            if errors:
                st.error("导入失败：")
                for e in errors:
                    st.markdown(f"- {e}")
            else:
                existing = storage.load_products(storage.MODE_USER)
                merged = pd.concat([existing, df], ignore_index=True).drop_duplicates(
                    subset=["商品ID"], keep="last"
                )
                storage.save_products(merged, storage.MODE_USER)
                st.success(f"商品导入成功：{len(df)} 条已保存到「我的数据」。")
                st.rerun()


def export_section(mode: str) -> None:
    st.subheader("导出经营报表")
    orders = storage.load_orders(mode)
    if orders.empty:
        st.info("当前数据源无订单，无法导出。")
        return
    products = storage.load_products(mode)
    marketing = storage.load_marketing(mode)
    period_label = st.text_input("报表名称/周期", value=f"{datetime.now():%Y-%m}经营报表")
    data = report.export_report_xlsx(orders, products, marketing, period_label)
    img = report.render_report_image(orders, products, marketing, period_label)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "下载 Excel 报表",
            data=data,
            file_name=f"{period_label}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_report",
        )
    with c2:
        st.download_button(
            "下载图片版报告（PNG）",
            data=img,
            file_name=f"{period_label}.png",
            mime="image/png",
            key="dl_report_img",
        )
    st.caption("Excel 报表包含：概览、每日趋势、TOP商品、类目分析、客户分层、营销渠道；PNG 为单页可视化报告。")


def clear_section() -> None:
    st.subheader("清除「我的数据」")
    st.caption("将删除我的数据中的全部订单、商品、营销记录与 SOP 流程（不可恢复）。演示数据不受影响。")
    if st.checkbox("我确认要清除我的数据", key="clear_confirm"):
        if st.button("执行清除", key="clear_btn"):
            storage.save_orders(pd.DataFrame(), storage.MODE_USER)
            storage.save_products(pd.DataFrame(), storage.MODE_USER)
            storage.save_marketing(pd.DataFrame(), storage.MODE_USER)
            storage.save_sop_flows([], storage.MODE_USER)
            st.success("已清除。")
            st.rerun()


def quality_section(mode: str) -> None:
    st.subheader("数据质量检查")
    orders = storage.load_orders(mode)
    if orders.empty:
        st.info("当前数据源无订单，无法检查。")
        return
    issues = quality.check_order_quality(orders)
    qs = quality.quality_summary(issues)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("问题总数", qs["总数"])
    c2.metric("高优先级", qs["高"])
    c3.metric("中优先级", qs["中"])
    c4.metric("低优先级", qs["低"])
    level = st.selectbox("按级别筛选", ["全部", "高", "中", "低"], key="quality_level")
    view = issues if level == "全部" else issues[issues["级别"] == level]
    if view.empty:
        st.success("未发现数据质量问题。")
    else:
        st.dataframe(view.head(100), width="stretch", hide_index=True)
        if len(view) > 100:
            st.caption(f"共 {len(view)} 条问题，仅展示前 100 条。")
    st.caption("检查项：字段缺失、时间异常、数量异常、金额异常、重复记录。异常订单建议修正后重新导入。")


mode, _, _ = ui.load_data()
st.title("🗂️ 数据管理")
overview(mode)
demo_status()
quality_section(mode)
import_section()
export_section(mode)
clear_section()
