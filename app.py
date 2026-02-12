import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time
import re
import requests

# ==========================================
# 📐 [FONT_CONFIG] - 사용자님 최종 설정 (절대 고정)
# ==========================================
FONT_CONFIG = {
    "SIDEBAR_ID": "25px",      # 사이드바 사용자 ID 크기
    "SIDEBAR_LINKS": "25px",   # 사이드바 서비스 링크 글자 크기
    "LOGOUT_BTN": "20px",      # 로그아웃 버튼 글자 크기
    "MAIN_TITLE": "32px",      # 메인 제목 크기
    "CHARGE_BTN": "20px",      # 충전하기 버튼 글자 크기
    "REMAIN_TITLE": "25px",    # '실시간 잔여 수량' 제목 크기
    "METRIC_LABEL": "16px",    # 수량 항목 이름 크기
    "METRIC_VALUE": "35px",    # 잔여 수량 숫자 크기
    "REGISTER_TITLE": "22px",  # '작업 일괄 등록' 제목 크기
    "TABLE_HEADER": "25px",    # 입력창 상단 라벨 크기
    "TABLE_INPUT": "16px",     # 입력창 내부 글자 크기
    "SUBMIT_BTN": "45px"       # 🔥 작업넣기 버튼 글자 크기 (기존 40px에서 상향)
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

# --- 🎨 디자인 & 정렬 CSS (하단 버튼 고정 + 사이즈 대폭 확대) ---
st.markdown(f"""
    <style>
    .main .block-container {{ padding-top: 2.5rem !important; padding-bottom: 150px !important; }}
    
    /* 🚀 [변경] 하단 작업넣기 버튼 고정 및 사이즈 키움 */
    div.stButton > button:first-child[kind="primary"] {{
        position: fixed; 
        bottom: 30px; 
        left: 50%; 
        transform: translateX(-50%);
        width: 95% !important;     /* 화면 너비에 맞춰 확장 */
        max-width: 600px;           /* 최대 너비 키움 */
        height: 100px !important;    /* 버튼 높이 대폭 확대 */
        background-color: #FF4B4B !important; 
        border-radius: 20px !important;
        box-shadow: 0 8px 30px rgba(0,0,0,0.7); 
        z-index: 9999;
        border: 2px solid white !important;
    }}
    div.stButton > button:first-child[kind="primary"] p {{
        font-size: {FONT_CONFIG['SUBMIT_BTN']} !important; 
        font-weight: 900 !important;
    }}

    [data-testid="stFormSubmitButton"] + div {{ display: none !important; }}
    small {{ display: none !important; }}

    .sidebar-id {{ font-size: {FONT_CONFIG['SIDEBAR_ID']} !important; font-weight: bold; margin-bottom: 10px; color: #2ecc71; }}
    [data-testid="stSidebar"] {{ font-size: {FONT_CONFIG['SIDEBAR_LINKS']} !important; }}
    [data-testid="stSidebar"] button p {{ font-size: {FONT_CONFIG['LOGOUT_BTN']} !important; font-weight: bold !important; }}
    
    .header-wrapper {{ display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }}
    .main-title {{ font-size: {FONT_CONFIG['MAIN_TITLE']} !important; font-weight: bold; margin: 0; }}
    
    .charge-link {{
        display: inline-block; padding: 6px 14px; background-color: #FF4B4B;
        color: white !important; text-decoration: none; border-radius: 8px;
        font-weight: bold; font-size: {FONT_CONFIG['CHARGE_BTN']} !important;
    }}

    div[data-testid="stHorizontalBlock"] {{ align-items: stretch !important; }}
    [data-testid="stMetric"] {{
        background-color: #1e2129; border-radius: 10px; border: 1px solid #444; 
        padding: 15px 10px !important; min-height: 110px;
        display: flex; flex-direction: column; justify-content: center;
    }}
    [data-testid="stMetricLabel"] div {{ font-size: {FONT_CONFIG['METRIC_LABEL']} !important; }}
    [data-testid="stMetricValue"] div {{ font-size: {FONT_CONFIG['METRIC_VALUE']} !important; font-weight: 800 !important; color: #00ff00 !important; }}
    
    input {{ font-size: {FONT_CONFIG['TABLE_INPUT']} !important; }}
    .stCaption {{ font-size: {FONT_CONFIG['TABLE_HEADER']} !important; color: #aaa !important; }}
    </style>
    """, unsafe_allow_html=True)

# 📢 텔레그램 알림 함수 (사용자 정보 고정)
def send_telegram_msg(message):
    try:
        token = "8568445865:AAHkHpC164IDFKTyy-G76QdCZlWnpFdr6ZU"
        chat_id = "496784884"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message})
    except: pass

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, center_col, _ = st.columns([1, 1.3, 1])
    with center_col:
        with st.form("login_form"):
            st.markdown("### 🛡️ 로그인")
            u_id = st.text_input("ID", placeholder="아이디")
            u_pw = st.text_input("PW", type="password", placeholder="비밀번호")
            if st.form_submit_button("LOGIN"):
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
                except Exception as e: st.error(f"실패: {str(e)}")
else:
    with st.sidebar:
        st.markdown(f'<div class="sidebar-id">✅ {st.session_state.nickname}님</div>', unsafe_allow_html=True)
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        for item in ANNOUNCEMENTS:
            st.markdown(f"**[{item['text']}]({item['url']})**")

    charge_url = "https://kmong.com/inboxes?inbox_group_id=&partner_id="
    st.markdown(f"""
        <div class="header-wrapper">
            <span class="main-title">🚀 {st.session_state.nickname}님의 작업등록</span>
            <a href="{charge_url}" target="_blank" class="charge-link">💰 충전요청하기</a>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        client = get_gspread_client()
        sh = client.open("작업_관리_데이터베이스")
        acc_sheet, hist_sheet = sh.worksheet("Accounts"), sh.worksheet("History")
        all_values = acc_sheet.get_all_values()
        user_row_idx, user_data = next(((i, r) for i, r in enumerate(all_values[1:], 2) if r[0] == st.session_state.current_user), (-1, []))

        if user_row_idx != -1:
            st.markdown(f"📊 실시간 잔여 수량")
            m_cols = st.columns(4)
            m_cols[0].metric("공감", f"{user_data[2]}")
            m_cols[1].metric("댓글", f"{user_data[3]}")
            m_cols[2].metric("스크랩", f"{user_data[4]}")
            m_cols[3].metric("접속ID", user_data[0])
            st.divider()

            with st.form("work_registration_form", clear_on_submit=True):
                h_col = st.columns([2, 3, 1.2, 1.2, 1.2])
                for idx, label in enumerate(["키워드", "URL (필수)", "공감", "댓글", "스크랩"]): h_col[idx].caption(label)

                rows_inputs = []
                for i in range(10):
                    r_col = st.columns([2, 3, 1.2, 1.2, 1.2])
                    kw = r_col[0].text_input(f"k_{i}", label_visibility="collapsed")
                    u_raw = r_col[1].text_input(f"u_{i}", label_visibility="collapsed", placeholder="(링크 입력)")
                    l = r_col[2].number_input(f"l_{i}", min_value=0, step=1, label_visibility="collapsed")
                    r = r_col[3].number_input(f"r_{i}", min_value=0, step=1, label_visibility="collapsed")
                    s = r_col[4].number_input(f"s_{i}", min_value=0, step=1, label_visibility="collapsed")
                    rows_inputs.append({"kw": kw, "url": u_raw.replace(" ", "").strip(), "l": l, "r": r, "s": s})

                # 🚀 하단 고정 버튼 (사이즈 대폭 키움)
                submitted = st.form_submit_button("🔥 작업넣기", type="primary")

                if submitted:
                    rows_to_submit = [d for d in rows_inputs if d['url'] and (d['l']>0 or d['r']>0 or d['s']>0)]
                    if rows_to_submit:
                        try:
                            total_l, total_r, total_s = sum(d['l'] for d in rows_to_submit), sum(d['r'] for d in rows_to_submit), sum(d['s'] for d in rows_to_submit)
                            rem_l, rem_r, rem_s = int(user_data[2]), int(user_data[3]), int(user_data[4])

                            if rem_l >= total_l and rem_r >= total_r and rem_s >= total_s:
                                acc_sheet.update_cell(user_row_idx, 3, rem_l - total_l)
                                acc_sheet.update_cell(user_row_idx, 4, rem_r - total_r)
                                acc_sheet.update_cell(user_row_idx, 5, rem_s - total_s)

                                target_sh = client.open_by_key("1uqAHj4DoD1RhTsapAXmAB7aOrTQs6FhTIPV4YredoO8")
                                target_ws = target_sh.worksheet("작업")
                                url_col = target_ws.col_values(5)
                                last_idx = len(url_col) + 1
                                
                                for i, d in enumerate(rows_to_submit):
                                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    hist_sheet.append_row([now, d['kw'], d['url'], d['l'], d['r'], d['s'], st.session_state.current_user, st.session_state.nickname])
                                    target_ws.insert_row(["", "", now, d['kw'], d['url'], d['l'], d['r'], d['s'], st.session_state.nickname], index=last_idx + i, value_input_option='USER_ENTERED')
                                
                                send_telegram_msg(f"🚀 [{st.session_state.nickname}] 작업 등록!\n수량: 공{total_l} / 댓{total_r} / 스{total_s}")
                                
                                st.success("🎊 모든 등록 완료!")
                                time.sleep(1)
                                st.rerun()
                            else: st.error("❌ 잔여 수량 부족")
                        except Exception as ex: st.error(f"오류: {ex}")
    except Exception as e: st.error(f"동기화 오류: {e}")
