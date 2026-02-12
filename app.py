import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. 대시보드 문구 및 공지 설정 ---
UI_TEXT = {
    "SUB_TITLE_REMAIN": "📊 실시간 잔여 수량",
    "SUB_TITLE_INPUT": "📝 작업 일괄 등록 (최대 10행)",
    "SUBMIT_BUTTON": "🔥 작업넣기",
    "ERROR_LACK": "❌ 잔여 수량이 부족합니다. 수량을 확인해주세요!",
    "SUCCESS_MSG": "🎊 성공! 모든 작업이 정상 등록되었습니다.",
    "LOGIN_TITLE": "### 🛡️ 크몽 파우쓰",
    "PROCESS_MSG": "📦 구글 데이터베이스 동기화 중..."
}

# --- 📢 사이드바 공지 및 하이퍼링크 ---
ANNOUNCEMENTS = [
    {"text": "👉 파우쓰 서비스 전체보기", "url": "https://kmong.com/@파우쓰"},
    {"text": "📢 스댓공 월 자동서비스", "url": "https://kmong.com/gig/645544"},
    {"text": "📢 스댓공 개별서비스", "url": "https://kmong.com/gig/445340"},
    {"text": "📢 방문자 서비스 보러가", "url": "https://caring-kayak-cd7.notion.site/27707671d021808a9567edb8ad065b28?source=copy_link"},
    {"text": "📢 이웃 서비스 100~700명", "url": "https://kmong.com/gig/668226"},
    {"text": "📢 최적화 블로그리스트 추출프로그램", "url": "https://kmong.com/gig/725815"},

]

# 페이지 설정
st.set_page_config(page_title="파우쓰 작업 자동화", layout="wide")

# CSS 스타일 적용
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #FF4B4B; color: white; border: none; font-weight: bold; }
    .stMetric { background-color: #1e2129; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# 세션 관리
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'nickname' not in st.session_state:
    st.session_state.nickname = ""

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

col_login, col_main = st.columns([1, 4], gap="large")

# --- 좌측 사이드바: 로그인 및 공지사항 ---
with col_login:
    st.markdown(UI_TEXT["LOGIN_TITLE"])
    
    if not st.session_state.logged_in:
        u_id = st.text_input("ID", placeholder="아이디 입력", key="login_id")
        u_pw = st.text_input("PW", type="password", placeholder="비밀번호 입력", key="login_pw")
        if st.button("LOGIN", key="btn_login"):
            try:
                client = get_gspread_client()
                sh = client.open("작업_관리_데이터베이스")
                acc_sheet = sh.worksheet("Accounts")
                all_values = acc_sheet.get_all_values()
                
                if len(all_values) > 1:
                    found = False
                    for row in all_values[1:]:
                        if len(row) >= 2 and str(row[0]) == u_id and str(row[1]) == u_pw:
                            st.session_state.logged_in = True
                            st.session_state.current_user = u_id
                            # F열(index 5) 닉네임 확인 로직
                            if len(row) > 5 and row[5].strip():
                                st.session_state.nickname = row[5]
                            else:
                                st.session_state.nickname = u_id
                            found = True
                            break
                    if found: st.rerun()
                    else: st.error("정보가 일치하지 않습니다.")
                else: st.error("계정 데이터가 존재하지 않습니다.")
            except Exception as e: st.error(f"연결 오류: {e}")
    else:
        st.success(f"✅ **{st.session_state.nickname}**님 접속 중")
        if st.button("LOGOUT", key="btn_logout"):
            st.session_state.logged_in = False
            st.rerun()

        st.markdown("---")
        st.markdown("### 📢 공지 및 서비스")
        for idx, item in enumerate(ANNOUNCEMENTS):
            st.markdown(f"**[{item['text']}]({item['url']})**")
            st.write("")

# --- 우측 메인: 작업 관리 영역 ---
with col_main:
    # 닉네임 기반 타이틀 동적 표시
    if st.session_state.logged_in:
        st.title(f"🚀 {st.session_state.nickname} 님의 작업등록")
    else:
        st.title("🚀 파우쓰 작업등록")

    if not st.session_state.logged_in:
        st.info("좌측 로그인 창을 통해 인증을 완료해 주세요.")
    else:
        try:
            client = get_gspread_client()
            sh = client.open("작업_관리_데이터베이스")
            acc_sheet = sh.worksheet("Accounts")
            hist_sheet = sh.worksheet("History")

            # 실시간 수량 읽기
            all_values = acc_sheet.get_all_values()
            user_row_idx, user_data = -1, []
            for idx, row in enumerate(all_values[1:], start=2):
                if row[0] == st.session_state.current_user:
                    user_row_idx, user_data = idx, row
                    break

            if user_row_idx != -1:
                # 수량 대시보드 위젯
                st.subheader(UI_TEXT["SUB_TITLE_REMAIN"])
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("접속 ID", user_data[0])
                c2.metric("잔여 공감", f"{user_data[2]}개")
                c3.metric("잔여 댓글", f"{user_data[3]}개")
                c4.metric("잔여 스크랩", f"{user_data[4]}개")

                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader(UI_TEXT["SUB_TITLE_INPUT"])
                
                # 입력 그리드 설정
                rows_data = []
                h_col = st.columns([2, 3, 1, 1, 1])
                for i, head in enumerate(["키워드", "URL (링크)", "공감", "댓글", "스크랩"]):
                    h_col[i].caption(head)

                for i in range(10):
                    r_col = st.columns([2, 3, 1, 1, 1])
                    kw = r_col[0].text_input(f"k_{i}", label_visibility="collapsed", key=f"kw_{i}", placeholder="키워드")
                    link = r_col[1].text_input(f"u_{i}", label_visibility="collapsed", key=f"url_{i}", placeholder="https://...")
                    l = r_col[2].number_input(f"l_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"l_{i}")
                    r = r_col[3].number_input(f"r_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"r_{i}")
                    s = r_col[4].number_input(f"s_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"s_{i}")
                    if kw and link:
                        rows_data.append({"kw": kw, "link": link, "l": l, "r": r, "s": s})

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(UI_TEXT["SUBMIT_BUTTON"], key="btn_final_submit"):
                    if not rows_data:
                        st.warning("⚠️ 등록할 데이터를 1줄 이상 입력해 주세요.")
                    else:
                        with st.spinner(UI_TEXT["PROCESS_MSG"]):
                            # 차감 전 수량 최신화
                            fresh_vals = acc_sheet.get_all_values()
                            f_user = fresh_vals[user_row_idx-1]
                            total_l = sum(d['l'] for d in rows_data)
                            total_r = sum(d['r'] for d in rows_data)
                            total_s = sum(d['s'] for d in rows_data)
                            
                            cur_l, cur_r, cur_s = int(f_user[2]), int(f_user[3]), int(f_user[4])

                            if cur_l >= total_l and cur_r >= total_r and cur_s >= total_s:
                                # 1. Accounts 차감 (C, D, E열)
                                acc_sheet.update_cell(user_row_idx, 3, cur_l - total_l)
                                acc_sheet.update_cell(user_row_idx, 4, cur_r - total_r)
                                acc_sheet.update_cell(user_row_idx, 5, cur_s - total_s)
                                
                                # 2. History 누적 (2행부터 쌓임)
                                for d in rows_data:
                                    hist_sheet.append_row([
                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        d['kw'], d['link'], d['l'], d['r'], d['s'], st.session_state.current_user
                                    ])
                                st.success(UI_TEXT["SUCCESS_MSG"])
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error(UI_TEXT["ERROR_LACK"])
            else:
                st.error("사용자 계정 정보를 시트에서 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"⚠️ 시스템 오류 발생: {e}")
