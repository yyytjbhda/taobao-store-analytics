"""订单管理：Excel 导入、查看、手动维护订单。"""

import pandas as pd
import streamlit as st

from core import storage, ui


def import_section() -> None:
    st.subheader("导入订单（Excel）")
    col1, col2 = st.columns([3, 1])
    with col1:
        file = st.file_uploader(
            "上传订单 Excel（请先下载模板，按模板整理数据）",
            type=["xlsx"],
            key="order_upload",
        )
    with col2:
        st.download_button(
            "下载订单模板",
            data=storage.make_order_template_bytes(),
            file_name="订单导入模板.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_order_tpl",
        )
    if file is not None:
        df, errors = storage.import_orders_excel(file)
        if errors:
            st.error("导入失败，请修正后重试：")
            for e in errors:
                st.write(f"- {e}")
            return
        existing = storage.load_orders(storage.MODE_USER)
        merged = pd.concat([existing, df], ignore_index=True).drop_duplicates(
            subset=["订单号", "商品ID"], keep="last"
        )
        storage.save_orders(merged, storage.MODE_USER)
        st.success(f"导入成功：{len(df)} 条记录已保存到「我的数据」。（左侧可切换查看）")


def add_form() -> None:
    with st.expander("＋ 手动新增订单"):
        with st.form("add_order_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            order_no = c1.text_input("订单号 *")
            product_id = c2.text_input("商品ID *")
            product_name = c1.text_input("商品名称 *")
            quantity = c1.number_input("数量 *", min_value=1, value=1, step=1)
            unit_price = c2.number_input("单价", min_value=0.0, value=0.0, step=0.01)
            paid = c1.number_input("实付金额 *", min_value=0.0, value=0.0, step=0.01)
            freight = c2.number_input("运费", min_value=0.0, value=0.0, step=0.01)
            discount = c1.number_input("优惠金额", min_value=0.0, value=0.0, step=0.01)
            refund_status = c2.selectbox("退款状态", ["未退款", "已退款"])
            order_status = c1.selectbox("订单状态", ["已完成", "处理中", "已退款"])
            d = c1.date_input("成交日期")
            t = c2.time_input("成交时间")
            note = st.text_input("备注")
            submitted = st.form_submit_button("保存")
        if submitted:
            if not (order_no and product_id and product_name):
                st.error("请填写订单号、商品ID、商品名称。")
                return
            dt = pd.Timestamp(d) + pd.Timedelta(hours=t.hour, minutes=t.minute)
            row = pd.DataFrame([{
                "订单号": order_no, "成交时间": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "商品ID": product_id, "商品名称": product_name, "数量": quantity,
                "单价": unit_price, "实付金额": paid, "运费": freight,
                "优惠金额": discount, "退款状态": refund_status,
                "订单状态": order_status, "备注": note,
            }])
            existing = storage.load_orders(storage.MODE_USER)
            storage.save_orders(pd.concat([existing, row], ignore_index=True), storage.MODE_USER)
            st.success("订单已保存到「我的数据」。")
            st.rerun()


def edit_form() -> None:
    orders = storage.load_orders(storage.MODE_USER)
    if orders.empty:
        return
    with st.expander("✏️ 修改 / 删除订单"):
        order_no = st.selectbox("选择订单号", sorted(orders["订单号"].astype(str).unique()))
        row = orders[orders["订单号"].astype(str) == order_no].iloc[0]
        c1, c2 = st.columns(2)
        new_paid = c1.number_input("实付金额", value=float(row["实付金额"]), step=0.01, key="edit_paid")
        new_qty = c2.number_input("数量", value=int(row["数量"]), min_value=1, step=1, key="edit_qty")
        new_refund = c1.selectbox("退款状态", ["未退款", "已退款"], index=0 if row["退款状态"] != "已退款" else 1, key="edit_refund")
        new_status = c2.selectbox("订单状态", ["已完成", "处理中", "已退款"], key="edit_status")
        b1, b2 = st.columns(2)
        if b1.button("保存修改", key="save_edit_order"):
            orders.loc[orders["订单号"].astype(str) == order_no, ["实付金额", "数量", "退款状态", "订单状态"]] = [new_paid, new_qty, new_refund, new_status]
            storage.save_orders(orders, storage.MODE_USER)
            st.success("已保存。")
            st.rerun()
        if b2.button("删除该订单（全部商品行）", key="del_order"):
            orders = orders[orders["订单号"].astype(str) != order_no]
            storage.save_orders(orders, storage.MODE_USER)
            st.success("已删除。")
            st.rerun()


def list_section(mode: str) -> None:
    st.subheader("订单列表")
    orders = storage.load_orders(mode)
    if orders.empty:
        st.info("当前数据源暂无订单。")
        return
    c1, c2, c3 = st.columns(3)
    refund_opt = c1.selectbox("退款状态", ["全部", "未退款", "已退款"])
    status_opt = c2.selectbox("订单状态", ["全部", "已完成", "处理中", "已退款"])
    q = c3.text_input("搜索订单号/商品", key="order_search")
    view = orders.copy()
    if refund_opt != "全部":
        view = view[view["退款状态"] == refund_opt]
    if status_opt != "全部":
        view = view[view["订单状态"] == status_opt]
    if q:
        view = view[view["订单号"].astype(str).str.contains(q, na=False) |
                    view["商品名称"].astype(str).str.contains(q, na=False)]
    show = view.sort_values("成交时间", ascending=False).reset_index(drop=True)
    st.dataframe(
        show,
        width="stretch",
        hide_index=True,
        column_config={
            "实付金额": st.column_config.NumberColumn(format="¥%.2f"),
            "单价": st.column_config.NumberColumn(format="¥%.2f"),
            "运费": st.column_config.NumberColumn(format="¥%.2f"),
            "优惠金额": st.column_config.NumberColumn(format="¥%.2f"),
        },
    )
    st.caption(f"共 {len(show)} 条记录（当前数据源）")


mode, _, _ = ui.load_data()
st.title("📦 订单管理")
import_section()
if mode == storage.MODE_USER:
    add_form()
    edit_form()
else:
    st.caption("提示：手动新增/修改订单需切换到「我的数据」数据源（左侧）。")
list_section(mode)

