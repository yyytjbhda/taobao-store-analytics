"""淘宝店铺经营分析工作台 - 应用入口。"""

import streamlit as st

st.set_page_config(page_title="淘宝店铺经营分析工作台", page_icon="🛍️", layout="wide")

from core import ui  # noqa: E402

ui.init_state()

pages = [
    st.Page("views/dashboard.py", title="仪表盘", icon="📊", default=True),
    st.Page("views/orders.py", title="订单管理", icon="📦"),
    st.Page("views/products.py", title="商品管理", icon="🛒"),
    st.Page("views/trade_analysis.py", title="交易分析", icon="📈"),
    st.Page("views/product_analysis.py", title="商品分析", icon="🏆"),
    st.Page("views/marketing_analysis.py", title="营销分析", icon="📣"),
    st.Page("views/customer_analysis.py", title="客户分析", icon="👥"),
    st.Page("views/insights.py", title="经营建议", icon="💡"),
    st.Page("views/sop.py", title="SOP 流程管理", icon="✅"),
    st.Page("views/data_manage.py", title="数据管理", icon="🗂️"),
]

pg = st.navigation(pages)
pg.run()
