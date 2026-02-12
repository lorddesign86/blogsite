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

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# 메인 레이아웃
col_login, col_main = st.columns([1, 4], gap="large")

# --- 왼쪽: 로그인 영역 ---
with col_login:
    st.subheader("🔒 로그인")
    if not st.session_state.logged_in:
        user_id = st.text_input("아이디", key="login_id")
        user_pw = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("로그인", use_container_width=True):
            if user_id == "admin" and user_pw == "1234": # 원하는 비번으로 수정
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("불일치")
    else:
        st.success("✅ 인증됨 (admin)")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# --- 오른쪽: 작업 입력 영역 ---
with col_main:
    st.title("🚀 작업 자동화 시스템")
    
    if not st.session_state.logged_in:
        st.info("왼쪽에서 로그인을 먼저 진행해주세요.")
    else:
        try:
            client = get_gspread_client()
            sh = client.open("작업_관리_데이터베이스")
            acc_sheet = sh.worksheet("Accounts")
            hist_sheet = sh.worksheet("History")

            # 실시간 현황 표 표시
            with st.expander("📊 현재 계정 잔여 수량 보기", expanded=True):
                acc_df = pd.DataFrame(acc_sheet.get_all_records())
                st.dataframe(acc_df, use_container_width=True)

            st.divider()
            st.subheader("📝 일괄 작업 등록 (최대 10행)")
            
            # 10개 행 입력을 위한 리스트
            rows_data = []
            
            # 헤더 라인
            h_col = st.columns([1.5, 2.5, 0.8, 0.8, 0.8])
            h_col[0].caption("키워드")
            h_col[1].caption("링크")
            h_col[2].caption("공감")
            h_col[3].caption("댓글")
            h_col[4].caption("스크랩")

            # 10개 행 생성
            for i in range(10):
                r_col = st.columns([1.5, 2.5, 0.8, 0.8, 0.8])
                kw = r_col[0].text_input(f"kw_{i}", label_visibility="collapsed")
                link = r_col[1].text_input(f"link_{i}", label_visibility="collapsed")
                l = r_col[2].number_input(f"l_{i}", min_value=0, step=1, label_visibility="collapsed")
                r = r_col[3].number_input(f"r_{i}", min_value=0, step=1, label_visibility="collapsed")
                s = r_col[4].number_input(f"s_{i}", min_value=0, step=1, label_visibility="collapsed")
                
                if kw and link: # 키워드와 링크가 입력된 행만 추출
                    rows_data.append({"kw": kw, "link": link, "l": l, "r": r, "s": s})

            st.write("")
            if st.button("🔥 전체 등록하기", type="primary", use_container_width=True):
                if not rows_data:
                    st.warning("입력된 데이터가 없습니다.")
                else:
                    with st.spinner("구글 시트에 기록 중..."):
                        acc_df = pd.DataFrame(acc_sheet.get_all_records())
                        process_count = 0
                        
                        for data in rows_data:
                            success = False
                            for idx, acc in acc_df.iterrows():
                                # 수량 체크
                                if (acc['잔여_공감'] >= data['l'] and 
                                    acc['잔여_댓글'] >= data['r'] and 
                                    acc['잔여_스크랩'] >= data['s']):
                                    
                                    # 시트 차감 업데이트
                                    row_num = idx + 2
                                    acc_sheet.update_cell(row_num, 2, int(acc['잔여_공감'] - data['l']))
                                    acc_sheet.update_cell(row_num, 3, int(acc['잔여_댓글'] - data['r']))
                                    acc_sheet.update_cell(row_num, 4, int(acc['잔여_스크랩'] - data['s']))
                                    
                                    # 내역 기록
                                    hist_sheet.append_row([
                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        data['kw'], data['link'], data['l'], data['r'], data['s'], acc['ID']
                                    ])
                                    
                                    # 메모리 상의 데이터도 업데이트 (다음 행 처리를 위해)
                                    acc_df.at[idx, '잔여_공감'] -= data['l']
                                    acc_df.at[idx, '잔여_댓글'] -= data['r']
                                    acc_df.at[idx, '잔여_스크랩'] -= data['s']
                                    
                                    success = True
                                    process_count += 1
                                    break
                            
                            if not success:
                                st.error(f"❌ '{data['kw']}' 작업: 잔여 수량이 부족한 계정이 없습니다.")
                        
                        if process_count > 0:
                            st.success(f"✅ 총 {process_count}건의 작업이 성공적으로 등록되었습니다!")
                            st.rerun()

        except Exception as e:
            st.error(f"연결 오류: {e}")
            st.info("구글 시트의 탭 이름(Accounts, History)과 헤더를 확인해주세요.")
