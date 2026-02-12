import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="작업 자동화 시스템", layout="wide")

# 1. 로그인 세션 관리
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# 메인 레이아웃
col_login, col_main = st.columns([1, 4], gap="large")

# --- 왼쪽: 로그인 영역 (Accounts 시트 2열부터 참조) ---
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
                # get_all_records()는 자동으로 1행을 제목으로 인식하고 2행부터 데이터를 가져옵니다.
                acc_data = pd.DataFrame(acc_sheet.get_all_records())
                
                if not acc_data.empty:
                    user_match = acc_data[(acc_data['ID'].astype(str) == u_id) & (acc_data['PW'].astype(str) == u_pw)]
                    if not user_match.empty:
                        st.session_state.logged_in = True
                        st.session_state.current_user = u_id
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 틀립니다.")
                else:
                    st.error("시트에 데이터가 없습니다 (2행부터 입력 확인).")
            except Exception as e:
                st.error(f"로그인 오류: {e}")
    else:
        st.success(f"✅ 접속 중: {st.session_state.current_user}")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()

# --- 오른쪽: 작업 입력 영역 ---
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

            # 내 계정 정보 가져오기
            acc_data = pd.DataFrame(acc_sheet.get_all_records())
            my_info_all = acc_data[acc_data['ID'].astype(str) == st.session_state.current_user]
            
            if not my_info_all.empty:
                my_info = my_info_all.iloc[0]
                with st.expander("📊 나의 잔여 수량 확인", expanded=True):
                    st.table(pd.DataFrame([my_info[['ID', '잔여_공감', '잔여_댓글', '잔여_스크랩']]]))

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

                            if my_info['잔여_공감'] >= total_l and my_info['잔여_댓글'] >= total_r and my_info['잔여_스크랩'] >= total_s:
                                # 정확한 행 번호 계산 (index 0은 2행이 됨)
                                row_idx = my_info_all.index[0] + 2
                                
                                # Accounts 시트 수량 차감 업데이트 (C, D, E열)
                                acc_sheet.update_cell(row_idx, 3, int(my_info['잔여_공감'] - total_l))
                                acc_sheet.update_cell(row_idx, 4, int(my_info['잔여_댓글'] - total_r))
                                acc_sheet.update_cell(row_idx, 5, int(my_info['잔여_스크랩'] - total_s))

                                # History 시트 기록 (2행부터 순차적으로 추가됨)
                                for d in rows_data:
                                    hist_sheet.append_row([
                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        d['kw'], d['link'], d['l'], d['r'], d['s'], st.session_state.current_user
                                    ])
                                st.success(f"✅ 총 {len(rows_data)}건 등록 완료! 수량이 차감되었습니다.")
                                st.rerun()
                            else:
                                st.error("❌ 잔여 수량이 부족합니다.")
            else:
                st.error("계정 정보를 찾을 수 없습니다.")

        except Exception as e:
            st.error(f"오류 발생: {e}")
