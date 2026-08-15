"""Business metric calculations for the analytics workbench."""

from __future__ import annotations

import numpy as np
import pandas as pd

SALES = "销售额"
ORDER_CNT = "订单量"
AOV = "客单价"
REFUND_RATE = "退款率"
GROSS_PROFIT = "毛利"
GROSS_MARGIN = "毛利率"


def _non_refunded(orders: pd.DataFrame) -> pd.DataFrame:
    return orders[orders["退款状态"] != "已退款"]


def _pct_change(cur: float, prev: float) -> float | None:
    if prev is None or prev == 0 or cur is None:
        return None
    return (cur - prev) / prev * 100


def _pp_change(cur: float, prev: float) -> float | None:
    if prev is None or cur is None:
        return None
    return (cur - prev) * 100


def compare_summaries(cur: dict, prev: dict) -> dict:
    """MOM change for headline metrics vs the previous window.

    Growth metrics use percent change; rate metrics use percentage-point diff.
    Returns {metric: {"mom": float | None}}; yoy left for caller to fill.
    """
    growth = [SALES, ORDER_CNT, AOV, GROSS_PROFIT]
    rates = [REFUND_RATE, GROSS_MARGIN]
    out: dict = {}
    for k in growth:
        out[k] = {"mom": _pct_change(cur.get(k), prev.get(k)), "yoy": None}
    for k in rates:
        out[k] = {"mom": _pp_change(cur.get(k), prev.get(k)), "yoy": None}
    return out


def compute_summary(orders: pd.DataFrame, products: pd.DataFrame) -> dict:
    """Compute headline metrics from orders and products."""
    if orders.empty:
        return {
            SALES: 0.0, ORDER_CNT: 0, AOV: 0.0, REFUND_RATE: 0.0,
            GROSS_PROFIT: 0.0, GROSS_MARGIN: 0.0,
            "订单数": 0, "退款订单数": 0, "商品数": int(len(products)),
        }

    sales_df = _non_refunded(orders)
    total_sales = float(sales_df["实付金额"].sum())
    order_count = int(sales_df["订单号"].nunique())
    aov = total_sales / order_count if order_count else 0.0
    total_orders = int(orders["订单号"].nunique())
    refund_orders = int(orders[orders["退款状态"] == "已退款"]["订单号"].nunique())
    refund_rate = refund_orders / total_orders if total_orders else 0.0

    cost_sum = 0.0
    if not products.empty and "商品ID" in products.columns:
        merged = sales_df.merge(
            products[["商品ID", "成本价"]], on="商品ID", how="left"
        )
        cost_sum = float((merged["数量"] * merged["成本价"].fillna(0)).sum())

    gross_profit = total_sales - cost_sum
    gross_margin = gross_profit / total_sales if total_sales else 0.0

    return {
        SALES: total_sales, ORDER_CNT: order_count, AOV: aov, REFUND_RATE: refund_rate,
        GROSS_PROFIT: gross_profit, GROSS_MARGIN: gross_margin,
        "订单数": total_orders, "退款订单数": refund_orders, "商品数": int(len(products)),
    }


def trend_by_period(orders: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    """Daily/weekly/monthly sales trend. freq: D / W / M."""
    df = _non_refunded(orders).copy()
    if df.empty:
        return pd.DataFrame(columns=["期间", SALES, ORDER_CNT, AOV])
    df["期间"] = df["成交时间"].dt.to_period(freq).astype(str)
    trend = (
        df.groupby("期间")
        .agg(**{SALES: ("实付金额", "sum"), ORDER_CNT: ("订单号", "nunique")})
        .reset_index()
    )
    trend[AOV] = trend[SALES] / trend[ORDER_CNT].replace(0, pd.NA)
    return trend


def refund_analysis(orders: pd.DataFrame) -> pd.DataFrame:
    """Refund order details."""
    df = orders[orders["退款状态"] == "已退款"].copy()
    return df.sort_values("成交时间", ascending=False)


def refund_rate_by_day(orders: pd.DataFrame) -> pd.DataFrame:
    """Refund rate trend by day."""
    df = orders.copy()
    if df.empty:
        return pd.DataFrame(columns=["日期", "总订单数", "退款订单数", REFUND_RATE])
    df["日期"] = df["成交时间"].dt.date.astype(str)
    df["是否退款"] = (df["退款状态"] == "已退款").astype(int)
    total = df.groupby("日期")["订单号"].nunique().rename("总订单数")
    refund = df[df["是否退款"] == 1].groupby("日期")["订单号"].nunique().rename("退款订单数")
    result = pd.concat([total, refund], axis=1).fillna(0).reset_index()
    result[REFUND_RATE] = result["退款订单数"] / result["总订单数"].replace(0, pd.NA)
    return result


def hour_distribution(orders: pd.DataFrame) -> pd.DataFrame:
    """Order count by hour of day."""
    df = orders.copy()
    if df.empty:
        return pd.DataFrame(columns=["时段", ORDER_CNT])
    df["小时"] = df["成交时间"].dt.hour
    dist = df.groupby("小时").agg(**{ORDER_CNT: ("订单号", "nunique")}).reset_index()
    dist["时段"] = dist["小时"].astype(str) + ":00"
    return dist


def store_summary(orders: pd.DataFrame) -> pd.DataFrame:
    """Sales comparison across stores/platforms."""
    df = _non_refunded(orders).copy()
    if df.empty:
        return pd.DataFrame(columns=["店铺", SALES, ORDER_CNT])
    df["店铺"] = df["商品ID"].str.extract(r"^([A-Za-z]{1,4})", expand=False).fillna("其他")
    grouped = (
        df.groupby("店铺")
        .agg(**{SALES: ("实付金额", "sum"), ORDER_CNT: ("订单号", "nunique")})
        .reset_index()
        .sort_values(SALES, ascending=False)
    )
    return grouped


def top_products(
    orders: pd.DataFrame, products: pd.DataFrame, metric: str = SALES, top_n: int = 10
) -> pd.DataFrame:
    """Top products by sales / order count / profit."""
    df = _non_refunded(orders).copy()
    if df.empty or "商品ID" not in df.columns:
        return pd.DataFrame(columns=["商品ID", "商品名称", metric])

    if metric == ORDER_CNT:
        result = (
            df.groupby(["商品ID", "商品名称"])
            .agg(**{ORDER_CNT: ("订单号", "nunique")})
            .reset_index()
        )
    elif metric == SALES:
        result = df.groupby(["商品ID", "商品名称"]).agg(
            **{SALES: ("实付金额", "sum")}
        ).reset_index()
    else:  # 毛利
        cost_map = {}
        if not products.empty and "商品ID" in products.columns:
            cost_map = dict(zip(products["商品ID"], products["成本价"].fillna(0)))
        df["成本"] = df["商品ID"].map(cost_map).fillna(0) * df["数量"]
        result = df.groupby(["商品ID", "商品名称"]).agg(
            **{SALES: ("实付金额", "sum"), "成本": ("成本", "sum")}
        ).reset_index()
        result[GROSS_PROFIT] = result[SALES] - result["成本"]
        result = result.drop(columns=["成本", SALES]).sort_values(GROSS_PROFIT, ascending=False)
        return result.head(top_n)

    return result.sort_values(result.columns[-1], ascending=False).head(top_n)


def category_summary(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Sales / profit by category."""
    df = _non_refunded(orders).copy()
    if df.empty or products.empty:
        return pd.DataFrame(columns=["类目", SALES, ORDER_CNT, GROSS_PROFIT])
    merged = df.merge(products[["商品ID", "类目", "成本价"]], on="商品ID", how="left")
    merged["类目"] = merged["类目"].fillna("未分类")
    merged["成本"] = merged["数量"] * merged["成本价"].fillna(0)
    result = (
        merged.groupby("类目")
        .agg(**{SALES: ("实付金额", "sum"), ORDER_CNT: ("订单号", "nunique")})
        .reset_index()
    )
    costs = merged.groupby("类目")["成本"].sum()
    result[GROSS_PROFIT] = result[SALES] - costs.values
    return result.sort_values(SALES, ascending=False)


def profit_contribution(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Product profit contribution with cumulative share (Pareto)."""
    df = _non_refunded(orders).copy()
    if df.empty:
        return pd.DataFrame(columns=["商品ID", "商品名称", GROSS_PROFIT, "累计利润占比"])
    cost_map = {}
    if not products.empty and "商品ID" in products.columns:
        cost_map = dict(zip(products["商品ID"], products["成本价"].fillna(0)))
    df["成本"] = df["商品ID"].map(cost_map).fillna(0) * df["数量"]
    result = (
        df.groupby(["商品ID", "商品名称"])
        .agg(**{SALES: ("实付金额", "sum"), "成本": ("成本", "sum")})
        .reset_index()
    )
    result[GROSS_PROFIT] = result[SALES] - result["成本"]
    result = result.sort_values(GROSS_PROFIT, ascending=False).reset_index(drop=True)
    total_profit = result[GROSS_PROFIT].sum()
    result["累计利润占比"] = result[GROSS_PROFIT].cumsum() / total_profit if total_profit else 0.0
    return result


def product_margin_table(products: pd.DataFrame) -> pd.DataFrame:
    """Product table with computed margin."""
    if products.empty:
        return pd.DataFrame()
    df = products.copy()
    df["毛利"] = df["销售价"] - df["成本价"]
    df["毛利率"] = df["毛利"] / df["销售价"].replace(0, pd.NA)
    return df


def inventory_alert(products: pd.DataFrame) -> pd.DataFrame:
    """Products whose stock is at or below the alert threshold."""
    if products.empty:
        return pd.DataFrame()
    df = products.copy()
    df["库存预警阈值"] = df["库存预警阈值"].fillna(0)
    return df[df["库存数量"] <= df["库存预警阈值"]]




# ---------- 客户分析 ----------

def _customer_base(orders: pd.DataFrame) -> pd.DataFrame:
    df = _non_refunded(orders).copy()
    if df.empty or "买家ID" not in df.columns:
        return pd.DataFrame()
    return df[df["买家ID"].astype(str).str.strip().ne("")]


SEGMENT_MAP = {
    (1, 1, 1): "重要价值客户", (1, 1, 0): "重要发展客户",
    (1, 0, 1): "重要保持客户", (1, 0, 0): "一般价值客户",
    (0, 1, 1): "重要挽留客户", (0, 1, 0): "一般挽留客户",
    (0, 0, 1): "一般发展客户", (0, 0, 0): "低价值客户",
}


def customer_rfm(orders: pd.DataFrame) -> pd.DataFrame:
    """RFM customer profile: recency / frequency / monetary with segments."""
    df = _customer_base(orders)
    if df.empty:
        return pd.DataFrame(columns=["买家ID", "最近购买", "购买次数", "总金额", "最近天数", "R", "F", "M", "客户分层"])
    ref_date = df["成交时间"].max()
    grouped = df.groupby("买家ID").agg(
        最近购买=("成交时间", "max"),
        购买次数=("订单号", "nunique"),
        总金额=("实付金额", "sum"),
    ).reset_index()
    grouped["最近天数"] = (ref_date - grouped["最近购买"]).dt.days
    r_med = grouped["最近天数"].median()
    f_med = grouped["购买次数"].median()
    m_med = grouped["总金额"].median()
    grouped["R"] = (grouped["最近天数"] <= r_med).astype(int)
    grouped["F"] = (grouped["购买次数"] > f_med).astype(int)
    grouped["M"] = (grouped["总金额"] > m_med).astype(int)
    grouped["客户分层"] = grouped.apply(
        lambda r: SEGMENT_MAP.get((int(r["R"]), int(r["F"]), int(r["M"])), "低价值客户"), axis=1
    )
    return grouped.sort_values("总金额", ascending=False).reset_index(drop=True)


def repurchase_rate(orders: pd.DataFrame) -> float:
    rfm = customer_rfm(orders)
    if rfm.empty:
        return 0.0
    return float((rfm["购买次数"] >= 2).mean())


def rfm_segments(orders: pd.DataFrame) -> pd.DataFrame:
    rfm = customer_rfm(orders)
    if rfm.empty:
        return pd.DataFrame(columns=["客户分层", "客户数", "总金额"])
    seg = (
        rfm.groupby("客户分层")
        .agg(客户数=("买家ID", "nunique"), 总金额=("总金额", "sum"))
        .reset_index()
        .sort_values("总金额", ascending=False)
    )
    return seg


# ---------- 营销分析 ----------

def marketing_summary(marketing: pd.DataFrame) -> dict:
    if marketing.empty:
        return {"总花费": 0.0, "总成交金额": 0.0, "ROI": 0.0, "记录数": 0}
    spend = float(marketing["花费"].sum())
    revenue = float(marketing["成交金额"].sum())
    return {"总花费": spend, "总成交金额": revenue, "ROI": revenue / spend if spend else 0.0, "记录数": len(marketing)}


def marketing_by_channel(marketing: pd.DataFrame) -> pd.DataFrame:
    df = marketing.copy()
    if df.empty:
        return pd.DataFrame(columns=["渠道", "花费", "成交金额", "ROI", "记录数"])
    result = (
        df.groupby("渠道")
        .agg(花费=("花费", "sum"), 成交金额=("成交金额", "sum"), 记录数=("日期", "count"))
        .reset_index()
    )
    result["ROI"] = result["成交金额"] / result["花费"].replace(0, pd.NA)
    return result.sort_values("花费", ascending=False).reset_index(drop=True)


def marketing_trend(marketing: pd.DataFrame) -> pd.DataFrame:
    df = marketing.copy()
    if df.empty:
        return pd.DataFrame(columns=["日期", "花费", "成交金额", "ROI"])
    df["日期"] = df["日期"].dt.date.astype(str)
    result = df.groupby("日期").agg(花费=("花费", "sum"), 成交金额=("成交金额", "sum")).reset_index()
    result["ROI"] = result["成交金额"] / result["花费"].replace(0, pd.NA)
    return result


# ---------- 价格带与滞销 ----------

def price_band_analysis(orders: pd.DataFrame) -> pd.DataFrame:
    df = _non_refunded(orders).copy()
    if df.empty or "单价" not in df.columns:
        return pd.DataFrame(columns=["价格带", "销售额", "订单量"])
    df["价格带"] = pd.cut(
        df["单价"],
        bins=[0, 50, 100, 200, 500, np.inf],
        labels=["0-50", "50-100", "100-200", "200-500", "500以上"],
        right=False,
    )
    result = (
        df.groupby("价格带", observed=False)
        .agg(**{SALES: ("实付金额", "sum"), ORDER_CNT: ("订单号", "nunique")})
        .reset_index()
    )
    return result


def slow_movers(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Products with stock but almost no sales (suggested clearance)."""
    if products.empty:
        return pd.DataFrame(columns=["商品ID", "商品名称", "类目", "库存数量", "销量", "库存预警阈值"])
    df = products.copy()
    sales = _non_refunded(orders)
    if sales.empty or "商品ID" not in sales.columns:
        sold = pd.Series(0, index=df["商品ID"])
    else:
        sold = sales.groupby("商品ID")["数量"].sum()
    df["销量"] = df["商品ID"].map(sold).fillna(0).astype(int)
    df["库存数量"] = df["库存数量"].fillna(0)
    result = df[(df["库存数量"] > 0) & (df["销量"] < 3)].copy()
    return result.sort_values("库存数量", ascending=False).reset_index(drop=True)
