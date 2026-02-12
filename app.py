import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. 기본 설정 및 문구 ---
UI_TEXT = {
    "SUB_TITLE_REMAIN": "📊 잔여 수량",
    "SUB_TITLE_INPUT": "📝 작업 등록",
    "SUBMIT_BUTTON": "🔥 작업넣기",
    "ERROR_LACK": "❌ 수량 부족!",
    "SUCCESS_MSG": "🎊 등록 완료!",
    "LOGIN_TITLE": "### 🛡️ 파우쓰",
    "PROCESS_MSG": "📦 처리 중..."
}

ANNOUNCEMENTS = [
    {"text": "👉 자동관리/방문자 바로가기", "url": "https://kmong.com/@파우쓰"},
    {"text": "👉 이웃추가 서비스 이용", "url": "https://kmong.com/@파우쓰"},
    {"text": "📢 신규 서비스 출시 공지", "url": "https://kmong.com/@파우쓰"},
]

st.set_page_config(page_title="파우쓰 모바일", layout="wide")

# --- 🎨 모바일 하단 고정 버튼 및 레이아웃 CSS ---
st.markdown("""
    <style>
    /* 전체 여백 조절 */
    .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important; }
    
    /* 숫자 카드 스타일 */
    [data-testid="stMetric"] { background-color: #1e2129; padding: 5px !important; border-radius: 8px; text-align: center; }
    [data-testid="stMetricValue"] { font-size: 1.1rem !important; font-weight: 700 !important; }

    /* 모바일 하단 고정 버튼 스타일 */
    @media (max-width: 768px) {
        div.stButton > button:first-child {
            position: fixed;
            bottom: 20px;
            left: 5%;
            right: 5%;
            width: 90%;
            z-index: 999;
            height: 3.5rem;
            background-color: #FF4B4B !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            border-radius: 15px;
            font-size: 18px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'nickname' not in st.session_state: st.session_state.nickname = ""

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

col_side, col_main = st.columns([1, 4])

with col_side:
    if not st.session_state.logged_in:
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
            except Exception: st.error("로그인 실패")
    else:
        c_user, c_logout = st.columns([2, 1])
        c_user.write(f"✅ **{st.session_state.nickname}**")
        if c_logout.button("OUT", key="out_btn"):
            st.session_state.logged_in = False
            st.rerun()

if st.session_state.logged_in:
    with col_main:
        st.markdown(f"#### 🚀 {st.session_state.nickname} 작업등록")
        try:
            client = get_gspread_client()
            sh = client.open("작업_관리_데이터베이스")
            acc_sheet, hist_sheet = sh.worksheet("Accounts"), sh.worksheet("History")
            all_values = acc_sheet.get_all_values()
            user_row_idx, user_data = next(((i, r) for i, r in enumerate(all_values[1:], 2) if r[0] == st.session_state.current_user), (-1, []))

            if user_row_idx != -1:
                # 상단 수량 3열 배치
                m1, m2, m3 = st.columns(3)
                m1.metric("공감", user_data[2])
                m2.metric("댓글", user_data[3])
                m3.metric("스크랩", user_data[4])
                st.divider()
                
                # 입력 영역
                rows_data = []
                h_col = st.columns([2, 2.5, 0.8, 0.8, 0.8])
                for i, txt in enumerate(["키워드", "URL", "공", "댓", "스"]): h_col[i].caption(txt)

                for i in range(10):
                    r_col = st.columns([2, 2.5, 0.8, 0.8, 0.8])
                    kw = r_col[0].text_input(f"k_{i}", label_visibility="collapsed", key=f"kw_{i}")
                    url = r_col[1].text_input(f"u_{i}", label_visibility="collapsed", key=f"url_{i}")
                    l = r_col[2].number_input(f"l_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"l_{i}")
                    r = r_col[3].number_input(f"r_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"r_{i}")
                    s = r_col[4].number_input(f"s_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"s_{i}")
                    if kw and url: rows_data.append({"kw": kw, "link": url, "l": l, "r": r, "s": s})

                # 이 버튼이 모바일에서는 하단에 고정됩니다
                if st.button(UI_TEXT["SUBMIT_BUTTON"], type="primary", key="sticky_submit"):
                    if not rows_data: st.warning("데이터를 입력하세요.")
                    else:
                        with st.spinner(UI_TEXT["PROCESS_MSG"]):
                            acc_sheet.update_cell(user_row_idx, 3, int(user_data[2]) - sum(d['l'] for d in rows_data))
                            acc_sheet.update_cell(user_row_idx, 4, int(user_data[3]) - sum(d['r'] for d in rows_data))
                            acc_sheet.update_cell(user_row_idx, 5, int(user_data[4]) - sum(d['s'] for d in rows_data))
                            for d in rows_data:
                                hist_sheet.append_row([datetime.now().strftime('%m-%d %H:%M'), d['kw'], d['link'], d['l'], d['r'], d['s'], st.session_state.current_user])
                            st.success(UI_TEXT["SUCCESS_MSG"])
                            time.sleep(0.5)
                            st.rerun()

                with st.expander("📢 공지/링크", expanded=False):
                    for item in ANNOUNCEMENTS: st.markdown(f"**[{item['text']}]({item['url']})**")

        except Exception: st.error("데이터 로드 실패")
