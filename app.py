import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# 페이지 설정 및 테마 개선
st.set_page_config(page_title="Task Automation Pro", layout="wide")

# 스타일 커스텀 (버튼 및 테이블 강조)
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #FF4B4B; color: white; border: none; font-weight: bold; }
    .stTable { border-radius: 10px; overflow: hidden; }
    .css-1kyxreq { background-color: #f0f2f6; padding: 20px; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

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

# --- 좌측 사이드: 로그인 섹션 ---
with col_login:
    st.markdown("###**크몽 파우쓰**")
    if not st.session_state.logged_in:
        u_id = st.text_input("ID", placeholder="Enter ID", key="input_id")
        u_pw = st.text_input("PASSWORD", type="password", placeholder="••••", key="input_pw")
        if st.button("LOGIN"):
            try:
                client = get_gspread_client()
                sh = client.open("작업_관리_데이터베이스")
                acc_sheet = sh.worksheet("Accounts")
                all_values = acc_sheet.get_all_values() 
                
                login_success = False
                if len(all_values) > 1:
                    for row in all_values[1:]:
                        if len(row) >= 2 and str(row[0]) == u_id and str(row[1]) == u_pw:
                            st.session_state.logged_in = True
                            st.session_state.current_user = u_id
                            login_success = True
                            break
                if login_success: st.rerun()
                else: st.error("Invalid Credentials")
            except Exception as e: st.error(f"Error: {e}")
    else:
        st.success(f"**{st.session_state.current_user}**님 환영합니다.")
        st.info("자동관리, 방문자, 이웃서비스는 크몽에서 이용해주세요. https://kmong.com/@파우쓰 ")
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()

# --- 좌측 사이드: 로그인 섹션 ---

with col_login:
    # (중략: 로그인 성공 메시지 출력 부분 아래)
    st.success(f"**{st.session_state.current_user}**님 환영합니다.")
    
    # --------------------------------------------------
    # 🎁 [마케팅 배너 영역 시작]
    # --------------------------------------------------
    st.markdown("---")  # 구분선
    st.markdown("### 📢 추천 서비스")

    # 배너 1: 이미지 클릭 시 링크 이동
    st.markdown(f'''
        <a href="https://kmong.com/특정서비스1" target="_blank">
            <img src="https://이미지주소1.png" width="100%" style="border-radius: 10px; margin-bottom: 10px;">
        </a>
    ''', unsafe_allow_html=True)

    # 배너 2: 이미지 클릭 시 링크 이동
    st.markdown(f'''
        <a href="https://kmong.com/특정서비스2" target="_blank">
            <img src="https://이미지주소2.png" width="100%" style="border-radius: 10px; margin-bottom: 10px;">
        </a>
    ''', unsafe_allow_html=True)

    # 배너 3: 텍스트 형태의 공지나 링크가 필요한 경우
    st.info("💡 [공지] 신규 서비스 출시! 확인해보세요.")
    # --------------------------------------------------

    if st.button("LOGOUT"):
        st.session_state.logged_in = False
        st.rerun()


# --- 우측 메인: 대시보드 및 입력 섹션 ---
with col_main:
    st.title("파우쓰 작업등록")
    
    if not st.session_state.logged_in:
        st.warning("로그인 후 시스템을 이용하실 수 있습니다.")
    else:
        try:
            client = get_gspread_client()
            sh = client.open("작업_관리_데이터베이스")
            acc_sheet = sh.worksheet("Accounts")
            hist_sheet = sh.worksheet("History")

            # 실시간 수량 조회 (동시성 보장을 위해 매번 새로 읽기)
            all_values = acc_sheet.get_all_values()
            user_row_idx = -1
            user_data = []
            for idx, row in enumerate(all_values[1:], start=2):
                if row[0] == st.session_state.current_user:
                    user_row_idx = idx
                    user_data = row
                    break

            if user_row_idx != -1:
                # 상단 잔여 수량 위젯 디자인
                st.subheader("📊 **잔여 수량**")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("ID", user_data[0])
                c2.metric("공감", f"{user_data[2]}개", delta_color="normal")
                c3.metric("댓글", f"{user_data[3]}개")
                c4.metric("스크랩", f"{user_data[4]}개")

                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("📝 **작업 일괄 등록 (최대 10행)**")
                
                # 입력 테이블 헤더
                rows_data = []
                h_col = st.columns([2, 3, 1, 1, 1])
                h_col[0].markdown("**키워드**")
                h_col[1].markdown("**URL (링크)**")
                h_col[2].markdown("**공감**")
                h_col[3].markdown("**댓글**")
                h_col[4].markdown("**스크랩**")

                for i in range(10):
                    r_col = st.columns([2, 3, 1, 1, 1])
                    kw = r_col[0].text_input(f"k_{i}", label_visibility="collapsed", placeholder=f"키워드 {i+1}")
                    link = r_col[1].text_input(f"u_{i}", label_visibility="collapsed", placeholder="https://...")
                    l = r_col[2].number_input(f"l_{i}", min_value=0, step=1, label_visibility="collapsed")
                    r = r_col[3].number_input(f"r_{i}", min_value=0, step=1, label_visibility="collapsed")
                    s = r_col[4].number_input(f"s_{i}", min_value=0, step=1, label_visibility="collapsed")
                    if kw and link:
                        rows_data.append({"kw": kw, "link": link, "l": l, "r": r, "s": s})

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔥 전체 작업 데이터베이스 전송"):
                    if not rows_data:
                        st.warning("⚠️ 등록할 데이터를 하나 이상 입력해주세요.")
                    else:
                        with st.spinner("📦 동기화 중... 잠시만 기다려주세요."):
                            # 전송 직전 수량 재확인 (동시 작업 방지)
                            fresh_values = acc_sheet.get_all_values()
                            fresh_user = fresh_values[user_row_idx-1]
                            
                            total_l = sum(d['l'] for d in rows_data)
                            total_r = sum(d['r'] for d in rows_data)
                            total_s = sum(d['s'] for d in rows_data)

                            cur_l, cur_r, cur_s = int(fresh_user[2]), int(fresh_user[3]), int(fresh_user[4])

                            if cur_l >= total_l and cur_r >= total_r and cur_s >= total_s:
                                # 1. 시트 수량 차감
                                acc_sheet.update_cell(user_row_idx, 3, cur_l - total_l)
                                acc_sheet.update_cell(user_row_idx, 4, cur_r - total_r)
                                acc_sheet.update_cell(user_row_idx, 5, cur_s - total_s)

                                # 2. 내역 기록 (2행부터 누적)
                                for d in rows_data:
                                    hist_sheet.append_row([
                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        d['kw'], d['link'], d['l'], d['r'], d['s'], st.session_state.current_user
                                    ])
                                st.success(f"🎊 성공! 총 {len(rows_data)}건의 작업이 정상 등록되었습니다.")
                                time.sleep(1) # 유저가 메시지를 볼 시간
                                st.rerun()
                            else:
                                st.error(f"❌ 잔여 수량이 부족합니다. 크몽에서 충전 후 이용해주세요.(필요 공감: {total_l}, 현재: {cur_l}) kmong.com/@파우쓰 ")
            else:
                st.error("사용자 정보를 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"시스템 오류: {e}")
