import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time
import re

# --- 1. 기본 설정 및 디자인 ---
st.set_page_config(page_title="파우쓰", layout="wide")

st.markdown("""
    <style>
    /* 상단 여백 보정 및 짤림 방지 */
    .main .block-container { padding-top: 2rem !important; padding-bottom: 6rem !important; }
    
    /* [핵심] 잔여 수량 가로 한 줄 강제 정렬 */
    div[data-testid="stHorizontalBlock"] { gap: 0.2rem !important; }
    [data-testid="stMetric"] { 
        background-color: #1e2129; padding: 4px 2px !important; 
        border-radius: 6px; text-align: center; border: 1px solid #333;
        min-width: 0px !important;
    }
    [data-testid="stMetricValue"] { font-size: 0.9rem !important; font-weight: 700 !important; color: #00ff00; }
    [data-testid="stMetricLabel"] { font-size: 0.65rem !important; }

    /* 입력창 디자인: 음영 가이드 및 간격 밀착 */
    .stTextInput, .stNumberInput { margin-bottom: -18px !important; }
    .stTextInput input { font-size: 14px !important; height: 32px !important; }
    
    /* 모바일 하단 고정 버튼 */
    @media (max-width: 768px) {
        div.stButton > button:first-child {
            position: fixed; bottom: 10px; left: 5%; right: 5%; width: 90%; z-index: 999;
            height: 3.5rem; background-color: #FF4B4B !important; border-radius: 12px; font-weight: bold;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 네이버 블로그 링크 검증 함수 ---
def is_valid_naver_link(url):
    # https://blog.naver.com/아이디/게시글번호 또는 https://m.blog.naver.com/아이디/게시글번호 형식 검사
    pattern = r'^https?://(m\.)?blog\.naver\.com/[\w-]+/\d+$'
    return re.match(pattern, url.strip()) is not None

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 메인 로직 ---
if not st.session_state.logged_in:
    st.markdown("### 🛡️ 파우쓰 로그인")
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
        except Exception: st.error("로그인 실패")
else:
    try:
        client = get_gspread_client()
        sh = client.open("작업_관리_데이터베이스")
        acc_sheet, hist_sheet = sh.worksheet("Accounts"), sh.worksheet("History")
        all_values = acc_sheet.get_all_values()
        user_row_idx, user_data = next(((i, r) for i, r in enumerate(all_values[1:], 2) if r[0] == st.session_state.current_user), (-1, []))

        if user_row_idx != -1:
            # 🚀 상단: 잔여 수량 가로 한 줄 (모바일 최적화)
            st.markdown(f"#### 🚀 {st.session_state.nickname} 작업등록")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("공감", user_data[2])
            m2.metric("댓글", user_data[3])
            m3.metric("스크랩", user_data[4])
            m4.metric("ID", user_data[0])
            st.divider()

            # 📝 중단: 작업 입력 (최대 10행)
            h_col = st.columns([2, 3, 0.8, 0.8, 0.8])
            for i, txt in enumerate(["키워드", "URL (필수)", "공", "댓", "스"]): h_col[i].caption(txt)

            rows_data = []
            link_errors = []
            for i in range(10):
                r_col = st.columns([2, 3, 0.8, 0.8, 0.8])
                kw = r_col[0].text_input(f"k_{i}", label_visibility="collapsed", key=f"kw_{i}", placeholder="(키워드)")
                url = r_col[1].text_input(f"u_{i}", label_visibility="collapsed", key=f"url_{i}", placeholder="(링크 입력)")
                l = r_col[2].number_input(f"l_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"l_{i}")
                r = r_col[3].number_input(f"r_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"r_{i}")
                s = r_col[4].number_input(f"s_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"s_{i}")
                
                if url.strip():
                    # 1. 링크 형식 검사
                    if not is_valid_naver_link(url):
                        link_errors.append(f"{i+1}행 링크 오류")
                    # 2. 작업 수량 검사 (최소 하나는 1 이상)
                    elif l > 0 or r > 0 or s > 0:
                        rows_data.append({"kw": kw if kw else "", "link": url, "l": l, "r": r, "s": s})

            # 🔥 하단: 등록 버튼 (모바일 고정)
            if st.button("🔥 작업넣기", type="primary", key="submit_btn"):
                if link_errors:
                    st.error(f"⚠️ {' / '.join(link_errors)}: 네이버 블로그 형식이 아닙니다.")
                elif not rows_data:
                    st.warning("⚠️ 등록할 링크와 작업 수량(최소 1개 이상)을 입력해 주세요.")
                else:
                    with st.spinner("📦 데이터 전송 중..."):
                        t_l, t_r, t_s = sum(d['l'] for d in rows_data), sum(d['r'] for d in rows_data), sum(d['s'] for d in rows_data)
                        if int(user_data[2]) >= t_l and int(user_data[3]) >= t_r and int(user_data[4]) >= t_s:
                            acc_sheet.update_cell(user_row_idx, 3, int(user_data[2]) - t_l)
                            acc_sheet.update_cell(user_row_idx, 4, int(user_data[3]) - t_r)
                            acc_sheet.update_cell(user_row_idx, 5, int(user_data[4]) - t_s)
                            for d in rows_data:
                                hist_sheet.append_row([datetime.now().strftime('%Y-%m-%d %H:%M'), d['kw'], d['link'], d['l'], d['r'], d['s'], st.session_state.current_user])
                            st.success("🎊 모든 작업이 정상 등록되었습니다.")
                            time.sleep(1)
                            st.rerun()
                        else: st.error("❌ 잔여 수량이 부족합니다.")

            if st.button("LOGOUT"):
                st.session_state.clear()
                st.rerun()
    except Exception: st.error("데이터 연동 중 오류가 발생했습니다.")
