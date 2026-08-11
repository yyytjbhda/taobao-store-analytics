"""开场页：全屏电影感欢迎页，点击进入工作台。"""

import streamlit as st

from core import style

VIDEO_URL = (
    "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/"
    "hf_20260619_191346_9d19d66e-86a4-47f7-8dc6-712c1788c3b2.mp4"
)


def _stagger_chars(text: str, base_delay: float = 0.0) -> str:
    """Split text into per-character animated spans (CSS stagger)."""
    spans = []
    for i, ch in enumerate(text):
        delay = base_delay + i * 0.07
        spans.append(f'<span class="char-anim" style="animation-delay:{delay:.2f}s">{ch}</span>')
    return "".join(spans)


def render() -> None:
    st.markdown(f"<style>{style.WELCOME_CSS}</style>", unsafe_allow_html=True)

    html = f"""
    <div class="hero-root">
      <div class="hero-video">
        <video autoplay muted loop playsinline src="{VIDEO_URL}"></video>
      </div>
      <div class="hero-glow"></div>
      <div class="hero-inner">
        <div class="hero-eyebrow">TAOBAO STORE ANALYTICS &middot; WORKBENCH</div>
        <h1 class="hero-title">
          <span class="line">{_stagger_chars("WITNESS THE")}</span>
          <span class="line">{_stagger_chars("HIDDEN REALM", base_delay=0.42)}</span>
        </h1>
        <div class="hero-subtitle">淘宝店铺经营分析工作台</div>
        <p class="hero-desc">以真实交易数据，解读经营的每一面<br>让每一次决策都有据可依。</p>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    st.link_button("进入工作台 · BEGIN", "/dashboard", type="primary")


render()