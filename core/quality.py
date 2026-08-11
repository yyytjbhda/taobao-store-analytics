"""Data quality checks for imported orders."""

from __future__ import annotations

import pandas as pd


def check_order_quality(orders: pd.DataFrame) -> pd.DataFrame:
    """Run quality checks on orders, return an issues table."""
    issues: list[dict] = []
    if orders.empty:
        return pd.DataFrame(columns=["行号", "订单号", "问题类型", "说明", "级别"])

    df = orders.reset_index(drop=True)

    def add(issue_type: str, note: str, level: str, row_idx: int) -> None:
        issues.append({
            "行号": int(row_idx) + 2,
            "订单号": str(df.loc[row_idx, "订单号"]),
            "问题类型": issue_type,
            "说明": note,
            "级别": level,
        })

    # 必填字段缺失
    for col in ["订单号", "成交时间", "商品ID", "商品名称"]:
        mask = df[col].isna() | df[col].astype(str).str.strip().eq("")
        for i in df.index[mask]:
            add("字段缺失", f"缺少「{col}」", "高", i)

    # 成交时间异常
    if "成交时间" in df.columns:
        dt = pd.to_datetime(df["成交时间"], errors="coerce")
        future_mask = dt > (pd.Timestamp.now() + pd.Timedelta(days=1))
        for i in df.index[future_mask]:
            add("时间异常", "成交时间在未来", "高", i)
        too_old = dt < pd.Timestamp("2000-01-01")
        for i in df.index[too_old]:
            add("时间异常", "成交时间早于2000年", "中", i)

    # 数量异常
    qty = pd.to_numeric(df["数量"], errors="coerce")
    for i in df.index[qty.isna() | (qty <= 0)]:
        add("数量异常", f"数量无效：{df.loc[i, '数量']}", "高", i)

    # 非退款订单金额异常
    not_refunded = df["退款状态"] != "已退款"
    paid = pd.to_numeric(df["实付金额"], errors="coerce")
    for i in df.index[not_refunded & (paid.isna() | (paid <= 0))]:
        add("金额异常", f"非退款订单实付金额异常：{df.loc[i, '实付金额']}", "高", i)

    price = pd.to_numeric(df["单价"], errors="coerce")
    for i in df.index[not_refunded & price.isna() & df["单价"].astype(str).str.strip().ne("")]:
        add("金额异常", "单价不是有效数字", "高", i)

    # 实付金额与 单价×数量-优惠 偏差过大（容忍1元，运费单独列）
    expected = price * qty - pd.to_numeric(df["优惠金额"], errors="coerce").fillna(0)
    diff = (paid - expected).abs()
    for i in df.index[not_refunded & price.notna() & qty.notna() & diff.gt(1.0)]:
        add("金额异常", f"实付与(单价×数量-优惠)偏差{diff[i]:.2f}元", "低", i)

    # 重复行（同一订单号+商品ID）
    dup_mask = df.duplicated(subset=["订单号", "商品ID"], keep=False)
    seen = set()
    for i in df.index[dup_mask]:
        key = (str(df.loc[i, "订单号"]), str(df.loc[i, "商品ID"]))
        if key in seen:
            add("重复记录", "同一订单号+商品ID重复", "中", i)
        seen.add(key)

    return pd.DataFrame(issues, columns=["行号", "订单号", "问题类型", "说明", "级别"])


def quality_summary(issues: pd.DataFrame) -> dict:
    if issues.empty:
        return {"总数": 0, "高": 0, "中": 0, "低": 0}
    return {
        "总数": len(issues),
        "高": int((issues["级别"] == "高").sum()),
        "中": int((issues["级别"] == "中").sum()),
        "低": int((issues["级别"] == "低").sum()),
    }
