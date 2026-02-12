import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="작업 자동화 시스템", layout="wide")

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

with col_login:
    st.subheader("🔒 로그인")
    if not st.session_state.logged_in:
        u_id = st.text_input("아이디", key="input_id")
        u_pw = st.text_input("비밀번호", type="password", key="input_pw")
        if st.button("로그인", use_container_width=True):
            try:
                client = get_gspread_client()
                sh = client.open("작업_관리_데이터베이스")
                acc_sheet = sh.worksheet("Accounts")
                # values_get()을 사용하여 제목 상관없이 모든 데이터를 가져옵니다.
                all_values = acc_sheet.get_all_values() 
                
                if len(all_values) > 1:
                    # 1행은 제목이므로 제외하고 2행(all_values[1:])부터 검사
                    login_success = False
                    for row in all_values[1:]:
                        if str(row[0]) == u_id and str(row[1]) == u_pw:
                            st.session_state.logged_in = True
                            st.session_state.current_user = u_id
                            login_success = True
                            break
                    
                    if login_success:
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 틀립니다.")
                else:
                    st.error("시트 2행에 데이터가 없습니다.")
            except Exception as e:
                st.error(f"로그인 오류: {e}")
    else:
        st.success(f"✅ 접속 중: {st.session_state.current_user}")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()

with col_main:
    st.title("🚀 작업 자동화 시스템")
    
    if not st.session_state.logged_in:
        st.info("왼쪽 대시보드에서 로그인을 진행해주세요.")
    else:
        try:
            client = get_gspread_client()
            sh = client.open("작업_관리_데이터베이스")
            acc_sheet = sh.worksheet("Accounts")
            hist_sheet = sh.worksheet("History")

            all_values = acc_sheet.get_all_values()
            # 현재 로그인한 사용자의 행 찾기 (2행부터)
            user_row_idx = -1
            user_data = []
            for idx, row in enumerate(all_values[1:], start=2):
                if row[0] == st.session_state.current_user:
                    user_row_idx = idx
                    user_data = row
                    break

            if user_row_idx != -1:
                with st.expander("📊 나의 잔여 수량 확인", expanded=True):
                    # C, D, E열 값을 숫자로 변환하여 표시
                    display_df = pd.DataFrame([{
                        "ID": user_data[0],
                        "잔여_공감": user_data[2],
                        "잔여_댓글": user_data[3],
                        "잔여_스크랩": user_data[4]
                    }])
                    st.table(display_df)

                st.divider()
                st.subheader("📝 일괄 작업 등록 (최대 10행)")
                
                rows_data = []
                h_col = st.columns([1.5, 2.5, 0.8, 0.8, 0.8])
                h_col[0].caption("키워드")
                h_col[1].caption("링크")
                h_col[2].caption("공감")
                h_col[3].caption("댓글")
                h_col[4].caption("스크랩")

                for i in range(10):
                    r_col = st.columns([1.5, 2.5, 0.8, 0.8, 0.8])
                    kw = r_col[0].text_input(f"kw_{i}", label_visibility="collapsed")
                    link = r_col[1].text_input(f"link_{i}", label_visibility="collapsed")
                    l = r_col[2].number_input(f"l_{i}", min_value=0, step=1, label_visibility="collapsed")
                    r = r_col[3].number_input(f"r_{i}", min_value=0, step=1, label_visibility="collapsed")
                    s = r_col[4].number_input(f"s_{i}", min_value=0, step=1, label_visibility="collapsed")
                    if kw and link:
                        rows_data.append({"kw": kw, "link": link, "l": l, "r": r, "s": s})

                if st.button("🔥 전체 등록하기", type="primary", use_container_width=True):
                    if not rows_data:
                        st.warning("입력된 데이터가 없습니다.")
                    else:
                        with st.spinner("작업 처리 중..."):
                            total_l = sum(d['l'] for d in rows_data)
                            total_r = sum(d['r'] for d in rows_data)
                            total_s = sum(d['s'] for d in rows_data)

                            # 현재 수량 (숫자로 변환)
                            cur_l = int(user_data[2])
                            cur_r = int(user_data[3])
                            cur_s = int(user_data[4])

                            if cur_l >= total_l and cur_r >= total_r and cur_s >= total_s:
                                # 수량 차감 업데이트 (C, D, E열)
                                acc_sheet.update_cell(user_row_idx, 3, cur_l - total_l)
                                acc_sheet.update_cell(user_row_idx, 4, cur_r - total_r)
                                acc_sheet.update_cell(user_row_idx, 5, cur_s - total_s)

                                for d in rows_data:
                                    hist_sheet.append_row([
                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        d['kw'], d['link'], d['l'], d['r'], d['s'], st.session_state.current_user
                                    ])
                                st.success(f"✅ 총 {len(rows_data)}건 등록 완료!")
                                st.rerun()
                            else:
                                st.error("❌ 잔여 수량이 부족합니다.")
            else:
                st.error("사용자 정보를 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"오류 발생: {e}")
