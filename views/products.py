"""商品管理：商品档案、毛利计算、库存预警。"""

import pandas as pd
import streamlit as st

from core import metrics, storage, ui


def import_section() -> None:
    st.subheader("导入商品（Excel）")
    col1, col2 = st.columns([3, 1])
    with col1:
        file = st.file_uploader("上传商品 Excel（按模板整理）", type=["xlsx"], key="product_upload")
    with col2:
        st.download_button(
            "下载商品模板",
            data=storage.make_product_template_bytes(),
            file_name="商品导入模板.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_product_tpl",
        )
    if file is not None:
        df, errors = storage.import_products_excel(file)
        if errors:
            st.error("导入失败，请修正后重试：")
            for e in errors:
                st.write(f"- {e}")
            return
        existing = storage.load_products(storage.MODE_USER)
        merged = pd.concat([existing, df], ignore_index=True).drop_duplicates(
            subset=["商品ID"], keep="last"
        )
        storage.save_products(merged, storage.MODE_USER)
        st.success(f"导入成功：{len(df)} 条商品已保存到「我的数据」。")


def add_form() -> None:
    with st.expander("＋ 手动新增商品"):
        with st.form("add_product_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            product_id = c1.text_input("商品ID *")
            name = c2.text_input("商品名称 *")
            category = c1.text_input("类目")
            sku = c2.text_input("SKU")
            cost = c1.number_input("成本价 *", min_value=0.0, value=0.0, step=0.01)
            price = c2.number_input("销售价 *", min_value=0.0, value=0.0, step=0.01)
            stock = c1.number_input("库存数量", min_value=0, value=0, step=1)
            threshold = c2.number_input("库存预警阈值", min_value=0, value=0, step=1)
            status = st.selectbox("上架状态", ["上架", "下架"])
            submitted = st.form_submit_button("保存")
        if submitted:
            if not (product_id and name):
                st.error("请填写商品ID和商品名称。")
                return
            row = pd.DataFrame([{
                "商品ID": product_id, "商品名称": name, "类目": category, "SKU": sku,
                "成本价": cost, "销售价": price, "库存数量": stock,
                "库存预警阈值": threshold, "上架状态": status,
            }])
            existing = storage.load_products(storage.MODE_USER)
            storage.save_products(pd.concat([existing, row], ignore_index=True), storage.MODE_USER)
            st.success("商品已保存到「我的数据」。")
            st.rerun()


def edit_form() -> None:
    products = storage.load_products(storage.MODE_USER)
    if products.empty:
        return
    with st.expander("✏️ 修改 / 删除商品"):
        pid = st.selectbox("选择商品", sorted(products["商品ID"].astype(str).unique()))
        row = products[products["商品ID"].astype(str) == pid].iloc[0]
        c1, c2 = st.columns(2)
        new_cost = c1.number_input("成本价", value=float(row["成本价"]), step=0.01, key="edit_cost")
        new_price = c2.number_input("销售价", value=float(row["销售价"]), step=0.01, key="edit_price")
        new_stock = c1.number_input("库存数量", value=int(row["库存数量"]), step=1, key="edit_stock")
        new_threshold = c2.number_input("库存预警阈值", value=int(row["库存预警阈值"]), step=1, key="edit_threshold")
        b1, b2 = st.columns(2)
        if b1.button("保存修改", key="save_edit_product"):
            idx = products["商品ID"].astype(str) == pid
            products.loc[idx, ["成本价", "销售价", "库存数量", "库存预警阈值"]] = [new_cost, new_price, new_stock, new_threshold]
            storage.save_products(products, storage.MODE_USER)
            st.success("已保存。")
            st.rerun()
        if b2.button("删除该商品", key="del_product"):
            products = products[products["商品ID"].astype(str) != pid]
            storage.save_products(products, storage.MODE_USER)
            st.success("已删除。")
            st.rerun()


def list_section(mode: str) -> None:
    st.subheader("商品列表")
    products = storage.load_products(mode)
    if products.empty:
        st.info("当前数据源暂无商品数据。")
        return
    table = metrics.product_margin_table(products)
    q = st.text_input("搜索商品名称/ID", key="product_search")
    if q:
        table = table[table["商品名称"].astype(str).str.contains(q, na=False) |
                       table["商品ID"].astype(str).str.contains(q, na=False)]
    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        column_config={
            "成本价": st.column_config.NumberColumn(format="¥%.2f"),
            "销售价": st.column_config.NumberColumn(format="¥%.2f"),
            "毛利": st.column_config.NumberColumn(format="¥%.2f"),
            "毛利率": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )


mode, _, _ = ui.load_data()
st.title("🛒 商品管理")
import_section()
if mode == storage.MODE_USER:
    add_form()
    edit_form()
else:
    st.caption("提示：手动新增/修改商品需切换到「我的数据」数据源（左侧）。")
list_section(mode)

