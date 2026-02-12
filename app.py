import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time
import re

# ==========================================
# 📐 [글자 크기 및 설정 옵션] - 여기서 자유롭게 수정하세요!
# ==========================================
FONT_CONFIG = {
    "TITLE_SIZE": "28px",      # 메인 타이틀 (바둥이 작업등록)
    "METRIC_LABEL": "14px",    # 잔여 수량 항목 이름 (공감, 댓글 등)
    "METRIC_VALUE": "22px",    # 잔여 수량 숫자 크기
    "INPUT_LABEL": "13px",     # 입력창 상단 캡션 (키워드, URL 등)
    "INPUT_TEXT": "15px",      # 입력창 내부 글자 크기
    "SUBMIT_BTN_TEXT": "22px", # 작업넣기 버튼 글자 크기
    "SUBMIT_BTN_WIDTH": "240px",# 작업넣기 버튼 가로 길이
    "SUBMIT_BTN_HEIGHT": "65px" # 작업넣기 버튼 세로 높이
}

# --- 1. 기본 설정 및 문구 ---
UI_TEXT = {
    "SUB_TITLE_REMAIN": "📊 실시간 잔여 수량",
    "SUB_TITLE_INPUT": "📝 작업 일괄 등록",
    "SUBMIT_BUTTON": "🔥 작업넣기",
    "LOGIN_TITLE": "### 🛡️ 파우쓰 관리자",
    "SUCCESS_MSG": "🎊 모든 작업이 정상 등록되었습니다."
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

# --- 🎨 디자인 CSS (f-string 중괄호 오류 수정 완료) ---
st.markdown(f"""
    <style>
    .main .block-container {{ padding-top: 2.5rem !important; }}
    
    /* 타이틀 영역 가로 정렬 */
    .header-wrapper {{ display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }}
    .main-title {{ font-size: {FONT_CONFIG['TITLE_SIZE']} !important; margin: 0; font-weight: bold; }}
    
    .charge-link {{
        display: inline-block; padding: 6px 14px; background-color: #FF4B4B;
        color: white !important; text-decoration: none; border-radius: 8px;
        font-weight: bold; font-size: 14px;
    }}
    .charge-link:hover {{ background-color: #e63939; text-decoration: none; }}

    /* 잔여 수량(Metric) 디자인 */
    [data-testid="stMetric"] {{ background-color: #1e2129; padding: 10px !important; border-radius: 10px; border: 1px solid #444; text-align: center; }}
    [data-testid="stMetricLabel"] > div {{ font-size: {FONT_CONFIG['METRIC_LABEL']} !important; }}
    [data-testid="stMetricValue"] > div {{ font-size: {FONT_CONFIG['METRIC_VALUE']} !important; font-weight: 700 !important; color: #00ff00 !important; }}

    /* 입력창 헤더 및 텍스트 */
    .stCaption {{ font-size: {FONT_CONFIG['INPUT_LABEL']} !important; color: #aaa; }}
    .stTextInput input, .stNumberInput input {{ font-size: {FONT_CONFIG['INPUT_TEXT']} !important; }}

    /* 🔥 대형 작업넣기 버튼 */
    div.stButton > button:first-child {{
        width: {FONT_CONFIG['SUBMIT_BTN_WIDTH']} !important;
        height: {FONT_CONFIG['SUBMIT_BTN_HEIGHT']} !important;
        font-size: {FONT_CONFIG['SUBMIT_BTN_TEXT']} !important;
        background-color: #FF4B4B !important;
        border-radius: 15px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        margin-top: 20px;
    }}

    /* 모바일 대응 */
    @media (max-width: 768px) {{
        div.stButton > button:first-child {{
            position: fixed; bottom: 10px; left: 5%; right: 5%; width: 90% !important; z-index: 999;
            height: 4rem !important;
        }}
        .header-wrapper {{ flex-direction: column; align-items: flex-start; gap: 10px; }}
        .stTextInput, .stNumberInput {{ margin-bottom: -15px !important; }}
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
    _, login_col, _ = st.columns([1, 2, 1])
    with login_col:
        st.markdown(UI_TEXT["LOGIN_TITLE"])
        u_id = st.text_input("ID", key="l_id")
        u_pw = st.text_input("PW", type="password", key="l_pw")
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
                        st.rerun()
                st.error("정보 불일치")
            except Exception: st.error("연결 오류")
else:
    # 사이드바 레이아웃
    with st.sidebar:
        st.success(f"✅ **{st.session_state.nickname}**님")
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        st.markdown("### 📢 서비스 링크")
        for item in ANNOUNCEMENTS:
            st.markdown(f"**[{item['text']}]({item['url']})**")

    # 헤더 (타이틀 + 충전하기 버튼)
    charge_url = "https://kmong.com/inboxes?inbox_group_id=&partner_id="
    st.markdown(f"""
        <div class="header-wrapper">
            <span class="main-title">🚀 {st.session_state.nickname} 작업등록</span>
            <a href="{charge_url}" target="_blank" class="charge-link">💰 충전하기</a>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        client = get_gspread_client()
        sh = client.open("작업_관리_데이터베이스")
        acc_sheet, hist_sheet = sh.worksheet("Accounts"), sh.worksheet("History")
        all_values = acc_sheet.get_all_values()
        user_row_idx, user_data = next(((i, r) for i, r in enumerate(all_values[1:], 2) if r[0] == st.session_state.current_user), (-1, []))

        if user_row_idx != -1:
            st.write(UI_TEXT["SUB_TITLE_REMAIN"])
            m1, m2, m3, m4 = st.columns([1, 1, 1, 1.2])
            m1.metric("공감", f"{user_data[2]}")
            m2.metric("댓글", f"{user_data[3]}")
            m3.metric("스크랩", f"{user_data[4]}")
            m4.metric("접속ID", user_data[0])
            st.divider()
            
            st.subheader(UI_TEXT["SUB_TITLE_INPUT"])
            h_col = st.columns([2, 3, 0.8, 0.8, 0.8])
            for i, txt in enumerate(["키워드", "URL (필수)", "공", "댓", "스"]): h_col[i].caption(txt)

            rows_data, link_errors = [], []
            for i in range(10):
                r_col = st.columns([2, 3, 0.8, 0.8, 0.8])
                kw = r_col[0].text_input(f"k_{i}", label_visibility="collapsed", key=f"kw_{i}", placeholder="(키워드)")
                url = r_col[1].text_input(f"u_{i}", label_visibility="collapsed", key=f"url_{i}", placeholder="(URL 입력)")
                l = r_col[2].number_input(f"l_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"l_{i}")
                r = r_col[3].number_input(f"r_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"r_{i}")
                s = r_col[4].number_input(f"s_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"s_{i}")
                
                if url.strip():
                    if not is_valid_naver_link(url): link_errors.append(f"{i+1}행")
                    elif l > 0 or r > 0 or s > 0:
                        rows_data.append({"kw": kw if kw else "", "link": url.strip(), "l": l, "r": r, "s": s})

            if st.button(UI_TEXT["SUBMIT_BUTTON"], type="primary", key="submit_btn"):
                if link_errors:
                    st.error(f"⚠️ {', '.join(link_errors)} 링크 오류: 네이버 블로그 형식이 아닙니다.")
                elif not rows_data:
                    st.warning("⚠️ 등록할 링크와 작업 수량을 입력하세요.")
                else:
                    with st.spinner("📦 처리 중..."):
                        t_l, t_r, t_s = sum(d['l'] for d in rows_data), sum(d['r'] for d in rows_data), sum(d['s'] for d in rows_data)
                        if int(user_data[2]) >= t_l and int(user_data[3]) >= t_r and int(user_data[4]) >= t_s:
                            acc_sheet.update_cell(user_row_idx, 3, int(user_data[2]) - t_l)
                            acc_sheet.update_cell(user_row_idx, 4, int(user_data[3]) - t_r)
                            acc_sheet.update_cell(user_row_idx, 5, int(user_data[4]) - t_s)
                            for d in rows_data:
                                hist_sheet.append_row([datetime.now().strftime('%m-%d %H:%M'), d['kw'], d['link'], d['l'], d['r'], d['s'], st.session_state.current_user])
                            st.success(UI_TEXT["SUCCESS_MSG"])
                            time.sleep(1)
                            st.rerun()
                        else: st.error("❌ 잔여 수량이 부족합니다.")

    except Exception: st.error("연동 실패")
