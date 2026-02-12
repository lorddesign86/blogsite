import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time
import re

# --- 1. 기본 설정 및 디자인 ---
st.set_page_config(page_title="파우쓰", layout="wide")

# 사이드바 링크 설정 (image_4f4538.png 기준)
ANNOUNCEMENTS = [
    {"text": "👉 파우쓰 서비스 전체보기", "url": "https://kmong.com/@파우쓰"},
    {"text": "📢 스댓공 월 자동서비스", "url": "https://kmong.com/@파우쓰"},
    {"text": "📢 스댓공 개별서비스", "url": "https://kmong.com/@파우쓰"},
    {"text": "📢 방문자 서비스 보러가", "url": "https://kmong.com/@파우쓰"},
    {"text": "📢 이웃 서비스 100~700명", "url": "https://kmong.com/@파우쓰"},
    {"text": "📢 최적화 블로그리스트 추출프로그램", "url": "https://kmong.com/@파우쓰"},
]

# --- 🎨 PC/모바일 하이브리드 CSS ---
st.markdown("""
    <style>
    /* 상단 잘림 방지 및 여백 */
    .main .block-container { padding-top: 2.5rem !important; padding-bottom: 6rem !important; }
    
    /* [중요] 잔여 수량 위젯 가로 한 줄 강제 정렬 */
    div[data-testid="stHorizontalBlock"] { gap: 0.3rem !important; }
    [data-testid="stMetric"] { 
        background-color: #1e2129; padding: 6px 2px !important; 
        border-radius: 8px; text-align: center; border: 1px solid #333;
        min-width: 0px !important;
    }
    [data-testid="stMetricValue"] { font-size: 1rem !important; font-weight: 700 !important; color: #2ecc71; }
    [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }

    /* 입력창 디자인 최적화 */
    .stTextInput, .stNumberInput { margin-bottom: -15px !important; }
    
    /* 모바일 전용 하단 고정 버튼 */
    @media (max-width: 768px) {
        div.stButton > button:first-child {
            position: fixed; bottom: 15px; left: 5%; right: 5%; width: 90%; z-index: 999;
            height: 3.5rem; background-color: #FF4B4B !important; border-radius: 15px; font-weight: bold;
            box-shadow: 0 4px 20px rgba(0,0,0,0.6);
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 링크 검증 함수 ---
def is_valid_naver_link(url):
    # https://blog.naver.com/아이디/게시글번호 형식 검사
    pattern = r'^https?://(m\.)?blog\.naver\.com/[\w-]+/\d+$'
    return re.match(pattern, url.strip()) is not None

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 🏠 레이아웃 구성 ---
if not st.session_state.logged_in:
    # 로그인 화면
    st.markdown("### 🛡️ 파우쓰 로그인")
    u_id = st.text_input("ID")
    u_pw = st.text_input("PW", type="password")
    if st.button("LOGIN"):
        client = get_gspread_client()
        sh = client.open("작업_관리_데이터베이스")
        acc_sheet = sh.worksheet("Accounts")
        all_vals = acc_sheet.get_all_values()
        for row in all_vals[1:]:
            if len(row) >= 2 and str(row[0]) == u_id and str(row[1]) == u_pw:
                st.session_state.logged_in, st.session_state.current_user = True, u_id
                st.session_state.nickname = row[5] if len(row) > 5 and row[5].strip() else u_id
                st.rerun()
else:
    # --- 로그인 완료 후 PC 사이드바 복구 ---
    with st.sidebar:
        st.success(f"✅ **{st.session_state.nickname}**님")
        if st.button("LOGOUT"):
            st.session_state.clear()
            st.rerun()
        st.divider()
        st.markdown("### 📢 서비스 링크")
        for item in ANNOUNCEMENTS:
            st.markdown(f"**[{item['text']}]({item['url']})**")

    # --- 메인 작업 영역 ---
    try:
        client = get_gspread_client()
        sh = client.open("작업_관리_데이터베이스")
        acc_sheet, hist_sheet = sh.worksheet("Accounts"), sh.worksheet("History")
        all_values = acc_sheet.get_all_values()
        user_row_idx, user_data = next(((i, r) for i, r in enumerate(all_values[1:], 2) if r[0] == st.session_state.current_user), (-1, []))

        if user_row_idx != -1:
            st.markdown(f"### 🚀 {st.session_state.nickname} 작업등록")
            st.write("📊 실시간 잔여 수량")
            
            # [요청] 모바일 가로 한 줄 (4개 지표)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("공감", f"{user_data[2]}개")
            m2.metric("댓글", f"{user_data[3]}개")
            m3.metric("스크랩", f"{user_data[4]}개")
            m4.metric("접속ID", user_data[0])
            st.divider()

            # 작업 입력 헤더
            st.write("📝 작업 일괄 등록")
            h_col = st.columns([2, 3, 0.8, 0.8, 0.8])
            for i, txt in enumerate(["키워드", "URL (링크)", "공", "댓", "스"]): h_col[i].caption(txt)

            rows_data, link_errors = [], []
            for i in range(10):
                r_col = st.columns([2, 3, 0.8, 0.8, 0.8])
                kw = r_col[0].text_input(f"k_{i}", label_visibility="collapsed", key=f"kw_{i}", placeholder="키워드")
                url = r_col[1].text_input(f"u_{i}", label_visibility="collapsed", key=f"url_{i}", placeholder="URL")
                l = r_col[2].number_input(f"l_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"l_{i}")
                r = r_col[3].number_input(f"r_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"r_{i}")
                s = r_col[4].number_input(f"s_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"s_{i}")
                
                if url.strip():
                    if not is_valid_naver_link(url): link_errors.append(f"{i+1}행")
                    elif l > 0 or r > 0 or s > 0:
                        rows_data.append({"kw": kw if kw else "", "link": url, "l": l, "r": r, "s": s})

            # 🔥 등록 버튼 (PC에선 하단, 모바일에선 고정)
            if st.button("🔥 작업넣기", type="primary", key="submit_btn"):
                if link_errors: st.error(f"⚠️ {', '.join(link_errors)} 링크 형식을 확인해주세요.")
                elif not rows_data: st.warning("⚠️ 링크와 수량을 입력해주세요.")
                else:
                    with st.spinner("📦 처리 중..."):
                        t_l, t_r, t_s = sum(d['l'] for d in rows_data), sum(d['r'] for d in rows_data), sum(d['s'] for d in rows_data)
                        if int(user_data[2]) >= t_l and int(user_data[3]) >= t_r and int(user_data[4]) >= t_s:
                            acc_sheet.update_cell(user_row_idx, 3, int(user_data[2]) - t_l)
                            acc_sheet.update_cell(user_row_idx, 4, int(user_data[3]) - t_r)
                            acc_sheet.update_cell(user_row_idx, 5, int(user_data[4]) - t_s)
                            for d in rows_data:
                                hist_sheet.append_row([datetime.now().strftime('%m-%d %H:%M'), d['kw'], d['link'], d['l'], d['r'], d['s'], st.session_state.current_user])
                            st.success("🎊 등록 완료!")
                            time.sleep(1)
                            st.rerun()
                        else: st.error("❌ 잔여 수량이 부족합니다.")

    except Exception: st.error("연동 실패")
