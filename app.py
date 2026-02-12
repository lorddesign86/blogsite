import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. 대시보드 문구 및 공지 링크 설정 ---
UI_TEXT = {
    "MAIN_TITLE": "파우쓰 작업등록",
    "SUB_TITLE_REMAIN": "📊 잔여 수량",
    "SUB_TITLE_INPUT": "📝 작업 일괄 등록 (최대 10행)",
    "SUBMIT_BUTTON": "🔥 작업넣기",
    "ERROR_LACK": "❌ 잔여 수량이 부족합니다. 수량을 확인해주세요!",
    "SUCCESS_MSG": "🎊 성공! 모든 작업이 정상 등록되었습니다.",
    "LOGIN_TITLE": "### 크몽 파우쓰",
    "PROCESS_MSG": "📦 동기화 중... 잠시만 기다려주세요."
}

# --- 📢 [여기에서 공지사항과 링크를 수정하세요] ---
ANNOUNCEMENTS = [
    {"text": "👉 자동관리/방문자 서비스 바로가기", "url": "https://kmong.com/@파우쓰"},
    {"text": "👉 이웃추가 서비스 이용하기", "url": "https://kmong.com/@파우쓰"},
    {"text": "📢 신규 서비스 출시 공지 확인", "url": "https://kmong.com/@파우쓰"},
]

st.set_page_config(page_title="파우쓰 관리 시스템", layout="wide")

# 세션 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

col_login, col_main = st.columns([1, 4], gap="large")

# --- 좌측 사이드바 영역 ---
with col_login:
    st.markdown(UI_TEXT["LOGIN_TITLE"])
    
    if not st.session_state.logged_in:
        u_id = st.text_input("ID", placeholder="Enter ID", key="login_id_input")
        u_pw = st.text_input("PASSWORD", type="password", key="login_pw_input")
        if st.button("LOGIN", key="login_btn"):
            try:
                client = get_gspread_client()
                sh = client.open("작업_관리_데이터베이스")
                acc_sheet = sh.worksheet("Accounts")
                all_values = acc_sheet.get_all_values() 
                
                if len(all_values) > 1:
                    login_success = False
                    for row in all_values[1:]:
                        if len(row) >= 2 and str(row[0]) == u_id and str(row[1]) == u_pw:
                            st.session_state.logged_in = True
                            st.session_state.current_user = u_id
                            login_success = True
                            break
                    if login_success: st.rerun()
                    else: st.error("정보가 틀립니다.")
                else: st.error("데이터가 없습니다.")
            except Exception as e: st.error(f"오류: {e}")
    else:
        st.success(f"**{st.session_state.current_user}**님 환영합니다.")
        
        # 로그아웃 버튼
        if st.button("LOGOUT", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()

        st.markdown("---")
        st.markdown("### 📢 공지 및 서비스")
        
        # 텍스트 하이퍼링크 공지 생성
        for idx, item in enumerate(ANNOUNCEMENTS):
            st.markdown(f"**[{item['text']}]({item['url']})**")
            st.write("") # 간격 조절

# --- 우측 메인 작업 영역 ---
with col_main:
    st.title(UI_TEXT["MAIN_TITLE"])
    
    if not st.session_state.logged_in:
        st.info("왼쪽에서 로그인을 먼저 진행해주세요.")
    else:
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
                st.subheader(UI_TEXT["SUB_TITLE_REMAIN"])
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("ID", user_data[0])
                c2.metric("공감", f"{user_data[2]}개")
                c3.metric("댓글", f"{user_data[3]}개")
                c4.metric("스크랩", f"{user_data[4]}개")

                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader(UI_TEXT["SUB_TITLE_INPUT"])
                
                rows_data = []
                h_col = st.columns([2, 3, 1, 1, 1])
                headers = ["키워드", "URL (링크)", "공감", "댓글", "스크랩"]
                for i, h in enumerate(headers): h_col[i].caption(h)

                for i in range(10):
                    r_col = st.columns([2, 3, 1, 1, 1])
                    kw = r_col[0].text_input(f"k_{i}", label_visibility="collapsed", key=f"kw_{i}")
                    link = r_col[1].text_input(f"u_{i}", label_visibility="collapsed", key=f"url_{i}")
                    l = r_col[2].number_input(f"l_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"l_{i}")
                    r = r_col[3].number_input(f"r_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"r_{i}")
                    s = r_col[4].number_input(f"s_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"s_{i}")
                    if kw and link:
                        rows_data.append({"kw": kw, "link": link, "l": l, "r": r, "s": s})

                if st.button(UI_TEXT["SUBMIT_BUTTON"], key="submit_work_btn"):
                    if not rows_data:
                        st.warning("데이터를 입력해주세요.")
                    else:
                        with st.spinner(UI_TEXT["PROCESS_MSG"]):
                            # 동시성 방지를 위한 실시간 수량 재확인
                            fresh_vals = acc_sheet.get_all_values()
                            f_user = fresh_vals[user_row_idx-1]
                            total_l, total_r, total_s = sum(d['l'] for d in rows_data), sum(d['r'] for d in rows_data), sum(d['s'] for d in rows_data)
                            cur_l, cur_r, cur_s = int(f_user[2]), int(f_user[3]), int(f_user[4])

                            if cur_l >= total_l and cur_r >= total_r and cur_s >= total_s:
                                acc_sheet.update_cell(user_row_idx, 3, cur_l - total_l)
                                acc_sheet.update_cell(user_row_idx, 4, cur_r - total_r)
                                acc_sheet.update_cell(user_row_idx, 5, cur_s - total_s)
                                for d in rows_data:
                                    hist_sheet.append_row([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), d['kw'], d['link'], d['l'], d['r'], d['s'], st.session_state.current_user])
                                st.success(UI_TEXT["SUCCESS_MSG"])
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(UI_TEXT["ERROR_LACK"])
        except Exception as e:
            st.error(f"시스템 오류: {e}")
