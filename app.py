import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time
import requests

# ==========================================
# 📐 [FONT_CONFIG] - 사용자님 최종 설정 (절대 고정)
# ==========================================
FONT_CONFIG = {
    "SIDEBAR_ID": "25px",      "SIDEBAR_LINKS": "20px",   "LOGOUT_TEXT": "15px",
    "MAIN_TITLE": "32px",      "CHARGE_BTN": "20px",      "REMAIN_TITLE": "30px",
    "METRIC_LABEL": "16px",    "METRIC_VALUE": "35px",    "REGISTER_TITLE": "22px",
    "TABLE_HEADER": "40px",    "TABLE_INPUT": "16px",     "SUBMIT_BTN": "22px"
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

if "form_id" not in st.session_state: st.session_state.form_id = 0

# --- 🎨 디자인 & 정렬 CSS (로그인 위치 수정 및 디자인 사수) ---
st.markdown(f"""
    <style>
    .main .block-container {{ padding-top: 2.5rem !important; padding-bottom: 150px !important; }}
    
    /* ✅ 1. 로그인 창 위치 정상화 (상단 정중앙 배치) */
    .login-wrapper {{
        display: flex; justify-content: center; align-items: flex-start;
        padding-top: 100px; min-height: 80vh;
    }}
    .login-box {{ width: 100%; max-width: 400px; }}

    /* 로그인 버튼 스타일 및 위치 (하단 고정 해제) */
    .stButton > button[kind="primaryFormSubmit"] {{
        width: 100% !important; height: 55px !important;
        background-color: #FF4B4B !important; color: white !important;
        font-size: 20px !important; font-weight: bold !important;
        border-radius: 12px !important; margin-top: 20px !important;
    }}

    /* 사이드바 & 메인 디자인 완벽 복구 */
    .sidebar-id {{ font-size: {FONT_CONFIG['SIDEBAR_ID']} !important; font-weight: bold !important; color: #2ecc71 !important; display: inline-block !important; }}
    .logout-link {{ font-size: {FONT_CONFIG['LOGOUT_TEXT']} !important; color: #888 !important; text-decoration: underline !important; margin-left: 10px !important; cursor: pointer !important; }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ font-size: {FONT_CONFIG['SIDEBAR_LINKS']} !important; }}
    .main-title {{ font-size: {FONT_CONFIG['MAIN_TITLE']} !important; font-weight: bold !important; }}
    [data-testid="stVerticalBlock"] .stCaption div p {{ font-size: {FONT_CONFIG['TABLE_HEADER']} !important; color: #ddd !important; font-weight: 900 !important; }}

    /* 메인 작업넣기 버튼 (50px 고정) */
    .main div.stButton > button {{
        position: fixed !important; bottom: 20px !important; left: 50% !important; transform: translateX(-50%) !important;
        width: 85% !important; max-width: 600px !important; height: 50px !important;
        background-color: #FF4B4B !important; color: white !important; border-radius: 12px !important;
        z-index: 999999 !important; border: 2px solid white !important;
    }}
    .main div.stButton > button p {{ font-size: {FONT_CONFIG['SUBMIT_BTN']} !important; font-weight: 900 !important; }}
    
    [data-testid="stMetricValue"] div {{ font-size: {FONT_CONFIG['METRIC_VALUE']} !important; font-weight: 800 !important; color: #00ff00 !important; }}
    small, .stDeployButton {{ display: none !important; }}
    </style>
    """, unsafe_allow_html=True)

def send_telegram_msg(message):
    try:
        token = "8568445865:AAHkHpC164IDFKTyy-G76QdCZlWnpFdr6ZU"
        chat_id = "496784884"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": message})
    except: pass

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    return gspread.authorize(Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes))

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if st.query_params.get("action") == "logout":
    st.session_state.logged_in = False; st.query_params.clear(); st.rerun()

# ✅ [복구] 로그인 창 위치 및 자동 완성 구조
if not st.session_state.logged_in:
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("### 🛡️ 로그인")
        with st.form("login_form", clear_on_submit=False):
            u_id = st.text_input("ID", placeholder="아이디", autocomplete="username")
            u_pw = st.text_input("PW", type="password", placeholder="비밀번호", autocomplete="current-password")
            if st.form_submit_button("LOGIN"):
                try:
                    client = get_gspread_client()
                    sh = client.open("작업_관리_데이터베이스")
                    acc_sheet = sh.worksheet("Accounts")
                    all_vals = acc_sheet.get_all_values()
                    for row in all_vals[1:]:
                        if str(row[0]) == u_id and str(row[1]) == u_pw:
                            st.session_state.logged_in, st.session_state.current_user = True, u_id
                            st.session_state.nickname = row[5] if len(row) > 5 and row[5].strip() else u_id
                            st.rerun()
                    st.error("정보 불일치")
                except Exception as e: st.error(f"실패: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    # --- 1. 사이드바 ---
    with st.sidebar:
        st.markdown(f'<div style="display: flex; align-items: center;"><span class="sidebar-id">✅ {st.session_state.nickname}님</span><a href="/?action=logout" target="_self" class="logout-link">LOGOUT</a></div>', unsafe_allow_html=True)
        st.divider()
        for item in ANNOUNCEMENTS: st.markdown(f"**[{item['text']}]({item['url']})**")

    # --- 2. 메인 헤더 & 수량 지표 (4칸 완벽 복구) ---
    h_col1, h_col2 = st.columns([4, 1.2])
    with h_col1: st.markdown(f'<div class="main-title">🚀 {st.session_state.nickname}님의 작업등록</div>', unsafe_allow_html=True)
    with h_col2: st.markdown(f'<a href="https://kmong.com/inboxes" target="_blank" style="display:inline-block; background-color:#FF4B4B; color:white; padding:10px 15px; border-radius:10px; text-decoration:none; font-weight:bold; font-size:{FONT_CONFIG["CHARGE_BTN"]}; text-align:center; width:100%;">💰 충전요청하기</a>', unsafe_allow_html=True)
    
    try:
        client = get_gspread_client()
        sh = client.open("작업_관리_데이터베이스")
        acc_sheet, hist_sheet = sh.worksheet("Accounts"), sh.worksheet("History")
        all_vals = acc_sheet.get_all_values()
        user_row_idx, user_data = next(((i, r) for i, r in enumerate(all_vals[1:], 2) if r[0] == st.session_state.current_user), (-1, []))

        if user_row_idx != -1:
            st.markdown(f'<div class="remain-title">📊 실시간 잔여 수량</div>', unsafe_allow_html=True)
            m_cols = st.columns(4)
            m_cols[0].metric("공감", f"{user_data[2]}"); m_cols[1].metric("댓글", f"{user_data[3]}")
            m_cols[2].metric("스크랩", f"{user_data[4]}"); m_cols[3].metric("접속ID", user_data[0])
            st.divider()

            # --- 3. 작업 일괄 등록 표 ---
            st.markdown(f'<div style="font-size:{FONT_CONFIG["REGISTER_TITLE"]}; font-weight:bold; margin-bottom:10px;">📝 작업 일괄 등록</div>', unsafe_allow_html=True)
            h_col = st.columns([2, 3, 1.2, 1.2, 1.2])
            for idx, label in enumerate(["키워드(선택)", "URL (필수)", "공감", "댓글", "스크랩"]): h_col[idx].caption(label)

            rows_inputs = []
            for i in range(10):
                r_col = st.columns([2, 3, 1.2, 1.2, 1.2])
                kw = r_col[0].text_input(f"k_{i}", key=f"k_{i}_{st.session_state.form_id}", label_visibility="collapsed")
                u_raw = r_col[1].text_input(f"u_{i}", key=f"u_{i}_{st.session_state.form_id}", label_visibility="collapsed", placeholder="(링크 입력)")
                l = r_col[2].number_input(f"l_{i}", key=f"l_{i}_{st.session_state.form_id}", min_value=0, step=1, label_visibility="collapsed")
                r = r_col[3].number_input(f"r_{i}", key=f"r_{i}_{st.session_state.form_id}", min_value=0, step=1, label_visibility="collapsed")
                s = r_col[4].number_input(f"s_{i}", key=f"s_{i}_{st.session_state.form_id}", min_value=0, step=1, label_visibility="collapsed")
                rows_inputs.append({"kw": kw, "url": u_raw.replace(" ", "").strip(), "l": l, "r": r, "s": s})

            # 🔥 [요청 해결] 시트 출력 위치 정상화 및 모든 기능 통합
            if st.button("🔥 작업넣기", type="primary"):
                valid_rows = [d for d in rows_inputs if d['url'] and (d['l']>0 or d['r']>0 or d['s']>0)]
                if valid_rows:
                    try:
                        total_l, total_r, total_s = sum(d['l'] for d in valid_rows), sum(d['r'] for d in valid_rows), sum(d['s'] for d in valid_rows)
                        rem_l, rem_r, rem_s = int(user_data[2]), int(user_data[3]), int(user_data[4])
                        if rem_l >= total_l and rem_r >= total_r and rem_s >= total_s:
                            # 수량 차감
                            acc_sheet.update_cell(user_row_idx, 3, rem_l - total_l)
                            acc_sheet.update_cell(user_row_idx, 4, rem_r - total_r)
                            acc_sheet.update_cell(user_row_idx, 5, rem_s - total_s)

                            # ✅ 2번째 시트("작업") 출력 위치 최적화
                            target_sh = client.open_by_key("1uqAHj4DoD1RhTsapAXmAB7aOrTQs6FhTIPV4YredoO8")
                            target_ws = target_sh.worksheet("작업")
                            
                            # ⚠️ [핵심] 기존의 append_row 대신 빈 행을 찾아 정확히 삽입 (image_1c309f.png 문제 해결)
                            all_data = target_ws.get_all_values()
                            # 5번째 열(URL)이 비어있는 첫 번째 행 번호 찾기 (기본 데이터가 있는 4행 이후부터)
                            start_row = next((i + 1 for i, row in enumerate(all_data) if i >= 3 and (len(row) < 5 or not row[4])), len(all_data) + 1)
                            
                            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            urls_for_msg = []
                            for idx, d in enumerate(valid_rows):
                                # 1번째 시트 기록
                                hist_sheet.append_row([now, d['kw'], d['url'], d['l'], d['r'], d['s'], st.session_state.current_user, st.session_state.nickname])
                                # 2번째 시트 정확한 위치에 데이터 삽입
                                target_ws.update(f"C{start_row+idx}:I{start_row+idx}", [[now, d['kw'], d['url'], d['l'], d['r'], d['s'], st.session_state.nickname]])
                                urls_for_msg.append(f"- {d['url']}")

                            send_telegram_msg(f"🔔 [신규작업]\n{st.session_state.nickname}\n\n" + "\n".join(urls_for_msg) + f"\n\n공{total_l} / 댓{total_r} / 스{total_s}")
                            st.session_state.form_id += 1 
                            st.success("🎊 작업 등록 완료!"); time.sleep(1.2); st.rerun()
                        else: st.error("❌ 잔여 수량 부족!")
                    except Exception as ex: st.error(f"오류: {ex}")
    except Exception as e: st.error(f"동기화 오류: {e}")
