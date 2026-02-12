import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. 대시보드 문구 및 공지 설정 ---
UI_TEXT = {
    "SUB_TITLE_REMAIN": "📊 잔여 수량",
    "SUB_TITLE_INPUT": "📝 작업 일괄 등록",
    "SUBMIT_BUTTON": "🔥 작업넣기",
    "ERROR_LACK": "❌ 잔여 수량이 부족합니다!",
    "SUCCESS_MSG": "🎊 모든 작업이 정상 등록되었습니다.",
    "LOGIN_TITLE": "### 🛡️ 크몽 파우쓰",
    "PROCESS_MSG": "📦 동기화 중..."
}

ANNOUNCEMENTS = [
    {"text": "👉 자동관리/방문자 서비스 바로가기", "url": "https://kmong.com/@파우쓰"},
    {"text": "👉 이웃추가 서비스 이용하기", "url": "https://kmong.com/@파우쓰"},
    {"text": "📢 신규 서비스 출시 공지 확인", "url": "https://kmong.com/@파우쓰"},
]

st.set_page_config(page_title="파우쓰 작업 자동화", layout="wide")

# --- 모바일 최적화 CSS 강화 ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; background-color: #FF4B4B; color: white; border: none; font-weight: bold; }
    [data-testid="stMetric"] { background-color: #1e2129; padding: 5px 10px; border-radius: 10px; border: 1px solid #333; }
    [data-testid="stMetricValue"] { font-size: 18px !important; }
    /* 모바일에서 여백 줄이기 */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
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

col_login, col_main = st.columns([1, 4], gap="small")

# --- 좌측/로그인 섹션 ---
with col_login:
    if not st.session_state.logged_in:
        st.markdown(UI_TEXT["LOGIN_TITLE"])
        u_id = st.text_input("ID", key="login_id")
        u_pw = st.text_input("PW", type="password", key="login_pw")
        if st.button("LOGIN", key="btn_login"):
            try:
                client = get_gspread_client()
                sh = client.open("작업_관리_데이터베이스")
                acc_sheet = sh.worksheet("Accounts")
                all_values = acc_sheet.get_all_values()
                for row in all_values[1:]:
                    if len(row) >= 2 and str(row[0]) == u_id and str(row[1]) == u_pw:
                        st.session_state.logged_in = True
                        st.session_state.current_user = u_id
                        st.session_state.nickname = row[5] if len(row) > 5 and row[5].strip() else u_id
                        st.rerun()
            except Exception as e: st.error(f"오류: {e}")
    else:
        # 로그인 상태일 때 모바일에서 이 부분이 위를 차지하지 않도록 최소화
        st.write(f"✅ **{st.session_state.nickname}**님")
        if st.button("LOGOUT", key="btn_logout"):
            st.session_state.logged_in = False
            st.rerun()

# --- 메인 작업 섹션 ---
with col_main:
    if st.session_state.logged_in:
        st.subheader(f"🚀 {st.session_state.nickname} 작업등록")
        
        try:
            client = get_gspread_client()
            sh = client.open("작업_관리_데이터베이스")
            acc_sheet = sh.worksheet("Accounts")
            hist_sheet = sh.worksheet("History")

            all_values = acc_sheet.get_all_values()
            user_row_idx, user_data = -1, []
            for idx, row in enumerate(all_values[1:], start=2):
                if row[0] == st.session_state.current_user:
                    user_row_idx, user_data = idx, row
                    break

            if user_row_idx != -1:
                # 수량 정보를 한 줄에 촘촘하게 배치 (모바일 스크롤 감소)
                m1, m2, m3 = st.columns(3)
                m1.metric("공감", f"{user_data[2]}")
                m2.metric("댓글", f"{user_data[3]}")
                m3.metric("스크랩", f"{user_data[4]}")

                st.markdown("---")
                
                rows_data = []
                # 입력창 레이아웃
                for i in range(10):
                    # 모바일에서 가로로 너무 길어지지 않게 컬럼 비율 조정
                    r_col = st.columns([2, 3, 1, 1, 1])
                    kw = r_col[0].text_input(f"k_{i}", label_visibility="collapsed", key=f"kw_{i}", placeholder="키워드")
                    link = r_col[1].text_input(f"u_{i}", label_visibility="collapsed", key=f"url_{i}", placeholder="URL")
                    l = r_col[2].number_input(f"l_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"l_{i}")
                    r = r_col[3].number_input(f"r_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"r_{i}")
                    s = r_col[4].number_input(f"s_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"s_{i}")
                    if kw and link: rows_data.append({"kw": kw, "link": link, "l": l, "r": r, "s": s})

                if st.button(UI_TEXT["SUBMIT_BUTTON"], key="btn_submit"):
                    if not rows_data: st.warning("⚠️ 데이터를 입력하세요.")
                    else:
                        with st.spinner(UI_TEXT["PROCESS_MSG"]):
                            # (중략: 데이터 차감 로직 동일)
                            acc_sheet.update_cell(user_row_idx, 3, int(user_data[2]) - sum(d['l'] for d in rows_data))
                            acc_sheet.update_cell(user_row_idx, 4, int(user_data[3]) - sum(d['r'] for d in rows_data))
                            acc_sheet.update_cell(user_row_idx, 5, int(user_data[4]) - sum(d['s'] for d in rows_data))
                            for d in rows_data:
                                hist_sheet.append_row([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), d['kw'], d['link'], d['l'], d['r'], d['s'], st.session_state.current_user])
                            st.success(UI_TEXT["SUCCESS_MSG"])
                            time.sleep(1)
                            st.rerun()
                
                # 공지사항을 맨 아래로 배치 (모바일 스크롤 편의성)
                st.markdown("<br><br>", unsafe_allow_html=True)
                with st.expander("📢 공지사항 및 서비스 링크 확인", expanded=False):
                    for item in ANNOUNCEMENTS:
                        st.markdown(f"**[{item['text']}]({item['url']})**")

        except Exception as e: st.error(f"오류: {e}")
    else:
        st.title("🚀 파우쓰 작업등록")
        st.info("좌측(또는 상단)에서 로그인을 진행해 주세요.")
