import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --- 구글 시트 연결 ---
def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # Streamlit Secrets에 저장된 정보를 불러옵니다.
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

st.set_page_config(page_title="작업 관리 대시보드", layout="wide")
st.title("🚀 작업 자동화 시스템")

try:
    client = get_gspread_client()
    # 구글 스프레드시트 파일 이름 (정확히 일치해야 함)
    sh = client.open("작업_관리_데이터베이스") 
    acc_sheet = sh.worksheet("Accounts")
    hist_sheet = sh.worksheet("History")

    # 사이드바 입력창
    with st.sidebar:
        st.header("📝 새 작업 등록")
        keyword = st.text_input("키워드")
        link = st.text_input("링크")
        c1, c2, c3 = st.columns(3)
        l_cnt = c1.number_input("공감", min_value=0, step=1)
        r_cnt = c2.number_input("댓글", min_value=0, step=1)
        s_cnt = c3.number_input("스크랩", min_value=0, step=1)
        btn = st.button("등록하기", use_container_width=True)

    # 데이터 표시
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 계정 잔여 수량")
        acc_df = pd.DataFrame(acc_sheet.get_all_records())
        st.table(acc_df)
    with col2:
        st.subheader("📜 최근 내역")
        hist_df = pd.DataFrame(hist_sheet.get_all_records())
        st.dataframe(hist_df.tail(15))

    # 등록 버튼 클릭 시 로직
    if btn:
        if not keyword or not link:
            st.error("키워드와 링크를 입력해주세요.")
        else:
            success = False
            for i, row in acc_df.iterrows():
                if row['잔여_공감'] >= l_cnt and row['잔여_댓글'] >= r_cnt and row['잔여_스크랩'] >= s_cnt:
                    # 차감 업데이트
                    acc_sheet.update_cell(i+2, 2, int(row['잔여_공감'] - l_cnt))
                    acc_sheet.update_cell(i+2, 3, int(row['잔여_댓글'] - r_cnt))
                    acc_sheet.update_cell(i+2, 4, int(row['잔여_스크랩'] - s_cnt))
                    # 내역 추가
                    hist_sheet.append_row([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), keyword, link, l_cnt, r_cnt, s_cnt, row['ID']])
                    st.success(f"✅ {row['ID']} 계정으로 등록 완료!")
                    success = True
                    st.rerun()
                    break
            if not success:
                st.error("❌ 수량이 충분한 계정이 없습니다.")
except Exception as e:
    st.info("구글 시트 연결 대기 중입니다. Streamlit Cloud의 Secrets 설정을 완료해주세요.")
