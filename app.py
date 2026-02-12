import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time
import re

# ==========================================
# 📐 [FONT_CONFIG] - 글자 크기를 여기서 수정하세요!
# ==========================================
FONT_CONFIG = {
    "SIDEBAR_ID": "25px",      # 사이드바 사용자 ID 크기
    "SIDEBAR_LINKS": "15px",   # 사이드바 서비스 링크 글자 크기
    "LOGOUT_BTN": "16px",      # 로그아웃 버튼 글자 크기
    "MAIN_TITLE": "32px",      # 메인 제목 (작업등록) 크기
    "CHARGE_BTN": "16px",      # 충전하기 버튼 글자 크기
    "REMAIN_TITLE": "22px",    # '실시간 잔여 수량' 제목 크기
    "METRIC_LABEL": "16px",    # 수량 항목 이름 (공감, 댓글 등) 크기
    "METRIC_VALUE": "35px",    # 잔여 수량 숫자 크기 (강력 조절 가능)
    "REGISTER_TITLE": "22px",  # '작업 일괄 등록' 제목 크기
    "TABLE_HEADER": "15px",    # 입력창 상단 라벨 (키워드, URL) 크기
    "TABLE_INPUT": "16px",     # 입력창 내부 텍스트 크기
    "SUBMIT_BTN": "26px"       # 작업넣기 버튼 글자 크기
}

# --- 📢 서비스 링크 (ANNOUNCEMENTS 변수 정의 필수) ---
ANNOUNCEMENTS = [
    {"text": "👉 파우쓰 서비스 전체보기", "url": "https://kmong.com/@파우쓰"},
    {"text": "📢 스댓공 월 자동서비스", "url": "https://kmong.com/gig/645544"},
    {"text": "📢 스댓공 개별서비스", "url": "https://kmong.com/gig/445340"},
    {"text": "📢 방문자 서비스 보러가", "url": "https://caring-kayak-cd7.notion.site/27707671d021808a9567edb8ad065b28?source=copy_link"},
    {"text": "📢 이웃 서비스 100~700명", "url": "https://kmong.com/gig/668226"},
    {"text": "📢 최적화 블로그리스트 추출프로그램", "url": "https://kmong.com/gig/725815"},
]

st.set_page_config(page_title="파우쓰", layout="wide")

# --- 🎨 디자인 CSS (에러 방지를 위해 중괄호 {{ }} 사용) ---
st.markdown(f"""
    <style>
    .main .block-container {{ padding-top: 2.5rem !important; }}
    
    /* 1. 사이드바 영역 */
    .sidebar-id {{ font-size: {FONT_CONFIG['SIDEBAR_ID']} !important; font-weight: bold; margin-bottom: 10px; color: #2ecc71; }}
    [data-testid="stSidebar"] {{ font-size: {FONT_CONFIG['SIDEBAR_LINKS']} !important; }}
    [data-testid="stSidebar"] button p {{ font-size: {FONT_CONFIG['LOGOUT_BTN']} !important; font-weight: bold !important; }}

    /* 2. 메인 타이틀 & 충전버튼 정렬 */
    .header-wrapper {{ display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }}
    .main-title {{ font-size: {FONT_CONFIG['MAIN_TITLE']} !important; font-weight: bold; margin: 0; }}
    .charge-link {{
        display: inline-block; padding: 6px 14px; background-color: #FF4B4B;
        color: white !important; text-decoration: none; border-radius: 8px;
        font-weight: bold; font-size: {FONT_CONFIG['CHARGE_BTN']} !important;
    }}

    /* 3. [정렬 보정] 잔여 수량 섹션 */
    .section-title {{ font-size: {FONT_CONFIG['REMAIN_TITLE']} !important; font-weight: bold; margin-bottom: 15px; }}
    div[data-testid="stHorizontalBlock"] {{ align-items: stretch !important; }}
    [data-testid="stMetric"] {{
        background-color: #1e2129; border-radius: 10px; border: 1px solid #444; 
        padding: 15px 10px !important; min-height: 110px;
        display: flex; flex-direction: column; justify-content: center;
    }}
    [data-testid="stMetricLabel"] div {{ font-size: {FONT_CONFIG['METRIC_LABEL']} !important; margin-bottom: 5px !important; }}
    [data-testid="stMetricValue"] div {{ 
        font-size: {FONT_CONFIG['METRIC_VALUE']} !important; 
        font-weight: 800 !important; color: #00ff00 !important; 
    }}

    /* 4. 작업 등록 섹션 */
    .input-title {{ font-size: {FONT_CONFIG['REGISTER_TITLE']} !important; font-weight: bold; margin-top: 25px; }}
    .stCaption {{ font-size: {FONT_CONFIG['TABLE_HEADER']} !important; color: #aaa !important; }}
    input {{ font-size: {FONT_CONFIG['TABLE_INPUT']} !important; }}

    /* 5. 하단 작업넣기 버튼 */
    div.stButton > button:first-child[kind="primary"] {{
        width: 250px !important; height: 75px !important;
        background-color: #FF4B4B !important; border-radius: 15px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-top: 20px;
    }}
    div.stButton > button:first-child[kind="primary"] p {{
        font-size: {FONT_CONFIG['SUBMIT_BTN']} !important; font-weight: bold !important;
    }}

    @media (max-width: 768px) {{
        div.stButton > button:first-child[kind="primary"] {{
            position: fixed; bottom: 10px; left: 5%; right: 5%; width: 90% !important; z-index: 999;
            height: 4.2rem !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

# 🔗 네이버 블로그 링크 검증
def is_valid_naver_link(url):
    pattern = r'^https?://(m\.)?blog\.naver\.com/[\w-]+/\d+$'
    return re.match(pattern, url.strip()) is not None

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 앱 실행 로직 ---
if not st.session_state.logged_in:
    # 로그인 폼 생략 (기존 유지)
    st.markdown("### 🛡️ 파우쓰 관리자 로그인")
    if st.button("테스트용 로그인 (실제 시트 연동 필요)"):
        st.session_state.logged_in = True
        st.session_state.nickname = "바둥이"
        st.session_state.current_user = "admin77"
        st.rerun()
else:
    # 사이드바
    with st.sidebar:
        st.markdown(f'<div class="sidebar-id">✅ {st.session_state.nickname}님</div>', unsafe_allow_html=True)
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        st.markdown("### 📢 서비스 링크")
        for item in ANNOUNCEMENTS:
            st.markdown(f"**[{item['text']}]({item['url']})**")

    # 메인 헤더
    charge_url = "https://kmong.com/inboxes?inbox_group_id=&partner_id="
    st.markdown(f"""
        <div class="header-wrapper">
            <span class="main-title">🚀 {st.session_state.nickname} 작업등록</span>
            <a href="{charge_url}" target="_blank" class="charge-link">💰 충전하기</a>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        # 데이터 연동 시 이 부분을 시트 읽어오는 코드로 채우세요
        # user_data = [ ... ] 
        
        st.markdown(f'<div class="section-title">📊 실시간 잔여 수량</div>', unsafe_allow_html=True)
        m_cols = st.columns(4)
        m_cols[0].metric("공감", "18개")
        m_cols[1].metric("댓글", "0개")
        m_cols[2].metric("스크랩", "18개")
        m_cols[3].metric("ID", "admin77")
        st.divider()

        st.markdown(f'<div class="input-title">📝 작업 일괄 등록</div>', unsafe_allow_html=True)
        h_col = st.columns([2, 3, 0.8, 0.8, 0.8])
        for i, txt in enumerate(["키워드", "URL (필수)", "공", "댓", "스"]): h_col[i].caption(txt)

        # 10행 입력칸 생성 (기존 로직 사용)
        # ...

        st.button("🔥 작업넣기", type="primary", key="submit_btn")

    except Exception:
        st.error("데이터 연동 실패")
