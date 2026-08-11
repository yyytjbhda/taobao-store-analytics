"""Build demo orders/products/marketing from the real Taobao UserBehavior dataset.

Note: the public Taobao dataset has no money/refund fields; amounts and
refund flags are simulated with realistic distributions. Behavior, users,
items, categories and timestamps are real.
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/demo/raw/UserBehavior.csv")
OUT_ORDERS = Path("data/demo/orders.csv")
OUT_PRODUCTS = Path("data/demo/products.csv")
OUT_MARKETING = Path("data/demo/marketing.csv")

CATEGORIES = {
    0: "服饰鞋包", 1: "数码家电", 2: "美妆个护", 3: "家居日用",
    4: "食品生鲜", 5: "运动户外", 6: "母婴玩具", 7: "图书文创",
}
PRICE_RANGES = {
    "服饰鞋包": (29, 199), "数码家电": (69, 899), "美妆个护": (19, 299),
    "家居日用": (15, 159), "食品生鲜": (8, 99), "运动户外": (39, 399),
    "母婴玩具": (19, 199), "图书文创": (12, 69),
}
CHANNELS = ["直通车", "淘宝客", "引力魔方", "万相台", "站外推广"]
CHANNEL_SHARE = {"直通车": 0.32, "淘宝客": 0.22, "引力魔方": 0.16, "万相台": 0.12, "站外推广": 0.05}

rng = np.random.default_rng(20260811)

df = pd.read_csv(RAW, header=None, names=["user_id", "item_id", "category_id", "behavior", "ts"])
buy = df[df["behavior"] == "buy"].copy()

buy["成交时间"] = pd.to_datetime(buy["ts"], unit="s")
buy["类目"] = buy["category_id"].mod(8).map(CATEGORIES)
buy = buy.sort_values(["user_id", "成交时间"]).reset_index(drop=True)

buy["_grp"] = buy.groupby(["user_id", "成交时间"]).cumcount().eq(0).cumsum()
buy["订单号"] = "TB" + buy["_grp"].astype(str).str.zfill(7)

lo = buy["类目"].map(lambda c: PRICE_RANGES[c][0])
hi = buy["类目"].map(lambda c: PRICE_RANGES[c][1])
buy["售价"] = rng.uniform(lo, hi).round(2)
buy["商品名称"] = buy["类目"] + "-商品" + buy["item_id"].astype(str).str[-4:]

order_ids = buy["订单号"].unique()
refund_ids = set(rng.choice(order_ids, size=int(len(order_ids) * 0.05), replace=False))
buy["退款状态"] = np.where(buy["订单号"].isin(refund_ids), "已退款", "未退款")
buy["订单状态"] = np.where(buy["订单号"].isin(refund_ids), "已退款", "已完成")

orders = pd.DataFrame({
    "订单号": buy["订单号"],
    "成交时间": buy["成交时间"].dt.strftime("%Y-%m-%d %H:%M:%S"),
    "商品ID": buy["item_id"].astype(str),
    "商品名称": buy["商品名称"],
    "数量": 1,
    "单价": buy["售价"],
    "实付金额": buy["售价"],
    "运费": 0,
    "优惠金额": 0,
    "买家ID": buy["user_id"].astype(str),
    "退款状态": buy["退款状态"],
    "订单状态": buy["订单状态"],
    "备注": "",
})
orders.to_csv(OUT_ORDERS, index=False, encoding="utf-8-sig")

items = buy.drop_duplicates("item_id").copy()
plo = items["类目"].map(lambda c: PRICE_RANGES[c][0])
phi = items["类目"].map(lambda c: PRICE_RANGES[c][1])
items["销售价"] = rng.uniform(plo, phi).round(2)
items["成本价"] = (items["销售价"] * rng.uniform(0.45, 0.65, len(items))).round(2)
items["库存预警阈值"] = rng.integers(15, 40, len(items))
items["库存数量"] = rng.integers(0, 500, len(items))
low_stock = rng.random(len(items)) < 0.08
items.loc[low_stock, "库存数量"] = rng.integers(0, items.loc[low_stock, "库存预警阈值"].values + 1)

products = pd.DataFrame({
    "商品ID": items["item_id"].astype(str),
    "商品名称": items["类目"] + "-商品" + items["item_id"].astype(str).str[-4:],
    "类目": items["类目"],
    "SKU": "SKU-" + items["item_id"].astype(str).str[-6:],
    "成本价": items["成本价"],
    "销售价": items["销售价"],
    "库存数量": items["库存数量"],
    "库存预警阈值": items["库存预警阈值"],
    "上架状态": "上架",
})
products.to_csv(OUT_PRODUCTS, index=False, encoding="utf-8-sig")

# 营销演示数据：按每日实际销售额，按渠道占比生成花费与归因成交
orders_parsed = orders.copy()
orders_parsed["成交时间"] = pd.to_datetime(orders_parsed["成交时间"])
daily_rev = orders_parsed[orders_parsed["退款状态"] == "未退款"].groupby(orders_parsed["成交时间"].dt.date)["实付金额"].sum()
marketing_rows = []
for d, rev in daily_rev.items():
    for ch, share in CHANNEL_SHARE.items():
        base = float(rev) * share
        spend = round(base * rng.uniform(0.18, 0.42), 2)
        revenue = round(base * rng.uniform(1.6, 3.8), 2)
        marketing_rows.append({"日期": str(d), "渠道": ch, "花费": spend, "成交金额": revenue, "备注": "演示数据"})
marketing = pd.DataFrame(marketing_rows, columns=["日期", "渠道", "花费", "成交金额", "备注"])
marketing.to_csv(OUT_MARKETING, index=False, encoding="utf-8-sig")

print("orders:", len(orders), "| products:", len(products), "| marketing:", len(marketing))
print("DONE")
