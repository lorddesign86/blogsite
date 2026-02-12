import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time
import re

# ==========================================
# 📐 [FONT_CONFIG] - 글자 크기 설정
# ==========================================
FONT_CONFIG = {
    "SIDEBAR_ID": "25px",      
    "SIDEBAR_LINKS": "15px",   
    "LOGOUT_BTN": "16px",      
    "MAIN_TITLE": "32px",      
    "CHARGE_BTN": "16px",      
    "REMAIN_TITLE": "22px",    
    "METRIC_LABEL": "16px",    
    "METRIC_VALUE": "35px",    
    "REGISTER_TITLE": "22px",  
    "TABLE_HEADER": "15px",    
    "TABLE_INPUT": "16px",     
    "SUBMIT_BTN": "26px"       
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

# --- 🎨 디자인 & 정렬 CSS (안내 문구 제거 및 버튼 스타일 포함) ---
st.markdown(f"""
    <style>
    .main .block-container {{ padding-top: 2.5rem !important; }}
    
    /* 🚀 "Press Enter to submit form" 안내 문구 숨기기 */
    [data-testid="stFormSubmitButton"] + div {{ display: none !important; }}
    small {{ display: none !important; }}

    /* 수량 조절 버튼 스타일 최적화 */
    div[data-testid="stVerticalBlock"] div[role="group"] {{
        gap: 0.5rem !important;
    }}
    
    .sidebar-id {{ font-size: {FONT_CONFIG['SIDEBAR_ID']} !important; font-weight: bold; margin-bottom: 10px; color: #2ecc71; }}
    [data-testid="stSidebar"] {{ font-size: {FONT_CONFIG['SIDEBAR_LINKS']} !important; }}
    [data-testid="stSidebar"] button p {{ font-size: {FONT_CONFIG['LOGOUT_BTN']} !important; font-weight: bold !important; }}
    
    .header-wrapper {{ display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }}
    .main-title {{ font-size: {FONT_CONFIG['MAIN_TITLE']} !important; font-weight: bold; margin: 0; }}
    
    input {{ font-size: {FONT_CONFIG['TABLE_INPUT']} !important; }}
    .stCaption {{ font-size: {FONT_CONFIG['TABLE_HEADER']} !important; color: #aaa !important; }}

    /* 작업넣기 버튼 대형화 */
    div.stButton > button:first-child[kind="primary"] {{
        width: 250px !important; height: 75px !important;
        background-color: #FF4B4B !important; border-radius: 15px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-top: 25px;
    }}
    </style>
    """, unsafe_allow_html=True)

def is_valid_naver_link(url):
    pattern = r'^https?://(m\.)?blog\.naver\.com/[\w-]+/\d+$'
    return re.match(pattern, url.strip()) is not None

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 1. 로그인 화면 ---
if not st.session_state.logged_in:
    _, center_col, _ = st.columns([1, 1.3, 1])
    with center_col:
        with st.form("login_form"):
            st.markdown("### 🛡️ 파우쓰 관리자 로그인")
            u_id = st.text_input("ID", placeholder="아이디", autocomplete="username")
            u_pw = st.text_input("PW", type="password", placeholder="비밀번호", autocomplete="current-password")
            if st.form_submit_button("LOGIN"):
                try:
                    client = get_gspread_client()
                    sh = client.open("작업_관리_데이터베이스")
                    acc_sheet = sh.worksheet("Accounts")
                    all_vals = acc_sheet.get_all_values()
                    for row in all_vals[1:]:
                        if len(row) >= 2 and str(row[0]) == u_id and str(row[1]) == u_pw:
                            st.session_state.logged_in = True
                            st.session_state.current_user = u_id
                            st.session_state.nickname = row[5] if len(row) > 5 and row[5].strip() else u_id
                            st.rerun()
                    st.error("정보 불일치")
                except Exception as e: st.error(f"연동 실패: {str(e)}")
else:
    # --- 2. 메인 앱 레이아웃 ---
    with st.sidebar:
        st.markdown(f'<div class="sidebar-id">✅ {st.session_state.nickname}님</div>', unsafe_allow_html=True)
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        for item in ANNOUNCEMENTS:
            st.markdown(f"**[{item['text']}]({item['url']})**")

    # 헤더 및 잔여 수량 표시
    st.markdown(f'<div class="main-title">🚀 {st.session_state.nickname} 작업등록</div>', unsafe_allow_html=True)
    
    try:
        client = get_gspread_client()
        sh = client.open("작업_관리_데이터베이스")
        acc_sheet, hist_sheet = sh.worksheet("Accounts"), sh.worksheet("History")
        all_values = acc_sheet.get_all_values()
        user_row_idx, user_data = next(((i, r) for i, r in enumerate(all_values[1:], 2) if r[0] == st.session_state.current_user), (-1, []))

        if user_row_idx != -1:
            st.divider()
            st.markdown(f"📝 작업 일괄 등록")
            
            with st.form("work_registration_form", clear_on_submit=True):
                h_col = st.columns([2, 3, 1.2, 1.2, 1.2]) # 버튼 공간 확보를 위해 너비 조정
                labels = ["키워드", "URL (필수)", "공감", "댓글", "스크랩"]
                for idx, label in enumerate(labels): h_col[idx].caption(label)

                rows_inputs = []
                for i in range(10):
                    r_col = st.columns([2, 3, 1.2, 1.2, 1.2])
                    kw = r_col[0].text_input(f"k_{i}", label_visibility="collapsed", placeholder="(키워드)")
                    url = r_col[1].text_input(f"u_{i}", label_visibility="collapsed", placeholder="(링크 입력)")
                    
                    # 🚀 버튼 기능이 포함된 number_input (step=1 설정 시 +/- 버튼 생성)
                    l = r_col[2].number_input(f"공_{i}", min_value=0, step=1, label_visibility="collapsed")
                    r = r_col[3].number_input(f"댓_{i}", min_value=0, step=1, label_visibility="collapsed")
                    s = r_col[4].number_input(f"스_{i}", min_value=0, step=1, label_visibility="collapsed")
                    
                    rows_inputs.append({"kw": kw, "url": url, "l": l, "r": r, "s": s})

                submitted = st.form_submit_button("🔥 작업넣기", type="primary")

                if submitted:
                    # 데이터 필터링 및 구글 시트 H열 기록 로직
                    rows_to_submit = [d for d in rows_inputs if d['url'].strip() and (d['l']>0 or d['r']>0 or d['s']>0)]
                    if rows_to_submit:
                        for d in rows_to_submit:
                            hist_sheet.append_row([
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                                d['kw'], d['url'], d['l'], d['r'], d['s'], 
                                st.session_state.current_user,
                                st.session_state.nickname # H열 기록
                            ])
                        st.success("🎊 등록 완료! 입력창이 비워졌습니다.")
                        time.sleep(1)
                        st.rerun()
    except Exception as e: st.error(f"동기화 실패: {str(e)}")
