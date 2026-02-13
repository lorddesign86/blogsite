import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time
import re
import requests

# ==========================================
# 📐 [FONT_CONFIG] - 사용자님 최종 설정 (절대 고정)
# ==========================================
FONT_CONFIG = {
    "SIDEBAR_ID": "25px",      # 사이드바 사용자 ID 크기 [cite: 2025-08-09]
    "SIDEBAR_LINKS": "20px",   # 사이드바 서비스 링크 글자 크기 [cite: 2025-08-09]
    "LOGOUT_TEXT": "15px",     # 로그아웃 텍스트 링크 크기
    "MAIN_TITLE": "32px",      # 메인 제목 크기
    "CHARGE_BTN": "20px",      # 충전하기 버튼 글자 크기
    "REMAIN_TITLE": "30px",    # '실시간 잔여 수량' 제목 크기
    "METRIC_LABEL": "16px",    # 수량 항목 이름 크기
    "METRIC_VALUE": "35px",    # 잔여 수량 숫자 크기
    "REGISTER_TITLE": "22px",  # '작업 일괄 등록' 제목 크기
    "TABLE_HEADER": "40px",    # 🔥 입력창 상단 라벨 크기 (40px 고정)
    "TABLE_INPUT": "16px",     # 입력창 내부 글자 크기
    "SUBMIT_BTN": "22px"       # 🔥 50px 높이에 맞춰 시인성을 높인 버튼 폰트 크기
}

ANNOUNCEMENTS = [
    {"text": "👉 파우쓰 서비스 전체보기", "url": "https://kmong.com/@파우쓰"},
    {"text": "📢 스댓공 월 자동서비스", "url": "https://kmong.com/gig/645544"},
    {"text": "📢 스댓공 개별서비스", "url": "https://kmong.com/gig/445340"},
    {"text": "📢 방문자 서비스 보러가", "url": "https://caring-kayak-cd7.notion.site/27707671d021808a9567edb8ad065b28?source=copy_link"},
    {"text": "📢 이웃 서비스 100~700명", "url": "https://kmong.com/gig/668226"},
    {"text": "📢 최적화 블로그리스트 추출프로그램", "url": "https://kmong.com/gig/725815"},
]

st.set_page_config(page_title="파우쓰", layout="wide")

# --- 🎨 디자인 & 정렬 CSS ---
st.markdown(f"""
    <style>
    .main .block-container {{ padding-top: 2.5rem !important; padding-bottom: 120px !important; }}
    .sidebar-id {{ font-size: {FONT_CONFIG['SIDEBAR_ID']} !important; font-weight: bold !important; color: #2ecc71 !important; display: inline-block !important; }}
    .logout-link {{ font-size: {FONT_CONFIG['LOGOUT_TEXT']} !important; color: #888 !important; text-decoration: underline !important; margin-left: 10px !important; cursor: pointer !important; }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ font-size: {FONT_CONFIG['SIDEBAR_LINKS']} !important; }}
    .main-title {{ font-size: {FONT_CONFIG['MAIN_TITLE']} !important; font-weight: bold !important; }}
    
    /* ✅ 상단 라벨 40px 절대 고정 */
    [data-testid="stVerticalBlock"] .stCaption div p {{ 
        font-size: {FONT_CONFIG['TABLE_HEADER']} !important; 
        color: #ddd !important; font-weight: 900 !important; 
    }}

    /* ✅ 하단 고정 작업넣기 버튼 (50px 높이 고정) */
    div.stButton > button {{
        position: fixed !important; bottom: 20px !important; left: 50% !important; transform: translateX(-50%) !important;
        width: 85% !important; max-width: 600px !important; height: 50px !important;
        background-color: #FF4B4B !important; color: white !important; border-radius: 12px !important;
        z-index: 999999 !important; border: 2px solid white !important; display: flex !important; align-items: center !important; justify-content: center !important;
    }}
    div.stButton > button p {{ font-size: {FONT_CONFIG['SUBMIT_BTN']} !important; font-weight: 900 !important; margin: 0 !important; line-height: 1 !important; }}
    
    input {{ font-size: {FONT_CONFIG['TABLE_INPUT']} !important; }}
    [data-testid="stMetricValue"] div {{ font-size: {FONT_CONFIG['METRIC_VALUE']} !important; font-weight: 800 !important; color: #00ff00 !important; }}
    small, .stDeployButton {{ display: none !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- ⚙️ 초기화 로직 함수 ---
def reset_form():
    """등록 성공 시 세션 상태에 저장된 입력값을 비움"""
    for i in range(10):
        st.session_state[f"k_{i}"] = ""
        st.session_state[f"u_{i}"] = ""
        st.session_state[f"l_{i}"] = 0
        st.session_state[f"r_{i}"] = 0
        st.session_state[f"s_{i}"] = 0

def send_telegram_msg(message):
    try:
        token = "8568445865:AAHkHpC164IDFKTyy-G76QdCZlWnpFdr6ZU"
        chat_id = "496784884"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": message})
    except: pass

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    return gspread.authorize(Credentials.from_service_account_info(creds_dict, scopes=scopes))

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if st.query_params.get("action") == "logout":
    st.session_state.logged_in = False
    st.query_params.clear()
    st.rerun()

if not st.session_state.logged_in:
    # (로그인 로직 생략 - 기존과 동일)
    pass
else:
    with st.sidebar:
        logout_html = f'<div style="display: flex; align-items: center;"><span class="sidebar-id">✅ {st.session_state.nickname}님</span><a href="/?action=logout" target="_self" class="logout-link">LOGOUT</a></div>'
        st.markdown(logout_html, unsafe_allow_html=True)
        st.divider()
        for item in ANNOUNCEMENTS: st.markdown(f"**[{item['text']}]({item['url']})**")

    # --- 메인 영역 ---
    # (잔여 수량 지표 생략 - 기존과 동일)
    
    try:
        client = get_gspread_client()
        sh = client.open("작업_관리_데이터베이스")
        acc_sheet, hist_sheet = sh.worksheet("Accounts"), sh.worksheet("History")
        
        # --- 3. 작업 일괄 등록 표 (초기화 대응 key 적용) ---
        st.markdown(f'<div style="font-size:{FONT_CONFIG["REGISTER_TITLE"]}; font-weight:bold; margin-bottom:10px;">📝 작업 일괄 등록</div>', unsafe_allow_html=True)
        h_col = st.columns([2, 3, 1.2, 1.2, 1.2])
        labels = ["키워드(선택)", "URL (필수)", "공감", "댓글", "스크랩"]
        for idx, label in enumerate(labels): h_col[idx].caption(label)

        rows_inputs = []
        for i in range(10):
            r_col = st.columns([2, 3, 1.2, 1.2, 1.2])
            # 위젯에 key를 부여하여 등록 후 세션 상태에서 직접 초기화 가능하게 함
            kw = r_col[0].text_input(f"kw_{i}", key=f"k_{i}", label_visibility="collapsed")
            u_raw = r_col[1].text_input(f"url_{i}", key=f"u_{i}", label_visibility="collapsed", placeholder="(링크 입력)")
            l = r_col[2].number_input(f"like_{i}", key=f"l_{i}", min_value=0, step=1, label_visibility="collapsed")
            r = r_col[3].number_input(f"reply_{i}", key=f"r_{i}", min_value=0, step=1, label_visibility="collapsed")
            s = r_col[4].number_input(f"scrap_{i}", key=f"s_{i}", min_value=0, step=1, label_visibility="collapsed")
            rows_inputs.append({"kw": kw, "url": u_raw.replace(" ", "").strip(), "l": l, "r": r, "s": s})

        if st.button("🔥 작업넣기", type="primary"):
            valid_rows = [d for d in rows_inputs if d['url'] and (d['l']>0 or d['r']>0 or d['s']>0)]
            if valid_rows:
                # (중략: 구글 시트 저장 및 텔레그램 발송 로직)
                
                # ✅ [해결] 등록 성공 후 입력 행만 비우기
                reset_form()
                st.success("🎊 모든 등록 완료!")
                time.sleep(1.2)
                st.rerun()
    except Exception as e: st.error(f"오류: {e}")
