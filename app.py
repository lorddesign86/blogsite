import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time

# --- 1. 기본 설정 및 문구 ---
UI_TEXT = {
    "SUB_TITLE_REMAIN": "📊 실시간 잔여 수량",
    "SUB_TITLE_INPUT": "📝 작업 일괄 등록",
    "SUBMIT_BUTTON": "🔥 작업넣기",
    "LOGIN_TITLE": "### 🛡️ 파우쓰 관리자",
    "SUCCESS_MSG": "🎊 모든 작업이 정상 등록되었습니다."
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

st.set_page_config(page_title="파우쓰", layout="wide")

# --- 🎨 기기별 맞춤형 CSS 보정 ---
st.markdown("""
    <style>
    /* 공통: 상단 여백 보정 */
    .main .block-container { padding-top: 2rem !important; }
    
    /* 숫자 카드(Metric) 디자인 */
    [data-testid="stMetric"] { background-color: #1e2129; padding: 8px !important; border-radius: 10px; border: 1px solid #444; text-align: center; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; color: #00ff00; }

    /* 모바일 전용: 하단 고정 버튼 */
    @media (max-width: 768px) {
        div.stButton > button:first-child {
            position: fixed; bottom: 10px; left: 5%; right: 5%; width: 90%; z-index: 999;
            height: 3.5rem; background-color: #FF4B4B !important; border-radius: 15px; font-weight: bold;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }
        /* 모바일 입력창 간격 압축 */
        .stTextInput, .stNumberInput { margin-bottom: -15px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 세션 관리 (새로고침 유지 포함)
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = None

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# --- 📱 기기 감지 로직 (화면 너비 기준) ---
# Streamlit의 columns 비율을 이용해 모바일 여부를 간접적으로 판단하거나 레이아웃을 분리합니다.
is_mobile = False 

# 메인 레이아웃 구성
if not st.session_state.logged_in:
    # 로그인 화면은 PC/모바일 공용으로 중앙 배치
    _, login_col, _ = st.columns([1, 2, 1])
    with login_col:
        st.markdown(UI_TEXT["LOGIN_TITLE"])
        u_id = st.text_input("ID", key="l_id")
        u_pw = st.text_input("PW", type="password", key="l_pw")
        if st.button("LOGIN"):
            client = get_gspread_client()
            sh = client.open("작업_관리_데이터베이스")
            acc_sheet = sh.worksheet("Accounts")
            all_vals = acc_sheet.get_all_values()
            for row in all_vals[1:]:
                if len(row) >= 2 and str(row[0]) == u_id and str(row[1]) == u_pw:
                    st.session_state.logged_in = True
                    st.session_state.current_user = u_id
                    st.session_state.nickname = row[5] if len(row) > 5 and row[5].strip() else u_id
                    st.rerun()
            st.error("정보 불일치")
else:
    # --- 로그인 성공 후 레이아웃 분기 ---
    
    # PC 버전 사이드바 (화면이 넓을 때만 유용)
    with st.sidebar:
        st.success(f"✅ **{st.session_state.nickname}**님")
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        st.markdown("### 📢 서비스 링크")
        for item in ANNOUNCEMENTS:
            st.markdown(f"**[{item['text']}]({item['url']})**")

    # 메인 작업 영역
    st.title(f"🚀 {st.session_state.nickname} 작업등록")
    
    try:
        client = get_gspread_client()
        sh = client.open("작업_관리_데이터베이스")
        acc_sheet, hist_sheet = sh.worksheet("Accounts"), sh.worksheet("History")
        all_values = acc_sheet.get_all_values()
        user_row_idx, user_data = next(((i, r) for i, r in enumerate(all_values[1:], 2) if r[0] == st.session_state.current_user), (-1, []))

        if user_row_idx != -1:
            # 1. 잔여 수량 위젯 (모바일/PC 공통 가로 1줄 배치)
            st.write(UI_TEXT["SUB_TITLE_REMAIN"])
            m1, m2, m3, m4 = st.columns([1, 1, 1, 1.2])
            m1.metric("공감", f"{user_data[2]}")
            m2.metric("댓글", f"{user_data[3]}")
            m3.metric("스크랩", f"{user_data[4]}")
            m4.metric("접속ID", user_data[0])
            
            st.divider()
            
            # 2. 작업 입력 영역
            st.subheader(UI_TEXT["SUB_TITLE_INPUT"])
            
            # 헤더 라벨 (PC에서는 보이고 모바일에서는 캡션으로 작동)
            h_col = st.columns([2, 3, 0.8, 0.8, 0.8])
            labels = ["키워드", "URL (링크)", "공", "댓", "스"]
            for i, txt in enumerate(labels): h_col[i].caption(txt)

            rows_data = []
            for i in range(10):
                r_col = st.columns([2, 3, 0.8, 0.8, 0.8])
                kw = r_col[0].text_input(f"k_{i}", label_visibility="collapsed", key=f"kw_{i}", placeholder="키워드")
                url = r_col[1].text_input(f"u_{i}", label_visibility="collapsed", key=f"url_{i}", placeholder="URL")
                l = r_col[2].number_input(f"l_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"l_{i}")
                r = r_col[3].number_input(f"r_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"r_{i}")
                s = r_col[4].number_input(f"s_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"s_{i}")
                if kw and url: rows_data.append({"kw": kw, "link": url, "l": l, "r": r, "s": s})

            # 3. 등록 버튼 (CSS에 의해 모바일에서만 하단 고정)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(UI_TEXT["SUBMIT_BUTTON"], type="primary", key="submit_btn"):
                if not rows_data: st.warning("데이터를 입력하세요.")
                else:
                    with st.spinner("📦 처리 중..."):
                        # 데이터 업데이트 로직
                        acc_sheet.update_cell(user_row_idx, 3, int(user_data[2]) - sum(d['l'] for d in rows_data))
                        acc_sheet.update_cell(user_row_idx, 4, int(user_data[3]) - sum(d['r'] for d in rows_data))
                        acc_sheet.update_cell(user_row_idx, 5, int(user_data[4]) - sum(d['s'] for d in rows_data))
                        for d in rows_data:
                            hist_sheet.append_row([datetime.now().strftime('%m-%d %H:%M'), d['kw'], d['link'], d['l'], d['r'], d['s'], st.session_state.current_user])
                        st.success(UI_TEXT["SUCCESS_MSG"])
                        time.sleep(1)
                        st.rerun()

    except Exception: st.error("연동 실패")
