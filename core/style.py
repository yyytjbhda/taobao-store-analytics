"""Global UI style: theme CSS, plotly defaults, sidebar brand, welcome page."""

from __future__ import annotations

import plotly.io as pio
import streamlit as st

BRAND_HTML = """
<div class="app-brand">
  <div class="app-brand-title">🛍️ 淘宝经营分析工作台</div>
  <div class="app-brand-sub">Taobao Store Analytics Workbench</div>
</div>
"""

GLOBAL_CSS = """
/* ===== 字体引入（网络不可用时自动回退系统字体） ===== */
@import url("https://db.onlinewebfonts.com/c/2bf40ab72ea4897a3fd9b6e48b233a19?family=Garamond");
@import url("https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500&display=swap");
@import url("https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&display=swap");

/* ===== 基础：深色电影感 ===== */
html, body, [class*="css"], [class*="st-"] {
  font-family: "Geist", "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
}
.font-garamond { font-family: "Garamond", "Times New Roman", serif; }

body {
  background-color: #0B0D10;
  background-image: url("/app/static/bg.jpg");
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  background-repeat: no-repeat;
}
.stApp { background: rgba(10, 12, 16, 0.84); }

/* 隐藏默认页眉 / 页脚 / 工具条 */
#MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {
  visibility: hidden; height: 0;
}

/* ===== 主内容标题 ===== */
.block-container { padding-top: 1.2rem; padding-bottom: 3rem; }
.block-container h1 {
  font-size: 24px; font-weight: 800; color: #F3F4F6; letter-spacing: .3px;
}
.block-container h2 {
  font-size: 18px; font-weight: 700; color: #E5E7EB;
  margin-top: 4px; margin-bottom: 2px;
}
.block-container h3 { font-size: 15.5px; font-weight: 700; color: #E5E7EB; }

/* 说明文字 */
[data-testid="stCaptionContainer"] p { color: #8B93A1; font-size: 12.5px; }

/* ===== 侧边栏：深色毛玻璃 ===== */
[data-testid="stSidebar"] {
  background: rgba(10, 12, 16, 0.82);
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  border-right: 1px solid rgba(255,255,255,.08);
}
[data-testid="stSidebarContent"] { padding: .6rem .9rem 2rem; }
/* 锁定侧边栏：隐藏收起按钮，导航不会消失 */
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label { color: #D7DCE4; }

/* 数据源切换：深色胶囊按钮 */
[data-testid="stSidebar"] [role="radiogroup"] label {
  display: flex; align-items: center;
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 10px;
  padding: 8px 12px; margin-bottom: 7px;
  transition: all .15s ease; cursor: pointer;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
  background: rgba(255,255,255,.10);
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
  background: #E84343; border-color: #E84343;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * {
  color: #FFFFFF !important;
}

/* 品牌头 */
.app-brand {
  padding: 4px 6px 14px;
  border-bottom: 1px solid rgba(255,255,255,.08);
  margin-bottom: 10px;
}
.app-brand-title { color: #FFFFFF; font-size: 16px; font-weight: 800; line-height: 1.5; }
.app-brand-sub { color: #9CA3AF; font-size: 11px; margin-top: 3px; letter-spacing: .5px; }

/* ===== 指标卡：深色玻璃 ===== */
[data-testid="stMetric"] {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 14px;
  padding: 14px 18px 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 6px 18px rgba(0,0,0,0.22),
              inset 0 1px 0 rgba(255,255,255,0.06);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
[data-testid="stMetricLabel"] {
  color: #9CA3AF !important; font-size: 13px !important; font-weight: 500 !important;
}
[data-testid="stMetricValue"] {
  color: #F9FAFB !important; font-size: 26px !important; font-weight: 800 !important;
  letter-spacing: .3px;
}

/* ===== 卡片容器 ===== */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.09) !important;
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 6px 18px rgba(0,0,0,0.22),
              inset 0 1px 0 rgba(255,255,255,0.06);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 4px 14px 10px;
}

/* 图表容器 */
[data-testid="stPlotlyChart"] {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 6px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.25);
}

/* ===== 按钮 ===== */
.stButton > button, .stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button {
  border-radius: 10px; font-weight: 600; transition: all .15s ease;
}
button[kind="primary"] { background: #E84343; border: 1px solid #E84343; color: #FFFFFF; }
button[kind="primary"]:hover { background: #D13939; border-color: #D13939; color: #FFFFFF; }
button[kind="secondary"] {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.14);
  color: #E5E7EB;
}
button[kind="secondary"]:hover {
  border-color: #E84343; color: #FFFFFF; background: rgba(232,67,67,0.14);
}

/* ===== 表格 ===== */
[data-testid="stDataFrame"] {
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 12px; overflow: hidden;
  box-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

/* ===== 提示框 ===== */
[data-testid="stAlert"] { border-radius: 12px; }

/* ===== Tabs ===== */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid rgba(255,255,255,0.10); }
.stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; font-weight: 600; padding: 8px 16px; color: #9CA3AF; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: #E84343; }
.stTabs [data-baseweb="tab-highlight"] { background-color: #E84343; }

/* ===== Expander ===== */
[data-testid="stExpander"] {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 12px !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.25);
}
[data-testid="stExpander"] summary { border-radius: 12px; }

/* ===== 输入控件圆角 ===== */
[data-baseweb="select"] > div, [data-baseweb="input"] > div,
[data-baseweb="base-input"] > div, [data-baseweb="textarea"] > div {
  border-radius: 10px !important;
}

/* ===== 主区筛选 radio：分段按钮 ===== */
.block-container [role="radiogroup"] label {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.14);
  border-radius: 999px;
  padding: 5px 16px; margin-right: 8px; font-weight: 500; color: #D1D5DB;
  transition: all .15s ease; cursor: pointer;
}
.block-container [role="radiogroup"] label:hover { border-color: #E84343; color: #FFFFFF; }
.block-container [role="radiogroup"] label:has(input:checked) {
  background: #E84343; border-color: #E84343;
}
.block-container [role="radiogroup"] label:has(input:checked) * {
  color: #FFFFFF !important;
}

/* 分割线 */
hr { border-color: rgba(255,255,255,0.08) !important; }
"""


def apply_plotly_defaults() -> None:
    """Set a unified dark look for all plotly charts."""
    pio.templates.default = "plotly_dark"
    try:
        tpl = pio.templates["plotly_dark"]
        tpl.layout.paper_bgcolor = "rgba(0,0,0,0)"
        tpl.layout.plot_bgcolor = "rgba(0,0,0,0)"
        tpl.layout.font.family = "Microsoft YaHei, Geist, sans-serif"
        tpl.layout.font.color = "#D1D5DB"
        tpl.layout.colorway = ["#E84343", "#F59E0B", "#10B981", "#3B82F6", "#8B5CF6", "#EC4899"]
        tpl.layout.xaxis.gridcolor = "rgba(255,255,255,0.08)"
        tpl.layout.yaxis.gridcolor = "rgba(255,255,255,0.08)"
    except Exception:  # noqa: BLE001
        pass


def inject_global_css() -> None:
    st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)


SIDEBAR_LOCK_JS = """<script>
(function () {
  if (window.__tbSidebarUnlocked) return;
  window.__tbSidebarUnlocked = true;
  function unlock() {
    var btn = document.querySelector('[data-testid="stExpandSidebarButton"]');
    if (btn) btn.click();
  }
  window.setTimeout(unlock, 200);
  window.setInterval(unlock, 800);
})();
</script>"""


def inject_sidebar_lock() -> None:
    """Auto-expand the sidebar and keep it expanded (nav never disappears)."""
    st.html(SIDEBAR_LOCK_JS, unsafe_allow_javascript=True)


def sidebar_brand() -> None:
    st.sidebar.markdown(BRAND_HTML, unsafe_allow_html=True)


WELCOME_CSS = """
/* ===== 开场页：全屏隐藏默认布局 ===== */
/* sidebar kept visible on welcome page */
[data-testid="stHeader"] { display: none !important; }
[data-testid="stMainBlockContainer"], .block-container {
  padding: 0 !important; max-width: 100% !important;
}
[data-testid="stMain"] { height: 100vh; overflow: hidden; }

/* ===== 电影感 hero 背景 ===== */
.hero-root {
  position: fixed; inset: 0; z-index: 5;
  background: #010101; overflow: hidden;
  display: flex; align-items: center; justify-content: center;
}
.hero-video { position: absolute; inset: 0; z-index: 0; }
.hero-video video {
  width: 100%; height: 100%; object-fit: cover; object-position: center;
  opacity: 0.82; filter: brightness(1.02);
}
.hero-glow {
  position: absolute; inset: 0; z-index: 1;
  background:
    radial-gradient(ellipse at 50% 38%, rgba(232, 67, 67, 0.13), transparent 58%),
    radial-gradient(ellipse at 80% 80%, rgba(59, 130, 246, 0.07), transparent 50%),
    linear-gradient(180deg, rgba(1,1,1,0.55) 0%, rgba(1,1,1,0.24) 42%, rgba(1,1,1,0.78) 100%);
}
.hero-inner { position: relative; z-index: 2; text-align: center; padding: 0 20px; margin-top: -6vh; }

.hero-eyebrow {
  color: rgba(255,255,255,0.62);
  font-family: "Geist", sans-serif;
  font-size: 12px; letter-spacing: 0.35em; text-transform: uppercase;
  margin-bottom: 30px;
  animation: fadeUp 0.8s ease both;
}
.hero-title {
  font-family: "Garamond", "Times New Roman", serif;
  font-weight: 400; color: #FFFFFF; line-height: 1.08; letter-spacing: -0.01em;
  font-size: clamp(44px, 9vw, 122px);
  margin-bottom: 30px;
}
.hero-title .line { display: block; }

.char-anim {
  display: inline-block; opacity: 0;
  animation: charIn 0.7s ease forwards;
}
@keyframes charIn {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}

.hero-subtitle {
  font-family: "Noto Serif SC", "Garamond", serif;
  color: rgba(255,255,255,0.88);
  font-size: clamp(17px, 2.4vw, 22px);
  letter-spacing: 0.28em;
  animation: fadeUp 0.8s ease 1.6s both;
}
.hero-desc {
  color: rgba(255,255,255,0.72);
  font-weight: 300; line-height: 1.9;
  font-size: 15px; max-width: 440px; margin: 18px auto 0;
  animation: fadeUp 0.8s ease 1.85s both;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(22px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ===== 玻璃拟态 CTA（居中：定位在外层，动画含 translateX(-50%)） ===== */
[data-testid="stLinkButton"] {
  position: fixed; bottom: 9vh; left: 50%; transform: translateX(-50%);
  z-index: 30;
}
a[data-testid="stBaseLinkButton-primary"],
a[data-testid="stBaseLinkButton-secondary"] {
  display: inline-block;
  background: rgba(255,255,255,0.01);
  backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
  border: none; border-radius: 999px;
  padding: 15px 44px;
  color: rgba(255,255,255,0.92) !important;
  font-weight: 400; font-size: 14px; letter-spacing: 0.2em; text-transform: uppercase;
  box-shadow: inset 0 1px 1px rgba(255,255,255,0.1);
  position: relative; overflow: hidden;
  text-decoration: none !important;
  transition: background 0.3s ease, box-shadow 0.3s ease;
  animation: fadeUpBtn 0.8s ease 2.1s both;
}
a[data-testid="stBaseLinkButton-primary"]::before,
a[data-testid="stBaseLinkButton-secondary"]::before {
  content: ""; position: absolute; inset: 0; border-radius: inherit; padding: 1.4px;
  background: linear-gradient(180deg,
    rgba(255,255,255,0.45) 0%, rgba(255,255,255,0.15) 20%,
    rgba(255,255,255,0) 40%, rgba(255,255,255,0) 60%,
    rgba(255,255,255,0.15) 80%, rgba(255,255,255,0.45) 100%);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}
a[data-testid="stBaseLinkButton-primary"]:hover,
a[data-testid="stBaseLinkButton-secondary"]:hover {
  background: rgba(255,255,255,0.05);
  box-shadow: inset 0 1px 2px rgba(255,255,255,0.18);
  color: #FFFFFF !important;
}
a[data-testid="stBaseLinkButton-primary"]:active,
a[data-testid="stBaseLinkButton-secondary"]:active { transform: scale(0.98); }

@keyframes fadeUpBtn {
  from { opacity: 0; transform: translateX(-50%) translateY(22px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}
"""