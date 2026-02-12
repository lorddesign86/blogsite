import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time
import re

# ==========================================
# 📐 [글자 크기 통합 설정] - 숫자만 수정하세요!
# ==========================================
폰트_설정 = {
    "사이드바_사용자ID": "25px",   # 왼쪽 '바둥이님' 글자 크기
    "사이드바_메뉴글자": "16px",   # 왼쪽 '서비스 링크' 등 메뉴 크기
    "로그아웃_버튼": "16px",       # 왼쪽 'LOGOUT' 버튼 글자 크기
    "메인_타이틀": "32px",         # 상단 '🚀 바둥이 작업등록' 크기
    "충전하기_버튼": "16px",       # 타이틀 옆 '💰 충전하기' 버튼 크기
    "실시간수량_제목": "22px",     # '📊 실시간 잔여 수량' 글자 크기
    "수량항목_이름": "16px",       # '공감', '댓글', '스크랩' 글자 크기
    "수량_숫자": "28px",           # 잔여 수량 숫자 크기
    "작업등록_제목": "22px",       # '📝 작업 일괄 등록' 글자 크기
    "입력창_상단라벨": "15px",     # 입력칸 위 '키워드', 'URL' 글자 크기
    "입력창_내부글자": "16px",     # 실제 타자 치는 글자 크기
    "작업넣기_버튼": "24px"        # 하단 '🔥 작업넣기' 대형 버튼 크기
}

# --- 기본 문구 설정 ---
UI_TEXT = {
    "SUBMIT_BUTTON": "🔥 작업넣기",
    "SUCCESS_MSG": "🎊 모든 작업이 정상 등록되었습니다."
}

ANNOUNCEMENTS = [
    {"text": "👉 파우쓰 서비스 전체보기", "url": "https://kmong.com/@파우쓰"},
    {"text": "📢 스댓공 월 자동서비스", "url": "https://kmong.com/gig/645544"},
    {"text": "📢 스댓공 개별서비스", "url": "https://kmong.com/gig/445340"},
    {"text": "📢 방문자 서비스 보러가", "url": "https://caring-kayak-cd7.notion.site/27707671d021808a9567edb8ad065b28?source=copy_link"},
    {"text": "📢 이웃 서비스 100~700명", "url": "https://kmong.com/gig/668226"},
    {"text": "📢 최적화 블로그리스트 추출프로그램", "url": "https://kmong.com/gig/725815"},
]

st.set_page_config(page_title="파우쓰", layout="wide")

# --- 🎨 디자인 CSS (모든 영역 텍스트 강제 제어) ---
# f-string 에러 방지를 위해 {{ }}를 사용하여 작성했습니다.
st.markdown(f"""
    <style>
    .main .block-container {{ padding-top: 2.5rem !important; }}
    
    /* 1. 사이드바 텍스트 및 버튼 */
    [data-testid="stSidebar"] {{ font-size: {폰트_설정['사이드바_메뉴글자']} !important; }}
    .sidebar-id {{ font-size: {폰트_설정['사이드바_사용자ID']} !important; font-weight: bold; margin-bottom: 10px; }}
    [data-testid="stSidebar"] button p {{ font-size: {폰트_설정['로그아웃_버튼']} !important; font-weight: bold !important; }}

    /* 2. 메인 타이틀 및 충전하기 버튼 */
    .header-wrapper {{ display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }}
    .main-title {{ font-size: {폰트_설정['메인_타이틀']} !important; font-weight: bold; margin: 0; }}
    .charge-link {{
        display: inline-block; padding: 6px 14px; background-color: #FF4B4B;
        color: white !important; text-decoration: none; border-radius: 8px;
        font-weight: bold; font-size: {폰트_설정['충전하기_버튼']} !important;
    }}

    /* 3. 잔여 수량 섹션 */
    .section-title {{ font-size: {폰트_설정['실시간수량_제목']} !important; font-weight: bold; margin-bottom: 15px; }}
    [data-testid="stMetricLabel"] div {{ font-size: {폰트_설정['수량항목_이름']} !important; }}
    [data-testid="stMetricValue"] div {{ 
        font-size: {폰트_설정['수량_숫자']} !important; 
        font-weight: 800 !important; color: #00ff00 !important; 
    }}
    [data-testid="stMetric"] {{ background-color: #1e2129; border-radius: 10px; border: 1px solid #444; }}

    /* 4. 작업 등록 섹션 및 입력창 */
    .register-title {{ font-size: {폰트_설정['작업등록_제목']} !important; font-weight: bold; margin-top: 25px; }}
    .stCaption {{ font-size: {폰트_설정['입력창_상단라벨']} !important; color: #aaa !important; }}
    input {{ font-size: {폰트_설정['입력창_내부글자']} !important; }}

    /* 5. 🔥 작업넣기 버튼 대형화 */
    div.stButton > button:first-child[kind="primary"] {{
        width: 250px !important;
        height: 70px !important;
        background-color: #FF4B4B !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        margin-top: 20px;
    }}
    div.stButton > button:first-child[kind="primary"] p {{
        font-size: {폰트_설정['작업넣기_버튼']} !important;
        font-weight: bold !important;
    }}

    @media (max-width: 768px) {{
        div.stButton > button:first-child[kind="primary"] {{
            position: fixed; bottom: 10px; left: 5%; right: 5%; width: 90% !important; z-index: 999;
            height: 4rem !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

# 🔗 네이버 블로그 링크 검증 함수
def is_valid_naver_link(url):
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
    _, login_col, _ = st.columns([1, 2, 1])
    with login_col:
        st.markdown("### 🛡️ 파우쓰 관리자 로그인")
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
                st.error("아이디 또는 비밀번호가 틀립니다.")
            except Exception: st.error("연결 오류")
else:
    # 사이드바 레이아웃
    with st.sidebar:
        st.markdown(f'<div class="sidebar-id">✅ {st.session_state.nickname}님</div>', unsafe_allow_html=True)
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        st.markdown("### 📢 서비스 링크")
        for item in ANNOUNCEMENTS:
            st.markdown(f"**[{item['text']}]({item['url']})**")

    # 메인 헤더
    charge_url = "https://kmong.com/inboxes?inbox_group_id=&partner_id="
    st.markdown(f"""
        <div class="header-wrapper">
            <span class="main-title">🚀 {st.session_state.nickname} 작업등록</span>
            <a href="{charge_url}" target="_blank" class="charge-link">💰 충전하기</a>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        client = get_gspread_client()
        sh = client.open("작업_관리_데이터베이스")
        acc_sheet, hist_sheet = sh.worksheet("Accounts"), sh.worksheet("History")
        all_values = acc_sheet.get_all_values()
        user_row_idx, user_data = next(((i, r) for i, r in enumerate(all_values[1:], 2) if r[0] == st.session_state.current_user), (-1, []))

        if user_row_idx != -1:
            st.markdown(f'<div class="section-title">{UI_TEXT["SUB_TITLE_REMAIN"]}</div>', unsafe_allow_html=True)
            m1, m2, m3, m4 = st.columns([1, 1, 1, 1.2])
            m1.metric("공감", f"{user_data[2]}개")
            m2.metric("댓글", f"{user_data[3]}개")
            m3.metric("스크랩", f"{user_data[4]}개")
            m4.metric("접속ID", user_data[0])
            st.divider()
            
            st.markdown(f'<div class="register-title">{UI_TEXT["SUB_TITLE_INPUT"]}</div>', unsafe_allow_html=True)
            h_col = st.columns([2, 3, 0.8, 0.8, 0.8])
            for i, txt in enumerate(["키워드", "URL (필수)", "공", "댓", "스"]): h_col[i].caption(txt)

            rows_data, link_errors = [], []
            for i in range(10):
                r_col = st.columns([2, 3, 0.8, 0.8, 0.8])
                kw = r_col[0].text_input(f"k_{i}", label_visibility="collapsed", key=f"kw_{i}", placeholder="(키워드)")
                url = r_col[1].text_input(f"u_{i}", label_visibility="collapsed", key=f"url_{i}", placeholder="(링크 필수)")
                l = r_col[2].number_input(f"l_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"l_{i}")
                r = r_col[3].number_input(f"r_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"r_{i}")
                s = r_col[4].number_input(f"s_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"s_{i}")
                
                if url.strip():
                    if not is_valid_naver_link(url): link_errors.append(f"{i+1}번")
                    elif l > 0 or r > 0 or s > 0:
                        rows_data.append({"kw": kw if kw else "", "link": url.strip(), "l": l, "r": r, "s": s})

            if st.button(UI_TEXT["SUBMIT_BUTTON"], type="primary", key="submit_btn"):
                if link_errors:
                    st.error(f"⚠️ {', '.join(link_errors)} 링크 오류: 네이버 블로그 형식이 아닙니다.")
                elif not rows_data:
                    st.warning("⚠️ 등록할 링크와 작업 수량을 입력하세요.")
                else:
                    with st.spinner("📦 처리 중..."):
                        t_l, t_r, t_s = sum(d['l'] for d in rows_data), sum(d['r'] for d in rows_data), sum(d['s'] for d in rows_data)
                        if int(user_data[2]) >= t_l and int(user_data[3]) >= t_r and int(user_data[4]) >= t_s:
                            acc_sheet.update_cell(user_row_idx, 3, int(user_data[2]) - t_l)
                            acc_sheet.update_cell(user_row_idx, 4, int(user_data[3]) - t_r)
                            acc_sheet.update_cell(user_row_idx, 5, int(user_data[4]) - t_s)
                            for d in rows_data:
                                hist_sheet.append_row([datetime.now().strftime('%m-%d %H:%M'), d['kw'], d['link'], d['l'], d['r'], d['s'], st.session_state.current_user])
                            st.success(UI_TEXT["SUCCESS_MSG"])
                            time.sleep(1)
                            st.rerun()
                        else: st.error("❌ 잔여 수량이 부족합니다.")

    except Exception: st.error("연동 실패")
