"""数据管理：导入、切换、概览、清除。"""

from datetime import datetime

import pandas as pd
import streamlit as st

from core import report, storage, ui


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


def export_section(mode)
clear_section() -> None:
    st.subheader("清除「我的数据」")
    st.caption("将删除我的数据中的全部订单、商品与 SOP 流程（不可恢复）。演示数据不受影响。")
    if st.checkbox("我确认要清除我的数据", key="clear_confirm"):
        if st.button("执行清除", key="clear_btn"):
            storage.save_orders(pd.DataFrame(), storage.MODE_USER)
            storage.save_products(pd.DataFrame(), storage.MODE_USER)
            storage.save_sop_flows([], storage.MODE_USER)
            st.success("已清除。")
            st.rerun()


mode, _, _ = ui.load_data()
st.title("🗂️ 数据管理")
overview(mode)
demo_status()
import_section()
export_section(mode)
clear_section()


