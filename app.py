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
    "MAIN_TITLE": "32px",      # 메인 제목 크기
    "CHARGE_BTN": "16px",      # 충전하기 버튼 글자 크기
    "REMAIN_TITLE": "22px",    # '실시간 잔여 수량' 제목 크기
    "METRIC_LABEL": "16px",    # 수량 항목 이름 (공감, 댓글 등) 크기
    "METRIC_VALUE": "32px",    # 잔여 수량 숫자 크기 (강력 조절)
    "REGISTER_TITLE": "22px",  # '작업 일괄 등록' 제목 크기
    "TABLE_HEADER": "15px",    # 입력창 상단 라벨 크기
    "INPUT_TEXT": "16px",      # 입력창 내부 글자 크기
    "SUBMIT_BTN": "26px"       # 작업넣기 버튼 글자 크기
}

# --- 기본 설정 ---
st.set_page_config(page_title="파우쓰", layout="wide")

# --- 🎨 정렬 및 폰트 통합 제어 CSS ---
st.markdown(f"""
    <style>
    /* 전체 레이아웃 보정 */
    .main .block-container {{ padding-top: 2.5rem !important; }}
    
    /* 1. 타이틀 & 충전버튼 정렬 */
    .header-wrapper {{ display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }}
    .main-title {{ font-size: {FONT_CONFIG['MAIN_TITLE']} !important; font-weight: bold; margin: 0; }}
    .charge-link {{
        display: inline-block; padding: 6px 14px; background-color: #FF4B4B;
        color: white !important; text-decoration: none; border-radius: 8px;
        font-weight: bold; font-size: {FONT_CONFIG['CHARGE_BTN']} !important;
    }}

    /* 2. [핵심] 잔여 수량 박스 정렬 및 높이 통일 */
    div[data-testid="stHorizontalBlock"] {{
        align-items: stretch !important; /* 모든 박스 높이를 동일하게 */
    }}
    [data-testid="stMetric"] {{
        background-color: #1e2129; 
        border-radius: 10px; 
        border: 1px solid #444; 
        padding: 15px 10px !important;
        min-height: 120px; /* 박스 최소 높이 고정 */
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    [data-testid="stMetricLabel"] div {{ 
        font-size: {FONT_CONFIG['METRIC_LABEL']} !important; 
        margin-bottom: 8px !important;
    }}
    [data-testid="stMetricValue"] div {{ 
        font-size: {FONT_CONFIG['METRIC_VALUE']} !important; 
        font-weight: 800 !important; 
        color: #00ff00 !important; 
    }}

    /* 3. 작업넣기 버튼 대형화 */
    div.stButton > button:first-child[kind="primary"] {{
        width: 260px !important;
        height: 75px !important;
        background-color: #FF4B4B !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        margin-top: 25px;
    }}
    div.stButton > button:first-child[kind="primary"] p {{
        font-size: {FONT_CONFIG['SUBMIT_BTN']} !important;
        font-weight: bold !important;
    }}

    /* 4. 사이드바 및 입력창 */
    .sidebar-id {{ font-size: {FONT_CONFIG['SIDEBAR_ID']} !important; font-weight: bold; margin-bottom: 10px; }}
    input {{ font-size: {FONT_CONFIG['INPUT_TEXT']} !important; }}
    .stCaption {{ font-size: {FONT_CONFIG['TABLE_HEADER']} !important; color: #aaa !important; }}

    /* 모바일 대응 가로 정렬 */
    @media (max-width: 768px) {{
        [data-testid="stMetric"] {{ min-height: 80px; padding: 5px !important; }}
        div.stButton > button:first-child[kind="primary"] {{
            position: fixed; bottom: 10px; left: 5%; right: 5%; width: 90% !important; z-index: 999;
            height: 4.2rem !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

# 🔗 네이버 블로그 링크 검증 함수
def is_valid_naver_link(url):
    pattern = r'^https?://(m\.)?blog\.naver\.com/[\w-]+/\d+$'
    return re.match(pattern, url.strip()) is not None

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 메인 실행 로직 ---
if not st.session_state.logged_in:
    # 로그인 화면 (생략)
    st.title("🛡️ 파우쓰 관리자")
    if st.button("임시 로그인 (테스트용)"):
        st.session_state.logged_in = True
        st.session_state.current_user = "admin"
        st.session_state.nickname = "바둥이"
        st.rerun()
else:
    with st.sidebar:
        st.markdown(f'<div class="sidebar-id">✅ {st.session_state.nickname}님</div>', unsafe_allow_html=True)
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        st.markdown("### 📢 서비스 링크")
        for item in ANNOUNCEMENTS:
            st.markdown(f"**[{item['text']}]({item['url']})**")

    # 헤더
    charge_url = "https://kmong.com/inboxes"
    st.markdown(f"""
        <div class="header-wrapper">
            <span class="main-title">🚀 {st.session_state.nickname} 작업등록</span>
            <a href="{charge_url}" target="_blank" class="charge-link">💰 충전하기</a>
        </div>
    """, unsafe_allow_html=True)
    
    # 잔여 수량 표시 영역 (정렬 보정)
    st.markdown(f'<div style="font-size:{FONT_CONFIG["REMAIN_TITLE"]}; font-weight:bold; margin-bottom:15px;">📊 실시간 잔여 수량</div>', unsafe_allow_html=True)
    
    # 4개 컬럼을 균등하게 배치
    m_cols = st.columns(4)
    # 실제 데이터 연동 시 이 부분을 user_data[2], [3] 등으로 교체하세요.
    m_cols[0].metric("공감", "18개")
    m_cols[1].metric("댓글", "0개")
    m_cols[2].metric("스크랩", "18개")
    m_cols[3].metric("접속ID", "admin77")
    
    st.divider()
    
    # 작업 입력 영역 (캡션 정렬)
    st.markdown(f'<div style="font-size:{FONT_CONFIG["REGISTER_TITLE"]}; font-weight:bold; margin-bottom:15px;">📝 작업 일괄 등록</div>', unsafe_allow_html=True)
    h_cols = st.columns([2, 3, 0.8, 0.8, 0.8])
    labels = ["키워드", "URL (필수)", "공", "댓", "스"]
    for idx, label in enumerate(labels):
        h_cols[idx].caption(label)
        
    # 입력창 10행 생성 로직 (생략 - 기존과 동일하게 유지)
    st.button("🔥 작업넣기", type="primary")
