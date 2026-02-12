import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time
import re

# ==========================================
# 📐 [글자 크기 통합 설정] - 여기서 숫자만 수정하세요!
# ==========================================
FONT_CONFIG = {
    "MAIN_TITLE": "30px",      # 메인 제목 (바둥이 작업등록)
    "CHARGE_BTN": "16px",      # 충전하기 버튼 (빨간 상자 1)
    "METRIC_VALUE": "26px",    # 수량 숫자 크기 (빨간 상자 2)
    "SUBMIT_BTN": "24px",      # 작업넣기 버튼 (빨간 상자 3)
    "LOGOUT_BTN": "16px",      # 로그아웃 버튼 (빨간 상자 4)
    "METRIC_LABEL": "15px",    # 수량 라벨 크기
    "INPUT_TEXT": "15px"       # 입력창 내부 글자 크기
}

# --- 기본 설정 ---
UI_TEXT = {
    "SUBMIT_BUTTON": "🔥 작업넣기",
    "SUCCESS_MSG": "🎊 모든 작업이 정상 등록되었습니다."
}

ANNOUNCEMENTS = [
    {"text": "👉 파우쓰 서비스 전체보기", "url": "https://kmong.com/@파우쓰"},
    {"text": "📢 스댓공 월 자동서비스", "url": "https://kmong.com/gig/645544"},
]

st.set_page_config(page_title="파우쓰", layout="wide")

# --- 🎨 디자인 CSS (빨간 상자 내부 텍스트 강제 조절) ---
# f-string 오류 방지를 위해 중괄호를 {{ }}로 이중 처리했습니다.
st.markdown(f"""
    <style>
    .main .block-container {{ padding-top: 2.5rem !important; }}
    
    /* 1. 타이틀 및 충전하기 버튼 */
    .header-wrapper {{ display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }}
    .main-title {{ font-size: {FONT_CONFIG['MAIN_TITLE']} !important; font-weight: bold; }}
    .charge-link {{
        display: inline-block; padding: 6px 16px; background-color: #FF4B4B;
        color: white !important; text-decoration: none; border-radius: 8px;
        font-weight: bold; font-size: {FONT_CONFIG['CHARGE_BTN']} !important;
    }}

    /* 2. 잔여 수량 (Metric) 숫자 크기 강제 적용 */
    [data-testid="stMetricValue"] div {{ 
        font-size: {FONT_CONFIG['METRIC_VALUE']} !important; 
        font-weight: 700 !important; 
        color: #00ff00 !important; 
    }}
    [data-testid="stMetricLabel"] div {{ font-size: {FONT_CONFIG['METRIC_LABEL']} !important; }}

    /* 3. 작업넣기 버튼 크기 및 텍스트 강제 적용 */
    div.stButton > button:first-child {{
        width: 260px !important;
        height: 70px !important;
        background-color: #FF4B4B !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }}
    div.stButton > button:first-child p {{
        font-size: {FONT_CONFIG['SUBMIT_BTN']} !important;
        font-weight: bold !important;
    }}

    /* 4. 로그아웃 버튼 텍스트 크기 */
    [data-testid="stSidebar"] button p {{
        font-size: {FONT_CONFIG['LOGOUT_BTN']} !important;
        font-weight: bold !important;
    }}

    /* 입력창 내부 텍스트 */
    input {{ font-size: {FONT_CONFIG['INPUT_TEXT']} !important; }}

    @media (max-width: 768px) {{
        div.stButton > button:first-child {{
            position: fixed; bottom: 10px; left: 5%; right: 5%; width: 90% !important; z-index: 999;
            height: 4rem !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

# 🔗 네이버 블로그 링크 검증 함수
def is_valid_naver_link(url):
    pattern = r'^https?://(m\.)?blog\.naver\.com/[\w-]+/\d+$'
    return re.match(pattern, url.strip()) is not None

# --- 이하 생략된 기존 구글 시트 및 로그인 로직 ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🛡️ 파우쓰 관리자")
    # 로그인 폼... (생략)
    if st.button("LOGIN"):
        st.session_state.logged_in = True
        st.session_state.nickname = "바둥이"
        st.session_state.current_user = "admin"
        st.rerun()
else:
    # 사이드바 (로그아웃 버튼)
    with st.sidebar:
        st.markdown(f"### ✅ {st.session_state.nickname}님")
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        for item in ANNOUNCEMENTS:
            st.markdown(f"**[{item['text']}]({item['url']})**")

    # 메인 화면
    charge_url = "https://kmong.com/inboxes"
    st.markdown(f"""
        <div class="header-wrapper">
            <span class="main-title">🚀 {st.session_state.nickname} 작업등록</span>
            <a href="{charge_url}" target="_blank" class="charge-link">💰 충전하기</a>
        </div>
    """, unsafe_allow_html=True)

    # 잔여 수량 표시
    st.write("📊 실시간 잔여 수량")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("공감", "18개")
    m2.metric("댓글", "0개")
    m3.metric("스크랩", "18개")
    m4.metric("접속ID", "admin77")
    
    st.divider()
    
    # 작업넣기 버튼
    if st.button(UI_TEXT["SUBMIT_BUTTON"], type="primary", key="submit_btn"):
        st.success(UI_TEXT["SUCCESS_MSG"])
