"""Business insight engine: turn data into actionable suggestions."""

from __future__ import annotations

import pandas as pd

from core import metrics


def generate_insights(
    orders: pd.DataFrame, products: pd.DataFrame, marketing: pd.DataFrame
) -> list[dict]:
    """Generate business suggestions based on data rules."""
    insights: list[dict] = []
    if orders.empty:
        return insights

    summary = metrics.compute_summary(orders, products)

    # ---- 商品类建议 ----
    slow = metrics.slow_movers(orders, products)
    if not slow.empty:
        total_stock = int(slow["库存数量"].sum())
        insights.append({
            "类别": "商品", "级别": "高", "标题": "存在滞销商品，占用库存",
            "数据": f"共识别 {len(slow)} 个滞销商品（有库存但累计销量不足3件），合计占用库存 {total_stock} 件",
            "建议": "对滞销商品安排清仓活动（如满减、搭配销售、限时折扣），避免资金积压；销量接近0的考虑下架。",
        })

    alerts = metrics.inventory_alert(products)
    if not alerts.empty:
        insights.append({
            "类别": "商品", "级别": "高", "标题": "部分商品库存低于预警线",
            "数据": f"共 {len(alerts)} 个商品库存 ≤ 预警阈值，随时可能缺货断货",
            "建议": "优先为销量靠前的低库存商品补货，避免热销款断货损失销售额。",
        })

    if not products.empty:
        margins = metrics.product_margin_table(products)
        if not margins.empty:
            high = margins.nlargest(3, "毛利")[["商品ID", "商品名称", "毛利", "毛利率"]]
            insights.append({
                "类别": "商品", "级别": "中", "标题": "高毛利商品建议重点推广",
                "数据": "毛利最高的3个商品：" + "、".join(high["商品名称"].astype(str).tolist()),
                "建议": "将资源（流量、广告预算、活动位）向高毛利商品倾斜，提升整体利润。",
            })
            low = margins[margins["毛利率"] < 0.2]
            if not low.empty:
                insights.append({
                    "类别": "商品", "级别": "中", "标题": "存在低毛利商品",
                    "数据": f"共 {len(low)} 个商品毛利率不足20%，建议检查定价与成本",
                    "建议": "评估低毛利商品的引流价值：能带动关联销售的保留，否则考虑提价或替换供应商。",
                })

    # ---- 营销类建议 ----
    if not marketing.empty:
        ms = metrics.marketing_summary(marketing)
        by_channel = metrics.marketing_by_channel(marketing)
        if ms["ROI"] < 1:
            insights.append({
                "类别": "营销", "级别": "高", "标题": "整体推广 ROI 低于 1，推广在亏钱",
                "数据": f"整体 ROI {ms['ROI']:.2f}（花费 {ms['总花费']:.0f}，成交 {ms['总成交金额']:.0f}）",
                "建议": "优先优化 ROI 最低的渠道：调整出价、更换关键词/素材；无效渠道暂停投放。",
            })
        low_roi = by_channel[by_channel["ROI"] < 1]
        if not low_roi.empty:
            names = "、".join(low_roi["渠道"].astype(str).tolist())
            insights.append({
                "类别": "营销", "级别": "中", "标题": "部分渠道 ROI 偏低",
                "数据": f"渠道：{names}，ROI 均低于 1",
                "建议": "ROI < 1 的渠道缩减预算或优化投放策略；测试新素材/新人群包后再评估。",
            })
        best = by_channel[by_channel["ROI"].notna()].sort_values("ROI", ascending=False)
        if not best.empty:
            top_ch = best.iloc[0]
            insights.append({
                "类别": "营销", "级别": "中", "标题": "高 ROI 渠道可加大投入",
                "数据": f"渠道「{top_ch['渠道']}」ROI {top_ch['ROI']:.2f}，效果最好",
                "建议": "在预算可控范围内，将低效渠道的预算向高 ROI 渠道倾斜。",
            })

    # ---- 客户类建议 ----
    if "买家ID" in orders.columns and orders["买家ID"].astype(str).str.strip().ne("").any():
        repurchase = metrics.repurchase_rate(orders)
        if repurchase < 0.1:
            insights.append({
                "类别": "客户", "级别": "中", "标题": "复购率偏低，客户粘性不足",
                "数据": f"复购率 {repurchase:.1%}（复购客户占比不足10%）",
                "建议": "建立会员/复购机制：购买后推送优惠券、会员积分、周期回访，提升二次购买。",
            })
        rfm = metrics.customer_rfm(orders)
        if not rfm.empty:
            churn_risk = rfm[(rfm["购买次数"] >= 2) & (rfm["最近天数"] > 30)]
            if not churn_risk.empty:
                insights.append({
                    "类别": "客户", "级别": "中", "标题": "老客户流失预警",
                    "数据": f"{len(churn_risk)} 位老客户（购买2次以上）超过30天未再购买",
                    "建议": "对这类客户做定向召回：短信/私域触达、专属优惠，防止老客流失。",
                })

    # ---- 经营类建议 ----
    if summary["退款率"] > 0.1:
        insights.append({
            "类别": "经营", "级别": "高", "标题": "退款率偏高",
            "数据": f"退款率 {summary['退款率']:.1%}，高于10%",
            "建议": "排查退款原因：商品质量、描述不符、物流问题；针对高退款商品做改进或下架。",
        })
    aov = summary["客单价"]
    if aov > 0 and aov < 100:
        insights.append({
            "类别": "经营", "级别": "低", "标题": "客单价偏低，利润空间有限",
            "数据": f"客单价 {aov:.0f} 元",
            "建议": "设计搭配套餐、满减门槛，引导用户一次购买多件，提升客单价。",
        })
    trend = metrics.trend_by_period(orders, "D")
    if len(trend) >= 7:
        recent = trend["销售额"].tail(3).mean()
        prior = trend["销售额"].iloc[-6:-3].mean()
        if prior > 0 and recent < prior * 0.7:
            insights.append({
                "类别": "经营", "级别": "中", "标题": "近期销售额明显下滑",
                "数据": f"最近3天日均 {recent:.0f}，前推3天日均 {prior:.0f}，下降 {((prior-recent)/prior*100):.0f}%",
                "建议": "排查下滑原因（流量、竞品、活动节奏），及时调整推广与活动计划。",
            })

    # 排序：高在前
    level_order = {"高": 0, "中": 1, "低": 2}
    insights.sort(key=lambda x: (level_order.get(x["级别"], 9), x["类别"]))
    return insights
