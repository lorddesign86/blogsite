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
    "SIDEBAR_ID": "25px",      # 사이드바 사용자 ID
    "SIDEBAR_LINKS": "30px",   # 사이드바 링크
    "LOGOUT_BTN": "16px",      # 로그아웃 버튼
    "MAIN_TITLE": "32px",      # 메인 제목
    "CHARGE_BTN": "16px",      # 충전하기 버튼
    "REMAIN_TITLE": "22px",    # '실시간 잔여 수량' 제목
    "METRIC_LABEL": "16px",    # 수량 항목 이름
    "METRIC_VALUE": "35px",    # 잔여 수량 숫자
    "REGISTER_TITLE": "22px",  # '작업 일괄 등록' 제목
    "TABLE_HEADER": "20px",    # 입력창 상단 라벨
    "INPUT_TEXT": "18px",      # 입력창 내부 글자
    "SUBMIT_BTN": "40px"       # 작업넣기 버튼
}

ANNOUNCEMENTS = [
    {"text": "📢 파우쓰 서비스 전체보기", "url": "https://kmong.com/@파우쓰"},
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
    .main .block-container {{ padding-top: 2.5rem !important; }}
    .sidebar-id {{ font-size: {FONT_CONFIG['SIDEBAR_ID']} !important; font-weight: bold; margin-bottom: 10px; color: #2ecc71; }}
    [data-testid="stSidebar"] {{ font-size: {FONT_CONFIG['SIDEBAR_LINKS']} !important; }}
    [data-testid="stSidebar"] button p {{ font-size: {FONT_CONFIG['LOGOUT_BTN']} !important; font-weight: bold !important; }}
    .header-wrapper {{ display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }}
    .main-title {{ font-size: {FONT_CONFIG['MAIN_TITLE']} !important; font-weight: bold; margin: 0; }}
    .charge-link {{
        display: inline-block; padding: 6px 14px; background-color: #FF4B4B;
        color: white !important; text-decoration: none; border-radius: 8px;
        font-weight: bold; font-size: {FONT_CONFIG['CHARGE_BTN']} !important;
    }}
    div[data-testid="stHorizontalBlock"] {{ align-items: stretch !important; }}
    [data-testid="stMetric"] {{
        background-color: #1e2129; border-radius: 10px; border: 1px solid #444; 
        padding: 15px 10px !important; min-height: 110px;
        display: flex; flex-direction: column; justify-content: center;
    }}
    [data-testid="stMetricLabel"] div {{ font-size: {FONT_CONFIG['METRIC_LABEL']} !important; }}
    [data-testid="stMetricValue"] div {{ font-size: {FONT_CONFIG['METRIC_VALUE']} !important; font-weight: 800 !important; color: #00ff00 !important; }}
    input {{ font-size: {FONT_CONFIG['INPUT_TEXT']} !important; }}
    .stCaption {{ font-size: {FONT_CONFIG['TABLE_HEADER']} !important; color: #aaa !important; }}
    div.stButton > button:first-child[kind="primary"] {{
        width: 250px !important; height: 75px !important;
        background-color: #FF4B4B !important; border-radius: 15px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-top: 25px;
    }}
    div.stButton > button:first-child[kind="primary"] p {{
        font-size: {FONT_CONFIG['SUBMIT_BTN']} !important; font-weight: bold !important;
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

# --- 🚀 [핵심] 입력 데이터 초기화 함수 ---
def reset_inputs():
    for i in range(10):
        st.session_state[f"kw_{i}"] = ""
        st.session_state[f"url_{i}"] = ""
        st.session_state[f"l_{i}"] = 0
        st.session_state[f"r_{i}"] = 0
        st.session_state[f"s_{i}"] = 0

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 앱 실행 ---
if not st.session_state.logged_in:
    # 로그인 폼
    st.markdown("### 🛡️ 파우쓰 관리자 로그인")
    u_id = st.text_input("ID")
    u_pw = st.text_input("PW", type="password")
    if st.button("LOGIN"):
        try:
            client = get_gspread_client()
            sh = client.open("작업_관리_데이터베이스")
            acc_sheet = sh.worksheet("Accounts")
            all_vals = acc_sheet.get_all_values()
            for row in all_vals[1:]:
                if len(row) >= 2 and str(row[0]) == u_id and str(row[1]) == u_pw:
                    st.session_state.logged_in, st.session_state.current_user = True, u_id
                    st.session_state.nickname = row[5] if len(row) > 5 and row[5].strip() else u_id
                    reset_inputs() # 초기 진입 시 세션 생성
                    st.rerun()
            st.error("정보 불일치")
        except: st.error("연동 실패")
else:
    with st.sidebar:
        st.markdown(f'<div class="sidebar-id">✅ {st.session_state.nickname}님</div>', unsafe_allow_html=True)
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        st.markdown("### 👉 서비스 링크")
        for item in ANNOUNCEMENTS:
            st.markdown(f"**[{item['text']}]({item['url']})**")

    charge_url = "https://kmong.com/inboxes?inbox_group_id=&partner_id="
    st.markdown(f"""
        <div class="header-wrapper">
            <span class="main-title">🚀 {st.session_state.nickname} 님의 작업등록하기</span>
            <a href="{charge_url}" target="_blank" class="charge-link">💰 충전요청하기</a>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        client = get_gspread_client()
        sh = client.open("작업_관리_데이터베이스")
        acc_sheet, hist_sheet = sh.worksheet("Accounts"), sh.worksheet("History")
        all_values = acc_sheet.get_all_values()
        user_row_idx, user_data = next(((i, r) for i, r in enumerate(all_values[1:], 2) if r[0] == st.session_state.current_user), (-1, []))

        if user_row_idx != -1:
            st.markdown(f'<div style="font-size:{FONT_CONFIG["REMAIN_TITLE"]}; font-weight:bold; margin-bottom:15px;">📊 실시간 잔여 수량</div>', unsafe_allow_html=True)
            m_cols = st.columns(4)
            m_cols[0].metric("공감", f"{user_data[2]}")
            m_cols[1].metric("댓글", f"{user_data[3]}")
            m_cols[2].metric("스크랩", f"{user_data[4]}")
            m_cols[3].metric("접속ID", user_data[0])
            st.divider()

            st.markdown(f'<div style="font-size:{FONT_CONFIG["REGISTER_TITLE"]}; font-weight:bold; margin-bottom:15px;">📝 작업 일괄 등록</div>', unsafe_allow_html=True)
            
            # 폼을 사용하여 등록 후 즉시 초기화 구현
            with st.form("work_registration_form", clear_on_submit=True):
                h_col = st.columns([2, 3, 0.8, 0.8, 0.8])
                for idx, label in enumerate(["키워드", "URL (필수)", "공감", "댓글", "스크랩"]): h_col[idx].caption(label)

                rows_inputs = []
                for i in range(10):
                    r_col = st.columns([2, 3, 0.8, 0.8, 0.8])
                    kw = r_col[0].text_input(f"키워드_{i}", label_visibility="collapsed", placeholder="(키워드)")
                    url = r_col[1].text_input(f"URL_{i}", label_visibility="collapsed", placeholder="(링크 입력)")
                    l = r_col[2].number_input(f"공_{i}", min_value=0, step=1, label_visibility="collapsed")
                    r = r_col[3].number_input(f"댓_{idx}_{i}", min_value=0, step=1, label_visibility="collapsed")
                    s = r_col[4].number_input(f"스_{idx}_{i}", min_value=0, step=1, label_visibility="collapsed")
                    rows_inputs.append({"kw": kw, "url": url, "l": l, "r": r, "s": s})

                submitted = st.form_submit_button("🔥 작업넣기", type="primary")

                if submitted:
                    rows_to_submit = [d for d in rows_inputs if d['url'].strip() and (d['l']>0 or d['r']>0 or d['s']>0)]
                    link_errors = [f"{i+1}행" for i, d in enumerate(rows_inputs) if d['url'].strip() and not is_valid_naver_link(d['url'])]

                    if link_errors: st.error(f"⚠️ {', '.join(link_errors)} 링크 오류")
                    elif not rows_to_submit: st.warning("⚠️ 작업하실 내용을 입력해주세요.")
                    else:
                        rem_l, rem_r, rem_s = int(user_data[2]), int(user_data[3]), int(user_data[4])
                        total_l, total_r, total_s = sum(d['l'] for d in rows_to_submit), sum(d['r'] for d in rows_to_submit), sum(d['s'] for d in rows_to_submit)

                        if rem_l >= total_l and rem_r >= total_r and rem_s >= total_s:
                            acc_sheet.update_cell(user_row_idx, 3, rem_l - total_l)
                            acc_sheet.update_cell(user_row_idx, 4, rem_r - total_r)
                            acc_sheet.update_cell(user_row_idx, 5, rem_s - total_s)
                            
                            for d in rows_to_submit:
                                hist_sheet.append_row([
                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                                    d['kw'], d['url'], d['l'], d['r'], d['s'], 
                                    st.session_state.current_user,
                                    st.session_state.nickname
                                ])
                            st.success("🎊 작업 등록 완료! 순차적으로 시작됩니다.")
                            time.sleep(1)
                            st.rerun() # 폼 외부 데이터 동기화를 위해 재실행
                        else: st.error("❌ 잔여 수량 부족")
    except Exception as e: st.error(f"데이터 연동 실패: {e}")
