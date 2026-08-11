"""Shared UI helpers for the workbench."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from core import storage, style

MODE_LABELS = {
    storage.MODE_DEMO: "演示数据（淘宝真实数据）",
    storage.MODE_USER: "我的数据（导入）",
}


def init_state() -> None:
    if "data_mode" not in st.session_state:
        st.session_state.data_mode = storage.MODE_DEMO


def mode_selector() -> str:
    """Sidebar data source selector, returns the current mode."""
    init_state()
    style.sidebar_brand()
    mode = st.sidebar.radio(
        "数据源",
        [storage.MODE_DEMO, storage.MODE_USER],
        format_func=lambda m: MODE_LABELS[m],
        key="data_mode",
    )
    return mode


def load_data() -> tuple[str, pd.DataFrame, pd.DataFrame]:
    mode = mode_selector()
    orders = storage.load_orders(mode)
    products = storage.load_products(mode)
    return mode, orders, products


def fmt_money(v: float) -> str:
    return f"¥{v:,.2f}"


def fmt_pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def data_range_hint(orders: pd.DataFrame) -> None:
    if orders.empty:
        return
    lo = orders["成交时间"].min()
    hi = orders["成交时间"].max()
    st.caption(f"数据时间范围：{lo:%Y-%m-%d} 至 {hi:%Y-%m-%d}，共 {len(orders)} 条订单记录")
