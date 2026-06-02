import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import uuid

from pdf_generator import generate_pdf
from email_sender import send_application_email, get_default_email
from db_handler import (
    init_db, migrate_excel_to_db, migrate_reference_data_to_db,
    append_to_master_db as append_to_master,
    get_master_data_db as get_master_data,
    get_monthly_summary_db as get_monthly_summary,
    get_all_monthly_summary_db as get_all_monthly_summary,
    add_monthly_summary_site_db as add_monthly_summary_site,
    sync_sites_to_monthly_summary_db as sync_sites_to_monthly_summary,
    delete_monthly_summary_site_db as delete_monthly_summary_site,
    update_monthly_summary_budget_db as update_monthly_summary_budget,
    delete_application_db as delete_application,
    save_pdf_to_db, get_pdf_from_db, migrate_existing_pdfs_to_db
)
from reference_data import (
    get_sites, get_applicants, add_site, update_site, delete_site,
    add_applicant, update_applicant, delete_applicant, get_site_by_name, get_applicant_by_name,
    add_email_recipient, update_email_recipient, delete_email_recipient, get_email_recipients,
    get_supply_products, add_supply_product, update_supply_product, delete_supply_product, get_supply_product_by_name,
    get_uniform_products, add_uniform_product, update_uniform_product, delete_uniform_product, get_uniform_product_by_name
)
from draft_manager import save_draft, get_draft, delete_draft, get_draft_list, update_draft, migrate_json_drafts_to_db

@st.dialog("삭제 확인")
def confirm_delete_dialog(delete_type, item_id, item_name, extra_info=None):
    """팝업 형태의 삭제 확인 다이얼로그"""
    st.warning(f"⚠️ 정말 '{item_name}'을(를) 삭제하시겠습니까?")
    st.caption("이 작업은 취소할 수 없습니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 삭제 확인", type="primary", use_container_width=True):
            st.session_state.pending_delete = {
                'type': delete_type,
                'id': item_id,
                'name': item_name,
                'extra': extra_info,
                'confirmed': True
            }
            st.rerun()
    with col2:
        if st.button("❌ 취소", use_container_width=True):
            st.rerun()

st.set_page_config(
    page_title="경비용품 및 피복 신청 관리 시스템",
    page_icon="📋",
    layout="wide"
)

st.markdown("""
<style>
    /* 메인 색상 및 폰트 변수 설정 */
    :root {
        --primary: #0F172A;      /* Slate 900 (Navy) */
        --primary-light: #1E293B; /* Slate 800 */
        --accent: #F59E0B;       /* Amber 500 (Orange point) */
        --accent-hover: #D97706; /* Amber 600 */
        --bg-color: #F8FAFC;     /* Slate 50 (Very light gray) */
        --surface: #FFFFFF;
        --border: #E2E8F0;       /* Slate 200 */
        --text-main: #334155;    /* Slate 700 */
        --text-light: #64748B;   /* Slate 500 */
        --radius: 6px;           /* 약간 각진 모던한 느낌 */
        --font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif;
    }

    /* 전체 폰트 및 텍스트 색상 */
    html, body, [class*="css"] {
        font-family: var(--font-family) !important;
        color: var(--text-main);
    }

    /* 앱 전체 배경색 */
    .stApp {
        background-color: var(--bg-color);
    }

    /* 메인 컨텐츠 패딩 조절 (밀도 높이기) */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px !important;
    }

    /* 헤더 스타일링 */
    .main-header {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: var(--primary) !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem !important;
        padding-bottom: 0.75rem !important;
        border-bottom: 3px solid var(--primary);
    }
    
    .sub-header {
        font-size: 1rem;
        color: var(--text-light);
        margin-bottom: 1.5rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .sub-header::before {
        content: "";
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: var(--accent);
        border-radius: 50%;
    }

    /* 서브헤더 (st.subheader) */
    h3 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: var(--primary) !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border);
    }

    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: var(--surface);
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] [data-testid="stImage"] {
        padding: 1rem 0;
        margin-bottom: 1rem;
        border-bottom: 1px solid var(--border);
    }
    
    /* 사이드바 라디오 버튼 (메뉴) 스타일링 */
    [data-testid="stSidebar"] .stRadio > div[role="radiogroup"] {
        gap: 4px;
    }
    [data-testid="stSidebar"] .stRadio label {
        padding: 10px 12px;
        border-radius: var(--radius);
        transition: all 0.2s ease;
        cursor: pointer;
        background-color: transparent;
        border: 1px solid transparent;
        color: var(--text-main) !important;
        font-weight: 500;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: var(--bg-color);
    }
    [data-testid="stSidebar"] .stRadio label[data-checked="true"] {
        background-color: var(--primary);
        color: white !important;
    }
    [data-testid="stSidebar"] .stRadio label[data-checked="true"] p {
        color: white !important;
        font-weight: 600;
    }

    /* 버튼 기본 스타일 */
    .stButton > button {
        border-radius: var(--radius) !important;
        font-weight: 600 !important;
        border: 1px solid var(--border) !important;
        background-color: var(--surface) !important;
        color: var(--text-main) !important;
        transition: all 0.2s ease-in-out !important;
        padding: 0.5rem 1rem !important;
    }
    .stButton > button:hover {
        border-color: var(--text-light) !important;
        color: var(--primary) !important;
        background-color: var(--bg-color) !important;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Primary 버튼 (강조) */
    .stButton > button[kind="primary"] {
        background-color: var(--primary) !important;
        border-color: var(--primary) !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: var(--primary-light) !important;
        border-color: var(--primary-light) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    /* 입력 폼 (Input) 스타일 */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stDateInput > div > div > input {
        border-radius: var(--radius) !important;
        border: 1px solid var(--border) !important;
        padding: 0.5rem 0.75rem !important;
        font-size: 0.95rem !important;
        background-color: var(--surface);
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    
    /* 선택박스(Select) 래퍼 스타일 (padding 제거하여 잘림 방지) */
    .stSelectbox > div > div {
        border-radius: var(--radius) !important;
        border: 1px solid var(--border) !important;
        background-color: var(--surface);
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    
    /* 포커스 효과 */
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within,
    .stTextArea > div > div > textarea:focus,
    .stDateInput > div > div > input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
        outline: none !important;
    }
    
    /* 레이블 스타일 */
    .stTextInput label, .stSelectbox label, .stNumberInput label, .stDateInput label {
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        color: var(--text-main) !important;
        margin-bottom: 0.25rem !important;
    }

    /* Expander (카드 형태) 스타일 */
    .stExpander {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        background-color: var(--surface) !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem !important;
    }
    .stExpander summary {
        padding: 1rem !important;
        font-weight: 600 !important;
        color: var(--primary) !important;
    }
    .stExpander summary:hover {
        background-color: var(--bg-color) !important;
    }

    /* 알림창 (Info, Warning, Error) */
    .stAlert {
        border-radius: var(--radius) !important;
        padding: 1rem !important;
        border-left-width: 4px !important;
        border-left-style: solid !important;
    }
    [data-testid="stAlert"][data-baseweb="notification"]:has(div:contains("ℹ️")) {
        background-color: #EFF6FF !important; /* Blue 50 */
        border-left-color: #3B82F6 !important; /* Blue 500 */
        color: #1E3A8A !important; /* Blue 900 */
    }

    /* 데이터프레임 */
    .stDataFrame {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        overflow: hidden;
    }
    
    /* 탭(Tabs) 스타일 개선 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        font-weight: 600;
        color: var(--text-light);
        border: none;
        border-bottom: 2px solid transparent;
        background-color: transparent;
        border-radius: 0;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--primary);
    }
    .stTabs [aria-selected="true"] {
        color: var(--primary);
        border-bottom: 2px solid var(--primary);
    }

    /* 메트릭(Metric) 스타일 - 조회 화면용 */
    [data-testid="stMetric"] {
        background-color: var(--surface);
        padding: 1.25rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-light);
        font-weight: 600;
        font-size: 0.875rem;
        margin-bottom: 0.5rem;
    }
    [data-testid="stMetricValue"] {
        color: var(--primary);
        font-weight: 700;
        font-size: 1.875rem;
    }
    
    /* 구분선 */
    hr {
        margin: 2rem 0;
        border-color: var(--border);
    }
    
    /* 커스텀 유틸리티 클래스 */
    .card-container {
        background-color: var(--surface);
        padding: 1.5rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
    }
    
    /* 품목 리스트 아이템 컴팩트화 */
    .item-row {
        background-color: var(--surface);
        padding: 1rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        margin-bottom: 0.5rem;
    }

    /* 성공/경고/에러 메시지 */
    .stSuccess {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    .stWarning {
        background-color: #fff3cd;
        border-left: 4px solid #f5a623;
    }
    .stError {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

if 'pdf_generated' not in st.session_state:
    st.session_state.pdf_generated = False
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = None
if 'form_data' not in st.session_state:
    st.session_state.form_data = None
if 'loaded_draft_id' not in st.session_state:
    st.session_state.loaded_draft_id = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'draft_metadata' not in st.session_state:
    st.session_state.draft_metadata = None
if 'form_version' not in st.session_state:
    st.session_state.form_version = 0
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "신청서 작성"
if 'selected_company' not in st.session_state:
    st.session_state.selected_company = "미래"
if 'selected_app_type' not in st.session_state:
    st.session_state.selected_app_type = "경비물품"
if 'db_initialized' not in st.session_state:
    init_db()
    migrate_excel_to_db()
    migrate_reference_data_to_db()
    migrated_count = migrate_existing_pdfs_to_db()
    if migrated_count > 0:
        print(f"기존 PDF {migrated_count}개 DB로 마이그레이션 완료")
    migrate_json_drafts_to_db()
    st.session_state.db_initialized = True

menu_options = ["신청서 작성", "신청내역조회", "월별 집계", "관리자 모드"]
company_options = ["미래", "다원"]
app_type_options = ["경비물품", "피복"]

def _new_item_id():
    return str(uuid.uuid4())[:8]

def clear_form_state():
    st.session_state.loaded_draft_id = None
    st.session_state.pdf_generated = False
    st.session_state.pdf_path = None
    st.session_state.form_data = None
    st.session_state.draft_metadata = None
    st.session_state.form_version = st.session_state.get('form_version', 0) + 1
    for key in list(st.session_state.keys()):
        if key.startswith(('sup_select_', 'sup_name_', 'sup_spec_', 'sup_qty_', 'del_sup_',
                           'job_', 'pos_', 'worker_', 'top_', 'bot_', 'hat_', 'shoe_', 'del_',
                           'unif_select_', 'unif_qty_', 'prod_', 'add_prod_', 'del_prod_',
                           'manual_site', 'manual_applicant',
                           'site_select_', 'applicant_select_')):
            del st.session_state[key]
    for key in ('supplies_items', 'uniform_items'):
        if key in st.session_state:
            del st.session_state[key]

if 'pending_menu' in st.session_state:
    st.session_state.menu_radio = st.session_state.pending_menu
    del st.session_state.pending_menu
if 'pending_company' in st.session_state:
    st.session_state.company_select = st.session_state.pending_company
    del st.session_state.pending_company
if 'pending_app_type' in st.session_state:
    st.session_state.app_type_select = st.session_state.pending_app_type
    del st.session_state.pending_app_type

with st.sidebar:
    st.markdown('<div style="padding: 5px 15px 10px 15px;">', unsafe_allow_html=True)
    st.image("attached_assets/미래ABM_LOGO_1768364713952.png", width=120)
    st.markdown('</div>', unsafe_allow_html=True)
    st.header("설정")
    
    company = st.selectbox(
        "법인명",
        options=company_options,
        index=company_options.index(st.session_state.get('company_select', '미래')),
        key="company_select"
    )
    
    app_type = st.selectbox(
        "신청 유형",
        options=app_type_options,
        index=app_type_options.index(st.session_state.get('app_type_select', '경비물품')),
        key="app_type_select"
    )
    
    st.divider()
    
    menu = st.radio(
        "메뉴",
        options=menu_options,
        index=menu_options.index(st.session_state.get('menu_radio', '신청서 작성')),
        key="menu_radio"
    )

if 'previous_menu' not in st.session_state:
    st.session_state.previous_menu = menu
if 'previous_company' not in st.session_state:
    st.session_state.previous_company = company
if 'previous_app_type' not in st.session_state:
    st.session_state.previous_app_type = app_type

if st.session_state.previous_menu != menu:
    st.session_state.pending_delete = None
    if menu == "신청서 작성" and not st.session_state.get('reapply_pending'):
        clear_form_state()
    st.session_state.previous_menu = menu

if st.session_state.previous_company != company or st.session_state.previous_app_type != app_type:
    if not st.session_state.get('reapply_pending'):
        clear_form_state()
    st.session_state.previous_company = company
    st.session_state.previous_app_type = app_type

if st.session_state.get('reapply_pending'):
    del st.session_state['reapply_pending']

if 'pending_delete' not in st.session_state:
    st.session_state.pending_delete = None

if st.session_state.pending_delete and st.session_state.pending_delete.get('confirmed'):
    pd = st.session_state.pending_delete
    delete_type = pd['type']
    success = False
    msg = ""
    
    if delete_type == 'draft':
        delete_draft(pd['id'])
        success, msg = True, "임시저장이 삭제되었습니다."
    elif delete_type == 'application':
        extra = pd.get('extra', {})
        success, msg = delete_application(
            extra.get('date'),
            extra.get('site'),
            extra.get('applicant'),
            extra.get('app_type'),
            extra.get('company')
        )
    elif delete_type == 'site':
        success, msg = delete_site(pd['id'])
    elif delete_type == 'applicant':
        success, msg = delete_applicant(pd['id'])
    elif delete_type == 'email':
        success, msg = delete_email_recipient(pd['id'])
    elif delete_type == 'supply':
        success, msg = delete_supply_product(pd['id'])
    elif delete_type == 'uniform':
        success, msg = delete_uniform_product(pd['id'])
    elif delete_type == 'summary_site':
        extra = pd.get('extra', {})
        success, msg = delete_monthly_summary_site(extra.get('site'), extra.get('company'))
    
    st.session_state.pending_delete = None
    if success:
        st.success(msg)
    else:
        st.error(msg)

st.markdown('<p class="main-header">경비용품 및 피복 신청 관리 시스템</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-header">현재 선택: {company} ABM / {app_type} 신청</p>', unsafe_allow_html=True)

if menu == "신청서 작성":
    drafts = get_draft_list()
    if drafts:
        with st.expander("📂 임시저장 목록", expanded=False):
            for draft in drafts:
                col_d1, col_d2, col_d3 = st.columns([3, 1, 1])
                with col_d1:
                    st.write(f"**{draft['site_name']}** - {draft['company']} {draft['app_type']} ({draft['item_count']}개 품목)")
                    st.caption(f"저장일시: {draft['saved_at']}")
                with col_d2:
                    if st.button("불러오기", key=f"load_{draft['id']}"):
                        loaded = get_draft(draft['id'])
                        if loaded:
                            st.session_state.loaded_draft_id = draft['id']
                            st.session_state.form_version = st.session_state.get('form_version', 0) + 1
                            if loaded.get('app_type') == '경비물품':
                                st.session_state.supplies_items = loaded.get('items', [])
                            else:
                                loaded_items = loaded.get('items', [])
                                converted_items = []
                                for item in loaded_items:
                                    if '품목1' in item:
                                        if 'product_count' not in item:
                                            item['product_count'] = 3
                                        converted_items.append(item)
                                    else:
                                        converted_items.append({
                                            '업종': item.get('업종', '경비직'),
                                            '직책': item.get('직책', '경비원'),
                                            '근무자': item.get('근무자', ''),
                                            '상의': item.get('상의', '100'),
                                            '하의': item.get('하의', '32'),
                                            '모자': item.get('모자', '중'),
                                            '품목1': item.get('품목', ''),
                                            '수량1': item.get('수량', 1),
                                            '품목2': '',
                                            '수량2': 0,
                                            '품목3': '',
                                            '수량3': 0,
                                            'product_count': 3
                                        })
                                st.session_state.uniform_items = converted_items
                            st.session_state.draft_metadata = {
                                'site_name': loaded.get('site_name', ''),
                                'applicant': loaded.get('applicant', ''),
                                'applicant_contact': loaded.get('applicant_contact', ''),
                                'address': loaded.get('address', ''),
                                'contact': loaded.get('contact', ''),
                                'remarks': loaded.get('remarks', ''),
                                'application_date': loaded.get('application_date', '')
                            }
                            st.rerun()
                with col_d3:
                    if st.button("삭제", key=f"del_draft_{draft['id']}"):
                        confirm_delete_dialog('draft', draft['id'], draft.get('site_name', '임시저장'))
    
    if st.session_state.get('clear_form_pending'):
        clear_form_state()
        del st.session_state.clear_form_pending

    draft_meta = st.session_state.draft_metadata
    if draft_meta:
        st.info(f"📂 임시저장 데이터를 불러왔습니다: {draft_meta.get('site_name', '')}")
    
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.subheader("기본 정보 입력")
    
    sites = get_sites()
    applicants_list = get_applicants()
    
    filtered_sites = [s for s in sites if s.get("company", "미래") == company]
    site_names = ["직접 입력"] + [s["name"] for s in filtered_sites]
    applicant_names = ["직접 입력"] + [a["name"] for a in applicants_list]
    
    site_info = None
    applicant_info = None
    
    col1, col2 = st.columns(2)
    
    with col1:
        if draft_meta and draft_meta.get('application_date'):
            try:
                default_date = datetime.strptime(draft_meta['application_date'], '%Y-%m-%d').date()
            except:
                default_date = date.today()
        else:
            default_date = date.today()
        
        application_date = st.date_input(
            "신청일",
            value=default_date,
            format="YYYY-MM-DD"
        )
        
        draft_site_name = draft_meta.get('site_name', '') if draft_meta else ''
        if draft_site_name and draft_site_name in site_names:
            site_index = site_names.index(draft_site_name)
        elif draft_site_name:
            site_index = 0
        else:
            site_index = 0
        
        fv = st.session_state.form_version
        selected_site = st.selectbox(
            "현장명 선택",
            options=site_names,
            index=site_index,
            help="등록된 현장을 선택하거나 '직접 입력'을 선택하세요",
            key=f"site_select_{fv}"
        )
        if selected_site == "직접 입력":
            default_site_value = draft_site_name if draft_meta else ''
            site_name = st.text_input(
                "현장명",
                value=default_site_value,
                placeholder="예: 고산센트레빌, 성남메트로칸",
                key=f"manual_site_{fv}"
            )
        else:
            site_name = selected_site
            site_info = get_site_by_name(selected_site)
        
        draft_applicant = draft_meta.get('applicant', '') if draft_meta else ''
        if draft_applicant and draft_applicant in applicant_names:
            applicant_index = applicant_names.index(draft_applicant)
        elif draft_applicant:
            applicant_index = 0
        else:
            applicant_index = 0
        
        selected_applicant = st.selectbox(
            "신청자 선택",
            options=applicant_names,
            index=applicant_index,
            help="등록된 신청자를 선택하거나 '직접 입력'을 선택하세요",
            key=f"applicant_select_{fv}"
        )
        
        if selected_applicant == "직접 입력":
            default_applicant_value = draft_applicant if draft_meta else ''
            applicant = st.text_input(
                "신청자",
                value=default_applicant_value,
                placeholder="예: 김솔휘 대리",
                key=f"manual_applicant_{fv}"
            )
        else:
            applicant = selected_applicant
            applicant_info = get_applicant_by_name(selected_applicant)
    
    with col2:
        if draft_meta and draft_meta.get('applicant_contact'):
            default_applicant_contact = draft_meta['applicant_contact']
        elif applicant_info:
            default_applicant_contact = applicant_info.get("contact", "")
        else:
            default_applicant_contact = ""
        
        applicant_contact = st.text_input(
            "신청자 연락처",
            value=default_applicant_contact,
            placeholder="예: 010-5089-3105"
        )
        
        if draft_meta and draft_meta.get('address'):
            default_address = draft_meta['address']
        elif site_info:
            default_address = site_info.get("address", "")
        else:
            default_address = ""
        
        if draft_meta and draft_meta.get('contact'):
            default_contact = draft_meta['contact']
        elif site_info:
            default_contact = site_info.get("contact", "")
        else:
            default_contact = ""
        
        address = st.text_input(
            "배송지 주소",
            value=default_address,
            placeholder="예: 경기도 성남시 중원구 성남대로 1133"
        )
        
        contact = st.text_input(
            "현장 연락처 (담당자)",
            value=default_contact,
            placeholder="예: 010-2211-9352 정봉환 경비팀장"
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.subheader("품목 입력")
    
    if app_type == "경비물품":
        st.info("경비물품을 입력해주세요. 등록된 품목을 선택하거나 직접 입력하세요.")
        
        supply_product_list = get_supply_products()
        supply_options = ["직접 입력"] + [p['name'] for p in supply_product_list]
        
        if 'supplies_items' not in st.session_state:
            st.session_state.supplies_items = [
                {'_id': _new_item_id(), '품목명': '', '규격': '', '수량': 1}
            ]
        for item in st.session_state.supplies_items:
            if '_id' not in item:
                item['_id'] = _new_item_id()
        
        st.markdown("**No | 품목 선택 | 규격 | 수량 | 삭제**")
        
        supplies_to_delete = []
        for idx, item in enumerate(st.session_state.supplies_items):
            iid = item['_id']
            with st.container():
                cols = st.columns([0.5, 3, 2, 1, 0.5])
                with cols[0]:
                    st.write(f"**{idx+1}**")
                with cols[1]:
                    current_product = item.get('품목명', '')
                    if current_product in supply_options:
                        default_idx = supply_options.index(current_product)
                    else:
                        default_idx = 0
                    selected = st.selectbox('품목', supply_options, index=default_idx, key=f"sup_select_{iid}", label_visibility="collapsed")
                    
                    if selected == "직접 입력":
                        item['품목명'] = st.text_input('품목명', value=item.get('품목명', '') if item.get('품목명', '') not in supply_options else '', key=f"sup_name_{iid}", label_visibility="collapsed", placeholder="품목명 입력")
                    else:
                        item['품목명'] = selected
                        product_info = get_supply_product_by_name(selected)
                        if product_info and product_info.get('spec'):
                            item['규격'] = product_info.get('spec', '')
                with cols[2]:
                    item['규격'] = st.text_input('규격', value=item.get('규격', ''), key=f"sup_spec_{iid}", label_visibility="collapsed", placeholder="규격/옵션")
                with cols[3]:
                    item['수량'] = st.number_input('수량', value=item.get('수량', 1), min_value=1, key=f"sup_qty_{iid}", label_visibility="collapsed")
                with cols[4]:
                    if st.button("🗑️", key=f"del_sup_{iid}"):
                        supplies_to_delete.append(idx)
        
        if supplies_to_delete:
            for idx in sorted(supplies_to_delete, reverse=True):
                deleted_item = st.session_state.supplies_items.pop(idx)
                did = deleted_item['_id']
                for prefix in ('sup_select_', 'sup_name_', 'sup_spec_', 'sup_qty_', 'del_sup_'):
                    wkey = f"{prefix}{did}"
                    if wkey in st.session_state:
                        del st.session_state[wkey]
            st.rerun()
        
        col_add_sup_bot, col_space_sup = st.columns([1, 5])
        with col_add_sup_bot:
            if st.button("➕ 행 추가", use_container_width=True, key="add_supply"):
                st.session_state.supplies_items.append({'_id': _new_item_id(), '품목명': '', '규격': '', '수량': 1})
                st.rerun()
        
        edited_supplies = pd.DataFrame(st.session_state.supplies_items)
    
    else:
        st.info("피복 신청 품목을 입력해주세요. 등록된 품목을 선택하거나 직접 입력하세요.")
        
        uniform_product_list = get_uniform_products()
        uniform_options = ["선택 안함", "직접 입력"] + [p['name'] for p in uniform_product_list]
        
        top_sizes = ['선택없음', '이하', '90', '95', '100', '105', '110', '115', '120', '이상']
        bottom_sizes = ['선택없음', '이하', '28', '30', '32', '34', '36', '38', '40', '42', '이상']
        hat_sizes = ['선택없음', '대', '중', '소']
        shoe_sizes = ['선택없음', '이하', '250', '255', '260', '265', '270', '275', '280', '이상']
        
        if 'uniform_items' not in st.session_state:
            st.session_state.uniform_items = [
                {'_id': _new_item_id(), '업종': '경비직', '직책': '경비원', '근무자': '', '상의': '100', '하의': '32', '모자': '중', '신발': '선택없음',
                 '품목1': '', '수량1': 0, '품목2': '', '수량2': 0, '품목3': '', '수량3': 0, 'product_count': 3}
            ]
        
        for item in st.session_state.uniform_items:
            if 'product_count' not in item:
                item['product_count'] = 3
            if '_id' not in item:
                item['_id'] = _new_item_id()
        
        items_to_delete = []
        for idx, item in enumerate(st.session_state.uniform_items):
            iid = item['_id']
            with st.container():
                st.markdown(f'<div class="item-row">', unsafe_allow_html=True)
                st.markdown(f"<div style='font-weight:600; color:var(--primary); margin-bottom:0.5rem;'>신청자 {idx+1}</div>", unsafe_allow_html=True)
                cols1 = st.columns([1, 1, 1.5, 0.7, 0.7, 0.6, 0.7, 0.4])
                with cols1[0]:
                    item['업종'] = st.selectbox('업종', ['관리직', '경비직'], index=['관리직', '경비직'].index(item.get('업종', '경비직')), key=f"job_{iid}")
                with cols1[1]:
                    item['직책'] = st.text_input('직책', value=item.get('직책', '경비원'), key=f"pos_{iid}")
                with cols1[2]:
                    item['근무자'] = st.text_input('근무자', value=item.get('근무자', ''), key=f"worker_{iid}", placeholder="이름")
                with cols1[3]:
                    item['상의'] = st.selectbox('상의', top_sizes, index=top_sizes.index(item.get('상의', '100')) if item.get('상의', '100') in top_sizes else 4, key=f"top_{iid}")
                with cols1[4]:
                    item['하의'] = st.selectbox('하의', bottom_sizes, index=bottom_sizes.index(item.get('하의', '32')) if item.get('하의', '32') in bottom_sizes else 4, key=f"bot_{iid}")
                with cols1[5]:
                    item['모자'] = st.selectbox('모자', hat_sizes, index=hat_sizes.index(item.get('모자', '중')) if item.get('모자', '중') in hat_sizes else 2, key=f"hat_{iid}")
                with cols1[6]:
                    item['신발'] = st.selectbox('신발', shoe_sizes, index=shoe_sizes.index(item.get('신발', '선택없음')) if item.get('신발', '선택없음') in shoe_sizes else 0, key=f"shoe_{iid}")
                with cols1[7]:
                    if st.button("🗑️", key=f"del_{iid}", help="신청자 삭제"):
                        items_to_delete.append(idx)
                
                product_count = item.get('product_count', 3)
                
                products_per_row = 3
                num_rows = (product_count + products_per_row - 1) // products_per_row
                
                for row_num in range(num_rows):
                    start_i = row_num * products_per_row + 1
                    end_i = min(start_i + products_per_row, product_count + 1)
                    
                    cols2 = st.columns([2, 0.8] * (end_i - start_i))
                    col_idx = 0
                    
                    for i in range(start_i, end_i):
                        prod_key = f'품목{i}'
                        qty_key = f'수량{i}'
                        
                        with cols2[col_idx]:
                            current_uniform = item.get(prod_key, '')
                            if current_uniform in uniform_options:
                                default_uniform_idx = uniform_options.index(current_uniform)
                            else:
                                default_uniform_idx = 0
                            selected_uniform = st.selectbox(f'품목{i}', uniform_options, index=default_uniform_idx, key=f"unif_select_{iid}_{i}")
                            
                            if selected_uniform == "직접 입력":
                                item[prod_key] = st.text_input(f'품목{i} 입력', value=item.get(prod_key, '') if item.get(prod_key, '') not in uniform_options else '', key=f"prod_{iid}_{i}", label_visibility="collapsed", placeholder="품목 입력")
                            elif selected_uniform == "선택 안함":
                                item[prod_key] = ''
                            else:
                                item[prod_key] = selected_uniform
                        
                        with cols2[col_idx + 1]:
                            item[qty_key] = st.number_input(f'수량{i}', value=item.get(qty_key, 0), min_value=0, key=f"unif_qty_{iid}_{i}")
                        
                        col_idx += 2
                
                btn_cols = st.columns([1, 1, 4])
                with btn_cols[0]:
                    if st.button("➕ 품목추가", key=f"add_prod_{iid}", help="품목 추가"):
                        item['product_count'] = item.get('product_count', 3) + 1
                        new_prod_key = f"품목{item['product_count']}"
                        new_qty_key = f"수량{item['product_count']}"
                        item[new_prod_key] = ''
                        item[new_qty_key] = 0
                        st.rerun()
                with btn_cols[1]:
                    if product_count > 1:
                        if st.button("➖ 품목삭제", key=f"del_prod_{iid}", help="마지막 품목 삭제"):
                            last_prod_key = f"품목{product_count}"
                            last_qty_key = f"수량{product_count}"
                            if last_prod_key in item:
                                del item[last_prod_key]
                            if last_qty_key in item:
                                del item[last_qty_key]
                            for wkey_prefix in (f'unif_select_{iid}_{product_count}', f'unif_qty_{iid}_{product_count}', f'prod_{iid}_{product_count}'):
                                if wkey_prefix in st.session_state:
                                    del st.session_state[wkey_prefix]
                            item['product_count'] = product_count - 1
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        
        if items_to_delete:
            for idx in sorted(items_to_delete, reverse=True):
                deleted_item = st.session_state.uniform_items.pop(idx)
                did = deleted_item.get('_id', '')
                if did:
                    product_count = deleted_item.get('product_count', 3)
                    for prefix in ('job_', 'pos_', 'worker_', 'top_', 'bot_', 'hat_', 'shoe_', 'del_', 'add_prod_', 'del_prod_'):
                        wkey = f"{prefix}{did}"
                        if wkey in st.session_state:
                            del st.session_state[wkey]
                    for i in range(1, product_count + 1):
                        for prefix in ('unif_select_', 'unif_qty_', 'prod_'):
                            wkey = f"{prefix}{did}_{i}"
                            if wkey in st.session_state:
                                del st.session_state[wkey]
            st.rerun()
        
        col_add_bot, col_copy_bot, col_space_bot = st.columns([1, 1, 4])
        with col_add_bot:
            if st.button("➕ 행 추가", use_container_width=True):
                st.session_state.uniform_items.append(
                    {'_id': _new_item_id(), '업종': '경비직', '직책': '경비원', '근무자': '', '상의': '100', '하의': '32', '모자': '중', '신발': '선택없음',
                     '품목1': '', '수량1': 0, '품목2': '', '수량2': 0, '품목3': '', '수량3': 0, 'product_count': 3}
                )
                st.rerun()
        with col_copy_bot:
            if st.button("📋 복사 행추가", use_container_width=True, help="마지막 신청자 품목 복사"):
                if st.session_state.uniform_items:
                    last_item = st.session_state.uniform_items[-1]
                    last_iid = last_item['_id']
                    product_count = last_item.get('product_count', 3)
                    new_item = {
                        '_id': _new_item_id(),
                        '업종': st.session_state.get(f'job_{last_iid}', last_item.get('업종', '경비직')),
                        '직책': st.session_state.get(f'pos_{last_iid}', last_item.get('직책', '경비원')),
                        '근무자': '',
                        '상의': st.session_state.get(f'top_{last_iid}', last_item.get('상의', '100')),
                        '하의': st.session_state.get(f'bot_{last_iid}', last_item.get('하의', '32')),
                        '모자': st.session_state.get(f'hat_{last_iid}', last_item.get('모자', '중')),
                        '신발': st.session_state.get(f'shoe_{last_iid}', last_item.get('신발', '선택없음')),
                        'product_count': product_count
                    }
                    for i in range(1, product_count + 1):
                        prod_value = st.session_state.get(f'unif_select_{last_iid}_{i}', last_item.get(f'품목{i}', ''))
                        qty_value = st.session_state.get(f'unif_qty_{last_iid}_{i}', last_item.get(f'수량{i}', 0))
                        if prod_value == '선택 안함':
                            prod_value = ''
                        elif prod_value == '직접 입력':
                            prod_value = st.session_state.get(f'prod_{last_iid}_{i}', last_item.get(f'품목{i}', ''))
                        new_item[f'품목{i}'] = prod_value
                        new_item[f'수량{i}'] = qty_value
                    st.session_state.uniform_items.append(new_item)
                    st.rerun()
                else:
                    st.session_state.uniform_items.append(
                        {'_id': _new_item_id(), '업종': '경비직', '직책': '경비원', '근무자': '', '상의': '100', '하의': '32', '모자': '중', '신발': '선택없음',
                         '품목1': '', '수량1': 0, '품목2': '', '수량2': 0, '품목3': '', '수량3': 0, 'product_count': 3}
                    )
                    st.rerun()
        
        edited_uniform = pd.DataFrame(st.session_state.uniform_items)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.subheader("비고 및 참고사항")
    default_remarks = draft_meta.get('remarks', '') if draft_meta else ''
    remarks_placeholder = "예) 다원피엠씨입니다." if app_type == "경비물품" else "예) 동계상의 00벌, 동계하의 00벌입니다."
    remarks = st.text_area(
        "비고 / 참고사항",
        value=default_remarks,
        placeholder=remarks_placeholder,
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    
    with col_btn1:
        if st.button("신청서 생성 (PDF)", type="primary", use_container_width=True):
            if not site_name:
                st.error("현장명을 입력해주세요.")
            elif not applicant:
                st.error("신청자를 입력해주세요.")
            else:
                form_data = {
                    'company': company,
                    'application_date': application_date.strftime('%Y. %m. %d.'),
                    'site_name': site_name,
                    'applicant': applicant,
                    'applicant_contact': applicant_contact,
                    'address': address,
                    'contact': contact,
                    'remarks': remarks
                }
                
                if app_type == "경비물품":
                    items = []
                    total_amount = 0
                    for _, row in edited_supplies.iterrows():
                        if row['품목명']:
                            quantity = int(row['수량'])
                            product_info = get_supply_product_by_name(row['품목명'])
                            unit_price = product_info.get('unit_price', 0) if product_info else 0
                            amount = unit_price * quantity
                            total_amount += amount
                            items.append({
                                'name': row['품목명'],
                                'spec': row.get('규격', ''),
                                'quantity': quantity,
                                'unit_price': unit_price,
                                'amount': amount
                            })
                    form_data['items'] = items
                    form_data['total_amount'] = total_amount
                else:
                    items = []
                    total_amount = 0
                    for _, row in edited_uniform.iterrows():
                        products_list = []
                        product_count = int(row.get('product_count', 3))
                        for i in range(1, product_count + 1):
                            prod_key = f'품목{i}'
                            qty_key = f'수량{i}'
                            product_name = row.get(prod_key, '')
                            quantity = int(row.get(qty_key, 0)) if pd.notna(row.get(qty_key, 0)) else 0
                            if product_name and quantity > 0:
                                product_info = get_uniform_product_by_name(product_name)
                                unit_price = product_info.get('unit_price', 0) if product_info else 0
                                amount = unit_price * quantity
                                total_amount += amount
                                products_list.append({
                                    'name': product_name,
                                    'quantity': quantity,
                                    'unit_price': unit_price
                                })
                        
                        if products_list:
                            items.append({
                                'job_type': row['업종'],
                                'position': row['직책'],
                                'worker': row['근무자'],
                                'top_size': row['상의'],
                                'bottom_size': row['하의'],
                                'hat_size': row['모자'],
                                'shoe_size': row.get('신발', '선택없음'),
                                'products': products_list
                            })
                    form_data['items'] = items
                    form_data['total_amount'] = total_amount
                
                try:
                    pdf_path = generate_pdf(form_data, app_type)
                    st.session_state.pdf_generated = True
                    st.session_state.pdf_path = pdf_path
                    st.session_state.form_data = form_data
                    st.session_state.items = items
                    
                    if os.path.exists(pdf_path):
                        with open(pdf_path, 'rb') as f:
                            save_pdf_to_db(
                                os.path.basename(pdf_path),
                                f.read(),
                                app_type=app_type,
                                company=form_data.get('company', ''),
                                site_name=form_data.get('site_name', '')
                            )
                    
                    success, message = append_to_master(
                        form_data.get('application_date', ''),
                        app_type,
                        form_data.get('company', ''),
                        form_data.get('site_name', ''),
                        form_data.get('applicant', ''),
                        items
                    )
                    if success:
                        st.success(f"PDF가 생성되고 데이터가 저장되었습니다: {os.path.basename(pdf_path)}")
                        if st.session_state.loaded_draft_id:
                            delete_draft(st.session_state.loaded_draft_id)
                            st.session_state.loaded_draft_id = None
                            st.session_state.draft_metadata = None
                    else:
                        st.warning(f"PDF 생성됨. 데이터 저장 오류: {message}")
                except Exception as e:
                    st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
    
    with col_btn2:
        if st.button("💾 임시저장", use_container_width=True):
            if app_type == "경비물품":
                items_to_save = st.session_state.supplies_items
            else:
                items_to_save = st.session_state.uniform_items
            
            draft_data = {
                'company': company,
                'app_type': app_type,
                'application_date': application_date.strftime('%Y-%m-%d'),
                'site_name': site_name,
                'applicant': applicant,
                'applicant_contact': applicant_contact,
                'address': address,
                'contact': contact,
                'remarks': remarks,
                'items': items_to_save
            }
            
            if st.session_state.loaded_draft_id:
                update_draft(st.session_state.loaded_draft_id, draft_data)
                st.success("임시저장이 업데이트되었습니다.")
            else:
                draft_id = save_draft(draft_data)
                st.session_state.loaded_draft_id = draft_id
                st.success("임시저장되었습니다.")
    
    with col_btn3:
        if st.button("🔄 새로 작성", use_container_width=True):
            st.session_state.clear_form_pending = True
            st.rerun()
    
    if st.session_state.pdf_generated and st.session_state.pdf_path:
        st.divider()
        st.subheader("PDF 미리보기 및 전송")
        
        col_preview, col_send = st.columns([2, 1])
        
        with col_preview:
            if os.path.exists(st.session_state.pdf_path):
                with open(st.session_state.pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="PDF 다운로드",
                        data=pdf_file.read(),
                        file_name=os.path.basename(st.session_state.pdf_path),
                        mime="application/pdf"
                    )
        
        with col_send:
            st.subheader("이메일 전송")
            
            try:
                smtp_email = st.secrets.get("SMTP_EMAIL", os.environ.get("SMTP_EMAIL", ""))
                smtp_password = st.secrets.get("SMTP_PASSWORD", os.environ.get("SMTP_PASSWORD", ""))
            except Exception:
                smtp_email = os.environ.get("SMTP_EMAIL", "")
                smtp_password = os.environ.get("SMTP_PASSWORD", "")
            
            if not smtp_email or not smtp_password:
                st.warning("SMTP 설정이 필요합니다. Secrets에 SMTP_EMAIL과 SMTP_PASSWORD를 설정해주세요.")
            
            email_recipients = get_email_recipients()
            default_email = get_default_email(app_type)
            
            if email_recipients:
                recipient_options = ["직접 입력"] + [f"{r['company_name']} ({r['email']})" for r in email_recipients]
                selected_recipient = st.selectbox(
                    "수신자 선택",
                    options=recipient_options,
                    index=0,
                    help="등록된 수신자를 선택하거나 '직접 입력'을 선택하세요"
                )
                
                if selected_recipient == "직접 입력":
                    to_email = st.text_input(
                        "수신자 이메일",
                        value=default_email,
                        placeholder="수신자 이메일을 입력하세요"
                    )
                else:
                    for r in email_recipients:
                        if f"{r['company_name']} ({r['email']})" == selected_recipient:
                            to_email = r['email']
                            st.text(f"이메일: {to_email}")
                            break
            else:
                to_email = st.text_input(
                    "수신자 이메일",
                    value=default_email,
                    placeholder="수신자 이메일을 입력하세요",
                    help=f"기본값: {default_email}"
                )
            
            if st.button("이메일 전송", type="secondary"):
                if not smtp_email or not smtp_password:
                    st.error("SMTP 설정이 필요합니다.")
                elif not to_email:
                    st.error("수신자 이메일을 입력해주세요.")
                else:
                    with st.spinner("이메일 전송 중..."):
                        success, message = send_application_email(
                            smtp_email,
                            smtp_password,
                            app_type,
                            company,
                            site_name,
                            st.session_state.pdf_path,
                            to_email
                        )
                        if success:
                            st.success(message)
                        else:
                            st.error(message)

elif menu == "신청내역조회":
    st.subheader("신청 내역 조회")
    
    df = get_master_data()
    
    if not df.empty:
        try:
            if '날짜' in df.columns:
                df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        except Exception as e:
            st.warning(f"날짜 데이터 변환 중 일부 누락이 발생했습니다: {str(e)}")
        
        st.markdown("### 검색 필터")
        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
        
        with col_filter1:
            companies = ['전체'] + df['법인명'].dropna().unique().tolist()
            selected_company = st.selectbox("법인명", companies)
        
        with col_filter2:
            types = ['전체'] + df['구분'].dropna().unique().tolist()
            selected_type = st.selectbox("구분", types)
        
        with col_filter3:
            months = ['전체'] + sorted(df['날짜'].dt.strftime('%Y-%m').dropna().unique().tolist(), reverse=True)
            selected_month = st.selectbox("월별", months)
        
        with col_filter4:
            sites = ['전체'] + df['현장명'].dropna().unique().tolist()
            selected_site_filter = st.selectbox("현장명", sites)
        
        use_date_filter = st.checkbox("기간 검색 사용", value=False)
        if use_date_filter:
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_date = st.date_input("시작일", value=date.today().replace(day=1), key="start_date")
            with col_date2:
                end_date = st.date_input("종료일", value=date.today(), key="end_date")
        else:
            start_date = None
            end_date = None
        
        filtered_df = df.copy()
        if selected_company != '전체':
            filtered_df = filtered_df[filtered_df['법인명'] == selected_company]
        if selected_type != '전체':
            filtered_df = filtered_df[filtered_df['구분'] == selected_type]
        if selected_month != '전체':
            filtered_df = filtered_df[filtered_df['날짜'].dt.strftime('%Y-%m') == selected_month]
        if selected_site_filter != '전체':
            filtered_df = filtered_df[filtered_df['현장명'] == selected_site_filter]
        if start_date:
            filtered_df = filtered_df[filtered_df['날짜'] >= pd.Timestamp(start_date)]
        if end_date:
            filtered_df = filtered_df[filtered_df['날짜'] <= pd.Timestamp(end_date)]
        
        st.markdown("### 조회 결과")
        
        if not filtered_df.empty:
            def format_product_with_spec(group):
                items = []
                for _, row in group.iterrows():
                    product = str(row['품목명']) if pd.notna(row['품목명']) else ''
                    spec = str(row['규격']) if pd.notna(row['규격']) and row['규격'] else ''
                    size_info = ''
                    if spec and ('상의:' in spec or '하의:' in spec or '모자:' in spec or '신발:' in spec):
                        parts = spec.split('/')
                        sizes = []
                        for part in parts:
                            if part.startswith('상의:') or part.startswith('하의:') or part.startswith('모자:') or part.startswith('신발:'):
                                sizes.append(part)
                        if sizes:
                            size_info = f"[{'/'.join(sizes)}]"
                    if product:
                        if size_info:
                            items.append(f"{product}{size_info}")
                        else:
                            items.append(product)
                return ', '.join(items[:3]) + ('...' if len(items) > 3 else '')
            
            grouped = filtered_df.groupby(['날짜', '법인명', '현장명', '신청자', '구분']).apply(
                lambda x: pd.Series({
                    '품목': format_product_with_spec(x),
                    '총액': x['합계금액'].sum()
                })
            ).reset_index()
            grouped['품목수'] = filtered_df.groupby(['날짜', '법인명', '현장명', '신청자', '구분']).size().values
            
            col_metric1, col_metric2, col_export1, col_export2 = st.columns([1, 1, 1, 1])
            with col_metric1:
                st.metric("총 건수", f"{len(grouped)}건")
            with col_metric2:
                unique_sites = filtered_df['현장명'].nunique()
                st.metric("현장 수", f"{unique_sites}개")
            
            with col_export1:
                export_df = filtered_df[['날짜', '법인명', '현장명', '신청자', '구분', '품목명', '규격', '수량', '단가', '합계금액']].copy()
                export_df['날짜'] = pd.to_datetime(export_df['날짜']).dt.strftime('%Y-%m-%d')
                
                from io import BytesIO
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    export_df.to_excel(writer, index=False, sheet_name='신청내역')
                excel_buffer.seek(0)
                
                month_label = selected_month if selected_month != '전체' else datetime.now().strftime('%Y-%m')
                st.download_button(
                    label="📊 엑셀 다운로드",
                    data=excel_buffer,
                    file_name=f"신청내역_{month_label}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col_export2:
                from pdf_generator import generate_application_history_pdf
                pdf_buffer = generate_application_history_pdf(filtered_df, selected_month if selected_month != '전체' else '전체')
                month_label = selected_month if selected_month != '전체' else datetime.now().strftime('%Y-%m')
                st.download_button(
                    label="📄 PDF 다운로드",
                    data=pdf_buffer,
                    file_name=f"신청내역_{month_label}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            grouped['날짜_str'] = pd.to_datetime(grouped['날짜']).dt.strftime('%Y-%m-%d')
            
            # 선택 키 목록 (종합용)
            all_sel_keys = [f"sel_app_{idx}" for idx in grouped.index]
            
            sel_col1, sel_col2, sel_col3 = st.columns([1, 1, 4])
            with sel_col1:
                if st.button("☑️ 전체 선택", use_container_width=True):
                    for k in all_sel_keys:
                        st.session_state[k] = True
                    st.rerun()
            with sel_col2:
                if st.button("⬜ 전체 해제", use_container_width=True):
                    for k in all_sel_keys:
                        st.session_state[k] = False
                    st.rerun()
            
            for idx, row in grouped.iterrows():
                pdf_key = f"pdf_{row['날짜_str']}_{row['현장명']}_{row['신청자']}_{row['구분']}_{idx}"
                btn_key = f"edit_{row['날짜_str']}_{row['현장명']}_{row['신청자']}_{row['구분']}_{idx}"
                del_key = f"del_{row['날짜_str']}_{row['현장명']}_{row['신청자']}_{row['구분']}_{idx}"
                sel_key = f"sel_app_{idx}"
                
                company = row['법인명']
                date_str = row['날짜_str'].replace('-', '')
                if row['구분'] == '피복':
                    type_suffix = "경비원 피복 신청서"
                else:
                    type_suffix = "경비용품 신청서"
                pdf_filename = f"[{company}]{date_str}_{row['현장명']}_{type_suffix}.pdf"
                pdf_path = os.path.join('output', pdf_filename)
                
                pdf_data = None
                if os.path.exists(pdf_path):
                    with open(pdf_path, 'rb') as f:
                        pdf_data = f.read()
                else:
                    pdf_data = get_pdf_from_db(pdf_filename)
                
                is_selected = st.session_state.get(sel_key, False)
                chk_icon = "✅" if is_selected else "⬜"
                expander_label = f"{chk_icon} **{row['날짜_str']}** | {row['구분']} | {row['현장명']} | {row['신청자']} | {row['품목수']}개"
                with st.expander(expander_label):
                    st.checkbox("📌 종합에 포함", key=sel_key, value=is_selected)
                    detail_df_temp = filtered_df.copy()
                    detail_df_temp['날짜_str'] = detail_df_temp['날짜'].dt.strftime('%Y-%m-%d')
                    detail_items = detail_df_temp[
                        (detail_df_temp['날짜_str'] == row['날짜_str']) &
                        (detail_df_temp['현장명'] == row['현장명']) &
                        (detail_df_temp['신청자'] == row['신청자']) &
                        (detail_df_temp['구분'] == row['구분'])
                    ][['품목명', '규격', '수량', '단가', '합계금액']].copy()
                    detail_items['수량'] = detail_items['수량'].apply(lambda x: int(x) if pd.notna(x) else 0)
                    detail_items['단가'] = detail_items['단가'].apply(lambda x: f"{int(x):,}" if pd.notna(x) and x else "-")
                    detail_items['합계금액'] = detail_items['합계금액'].apply(lambda x: f"{int(x):,}" if pd.notna(x) and x else "-")
                    detail_items.columns = ['품목명', '규격', '수량', '단가(원)', '합계(원)']
                    st.dataframe(detail_items, use_container_width=True, hide_index=True)
                    
                    act_cols = st.columns([1, 1, 1, 4])
                    with act_cols[0]:
                        if pdf_data:
                            st.download_button(
                                label="📄 PDF",
                                data=pdf_data,
                                file_name=pdf_filename,
                                mime="application/pdf",
                                key=pdf_key,
                                use_container_width=True
                            )
                        else:
                            st.button("📄 PDF 없음", disabled=True, key=pdf_key, use_container_width=True)
                    with act_cols[1]:
                        reapply_clicked = st.button("✏️ 재신청", key=btn_key, use_container_width=True)
                    with act_cols[2]:
                        delete_clicked = st.button("🗑️ 삭제", key=del_key, use_container_width=True)
                    
                    if delete_clicked:
                        confirm_delete_dialog(
                            'application',
                            None,
                            f"{row['날짜_str']} - {row['현장명']} ({row['신청자']})",
                            extra_info={
                                'date': row['날짜_str'],
                                'site': row['현장명'],
                                'applicant': row['신청자'],
                                'app_type': row['구분'],
                                'company': row['법인명']
                            }
                        )
                
                if reapply_clicked:
                    display_df_temp = filtered_df.copy()
                    display_df_temp['날짜_str'] = display_df_temp['날짜'].dt.strftime('%Y-%m-%d')
                    
                    app_items = display_df_temp[
                        (display_df_temp['날짜_str'] == row['날짜_str']) & 
                        (display_df_temp['현장명'] == row['현장명']) & 
                        (display_df_temp['신청자'] == row['신청자']) &
                        (display_df_temp['구분'] == row['구분'])
                    ]
                    
                    reapply_site_info = get_site_by_name(row['현장명'])
                    reapply_address = reapply_site_info.get('address', '') if reapply_site_info else ''
                    reapply_contact = reapply_site_info.get('contact', '') if reapply_site_info else ''
                    
                    reapply_applicant_info = get_applicant_by_name(row['신청자'])
                    reapply_applicant_contact = reapply_applicant_info.get('contact', '') if reapply_applicant_info else ''
                    
                    st.session_state.reapply_pending = True
                    st.session_state.form_version = st.session_state.get('form_version', 0) + 1
                    if row['구분'] == '경비물품':
                        items_list = []
                        for _, item_row in app_items.iterrows():
                            items_list.append({
                                '_id': _new_item_id(),
                                '품목명': item_row['품목명'],
                                '규격': str(item_row['규격']) if pd.notna(item_row['규격']) else '',
                                '수량': int(item_row['수량']) if pd.notna(item_row['수량']) else 1
                            })
                        st.session_state.supplies_items = items_list
                    else:
                        grouped_items = {}
                        for _, item_row in app_items.iterrows():
                            spec = str(item_row['규격']) if pd.notna(item_row['규격']) else ''
                            worker = ''
                            top_size = '선택없음'
                            bottom_size = '선택없음'
                            hat_size = '선택없음'
                            shoe_size = '선택없음'
                            
                            if spec:
                                parts = spec.split('/')
                                for part in parts:
                                    if part.startswith('근무자:'):
                                        worker = part.replace('근무자:', '')
                                    elif part.startswith('상의:'):
                                        top_size = part.replace('상의:', '')
                                    elif part.startswith('하의:'):
                                        bottom_size = part.replace('하의:', '')
                                    elif part.startswith('모자:'):
                                        hat_size = part.replace('모자:', '')
                                    elif part.startswith('신발:'):
                                        shoe_size = part.replace('신발:', '')
                                if not any(part.startswith(('근무자:', '상의:', '하의:', '모자:', '신발:')) for part in parts):
                                    worker = spec
                            
                            spec_key = spec if spec else f"applicant_{len(grouped_items)}"
                            
                            if spec_key not in grouped_items:
                                grouped_items[spec_key] = {
                                    '업종': '경비직',
                                    '직책': '경비원',
                                    '근무자': worker,
                                    '상의': top_size if top_size else '선택없음',
                                    '하의': bottom_size if bottom_size else '선택없음',
                                    '모자': hat_size if hat_size else '선택없음',
                                    '신발': shoe_size if shoe_size else '선택없음',
                                    'products': []
                                }
                            
                            grouped_items[spec_key]['products'].append({
                                'name': item_row['품목명'] if pd.notna(item_row['품목명']) else '',
                                'qty': int(item_row['수량']) if pd.notna(item_row['수량']) else 1
                            })
                        
                        items_list = []
                        for spec_key, item_data in grouped_items.items():
                            uniform_item = {
                                '_id': _new_item_id(),
                                '업종': item_data['업종'],
                                '직책': item_data['직책'],
                                '근무자': item_data['근무자'],
                                '상의': item_data['상의'],
                                '하의': item_data['하의'],
                                '모자': item_data['모자'],
                                '신발': item_data.get('신발', '선택없음'),
                            }
                            
                            products = item_data['products']
                            product_count = max(3, len(products))
                            
                            for i in range(product_count):
                                if i < len(products):
                                    uniform_item[f'품목{i+1}'] = products[i]['name']
                                    uniform_item[f'수량{i+1}'] = products[i]['qty']
                                else:
                                    uniform_item[f'품목{i+1}'] = ''
                                    uniform_item[f'수량{i+1}'] = 0
                            
                            uniform_item['product_count'] = product_count
                            items_list.append(uniform_item)
                        
                        st.session_state.uniform_items = items_list
                    
                    st.session_state.draft_metadata = {
                        'site_name': row['현장명'],
                        'applicant': row['신청자'],
                        'applicant_contact': reapply_applicant_contact,
                        'address': reapply_address,
                        'contact': reapply_contact,
                        'remarks': '',
                        'application_date': date.today().strftime('%Y-%m-%d')
                    }
                    
                    st.session_state.loaded_draft_id = None
                    st.session_state.pending_menu = "신청서 작성"
                    st.session_state.pending_company = row['법인명']
                    st.session_state.pending_app_type = row['구분']
                    st.rerun()
            
            st.divider()
            
            # 선택된 건 종합
            selected_rows = grouped[grouped.index.map(lambda i: st.session_state.get(f"sel_app_{i}", False))]
            
            st.markdown("### 선택 항목 종합")
            if selected_rows.empty:
                st.info("위 목록에서 신청 건을 선택하면 품목별 수량 종합이 표시됩니다. (각 항목을 클릭해서 열고 '📌 종합에 포함' 체크, 또는 상단 '☑️ 전체 선택' 버튼 사용)")
            else:
                st.success(f"선택된 신청 건: **{len(selected_rows)}건**")
                
                # 선택된 행에 해당하는 품목 데이터 추출
                filtered_df_temp = filtered_df.copy()
                filtered_df_temp['날짜_str'] = filtered_df_temp['날짜'].dt.strftime('%Y-%m-%d')
                
                sel_masks = []
                for _, srow in selected_rows.iterrows():
                    mask = (
                        (filtered_df_temp['날짜_str'] == srow['날짜_str']) &
                        (filtered_df_temp['현장명'] == srow['현장명']) &
                        (filtered_df_temp['신청자'] == srow['신청자']) &
                        (filtered_df_temp['구분'] == srow['구분'])
                    )
                    sel_masks.append(mask)
                
                combined_mask = sel_masks[0]
                for m in sel_masks[1:]:
                    combined_mask = combined_mask | m
                
                sel_items_df = filtered_df_temp[combined_mask & filtered_df_temp['품목명'].notna() & (filtered_df_temp['품목명'] != '')].copy()
                
                if not sel_items_df.empty:
                    supply_sel = sel_items_df[sel_items_df['구분'] == '경비물품']
                    uniform_sel = sel_items_df[sel_items_df['구분'] == '피복']
                    
                    col_sup, col_uni = st.columns(2)
                    
                    with col_sup:
                        st.markdown("#### 경비물품")
                        if not supply_sel.empty:
                            sup_summary = (
                                supply_sel.groupby('품목명')
                                .agg(총수량=('수량', 'sum'), 총금액=('합계금액', 'sum'))
                                .reset_index()
                                .rename(columns={'품목명': '품목'})
                                .sort_values('총수량', ascending=False)
                            )
                            sup_summary['총수량'] = sup_summary['총수량'].astype(int)
                            sup_summary['총금액'] = sup_summary['총금액'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "-")
                            st.dataframe(sup_summary, use_container_width=True, hide_index=True)
                            total_qty = supply_sel['수량'].sum()
                            total_amt = supply_sel['합계금액'].sum()
                            st.caption(f"총 {int(total_qty):,}개 | 합계 {int(total_amt):,}원")
                        else:
                            st.info("선택 건 중 경비물품 없음")
                    
                    with col_uni:
                        st.markdown("#### 피복")
                        if not uniform_sel.empty:
                            uni_summary = (
                                uniform_sel.groupby('품목명')
                                .agg(총수량=('수량', 'sum'), 총금액=('합계금액', 'sum'))
                                .reset_index()
                                .rename(columns={'품목명': '품목'})
                                .sort_values('총수량', ascending=False)
                            )
                            uni_summary['총수량'] = uni_summary['총수량'].astype(int)
                            uni_summary['총금액'] = uni_summary['총금액'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "-")
                            st.dataframe(uni_summary, use_container_width=True, hide_index=True)
                            total_qty = uniform_sel['수량'].sum()
                            total_amt = uniform_sel['합계금액'].sum()
                            st.caption(f"총 {int(total_qty):,}개 | 합계 {int(total_amt):,}원")
                        else:
                            st.info("선택 건 중 피복 없음")
                else:
                    st.info("선택된 건의 품목 데이터가 없습니다.")
        else:
            st.info("검색 조건에 맞는 데이터가 없습니다.")
    else:
        st.info("저장된 데이터가 없습니다.")

elif menu == "월별 집계":
    st.subheader("월별 비용 집계")
    
    summary_tabs = st.tabs(["집계 현황", "현장 관리"])
    
    with summary_tabs[0]:
        summary_data = get_all_monthly_summary()
        
        summary_type = st.radio(
            "집계 유형",
            options=["피복", "경비물품"],
            horizontal=True,
            key="summary_type_radio"
        )
        
        col_label, col_filter, col_exp1, col_exp2 = st.columns([0.7, 1.3, 1, 1])
        with col_label:
            st.markdown("<div style='padding-top: 8px;'>법인 선택</div>", unsafe_allow_html=True)
        with col_filter:
            company_filter = st.selectbox(
                "법인 선택",
                options=["전체", "미래", "다원"],
                key="summary_company_filter",
                label_visibility="collapsed"
            )
        
        sheet_key = '피복' if summary_type == '피복' else '경비물품'
        df_summary = summary_data.get(sheet_key, pd.DataFrame())
        
        if not df_summary.empty:
            if company_filter != "전체":
                df_summary = df_summary[df_summary['구분'] == company_filter]
            
            display_cols = ['구분', '현장명', '예산', '1월', '2월', '3월', '4월', '5월', '6월', 
                           '7월', '8월', '9월', '10월', '11월', '12월', '합계', '가용']
            available_cols = [col for col in display_cols if col in df_summary.columns]
            df_display = df_summary[available_cols].copy()
            
            for col in df_display.columns:
                if col not in ['구분', '현장명']:
                    df_display[col] = pd.to_numeric(df_display[col], errors='coerce').fillna(0).astype(int)
            
            if '합계' in df_display.columns and '예산' in df_display.columns:
                df_display['사용률'] = df_display.apply(
                    lambda r: f"{r['합계'] / r['예산'] * 100:.1f}%" if r['예산'] > 0 else "-",
                    axis=1
                )
            
            total_budget = df_display['예산'].sum() if '예산' in df_display.columns else 0
            total_used = df_display['합계'].sum() if '합계' in df_display.columns else 0
            total_available = df_display['가용'].sum() if '가용' in df_display.columns else 0
            usage_rate = (total_used / total_budget * 100) if total_budget > 0 else 0
            
            with col_exp1:
                from io import BytesIO
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df_export = df_display.copy()
                    totals_row = {col: '' for col in df_export.columns}
                    totals_row['구분'] = '합계'
                    totals_row['현장명'] = ''
                    for col in df_export.columns:
                        if col not in ['구분', '현장명']:
                            totals_row[col] = df_export[col].sum()
                    df_export = pd.concat([df_export, pd.DataFrame([totals_row])], ignore_index=True)
                    
                    summary_row = {col: '' for col in df_export.columns}
                    summary_row['구분'] = '총예산'
                    summary_row['현장명'] = f"{total_budget:,}원"
                    summary_row['예산'] = ''
                    summary_row['1월'] = '총사용'
                    summary_row['2월'] = f"{total_used:,}원"
                    summary_row['3월'] = ''
                    summary_row['4월'] = '사용률'
                    summary_row['5월'] = f"{usage_rate:.1f}%"
                    df_export = pd.concat([df_export, pd.DataFrame([summary_row])], ignore_index=True)
                    
                    df_export.to_excel(writer, index=False, sheet_name=f'{summary_type}_{company_filter}')
                excel_buffer.seek(0)
                
                st.download_button(
                    label="📊 엑셀",
                    data=excel_buffer,
                    file_name=f"월별집계_{summary_type}_{company_filter}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col_exp2:
                from pdf_generator import generate_monthly_summary_pdf
                month_cols = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월']
                export_df_for_pdf = df_display.rename(columns={'구분': 'company', '현장명': 'site_name', '예산': 'budget'})
                pdf_buffer = generate_monthly_summary_pdf(
                    export_df_for_pdf, 
                    f"{summary_type} ({company_filter})", 
                    month_cols,
                    total_budget=total_budget,
                    total_used=total_used,
                    usage_rate=usage_rate
                )
                st.download_button(
                    label="📄 PDF",
                    data=pdf_buffer,
                    file_name=f"월별집계_{summary_type}_{company_filter}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "예산": st.column_config.NumberColumn("예산", format="%d"),
                    "합계": st.column_config.NumberColumn("합계", format="%d"),
                    "가용": st.column_config.NumberColumn("가용", format="%d"),
                }
            )
            
            st.divider()
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("총 예산", f"{total_budget:,}원")
            with col_m2:
                st.metric("총 사용", f"{total_used:,}원")
            with col_m3:
                st.metric("총 가용", f"{total_available:,}원")
            with col_m4:
                st.metric("사용률", f"{usage_rate:.1f}%")
        else:
            st.info("집계할 데이터가 없습니다.")
    
    with summary_tabs[1]:
        st.markdown("### 현장 추가/삭제/예산 수정")
        
        col_sync, col_sync_info = st.columns([1, 3])
        with col_sync:
            if st.button("🔄 미등록 현장 자동 동기화", use_container_width=True):
                sync_ok, sync_msg = sync_sites_to_monthly_summary()
                if sync_ok:
                    st.success(sync_msg)
                    st.rerun()
                else:
                    st.error(sync_msg)
        with col_sync_info:
            st.info("관리자 모드에 등록된 현장 중 월별 집계에 없는 현장을 자동으로 추가합니다. (예산은 0으로 설정되며, 이후 직접 수정 가능)")
        
        st.divider()
        
        st.markdown("#### 새 현장 추가")
        with st.form("add_summary_site_form", clear_on_submit=True):
            col_add1, col_add2 = st.columns(2)
            with col_add1:
                new_site_company = st.selectbox("법인", options=["미래", "다원"], key="new_summary_company")
                new_site_name = st.text_input("현장명", placeholder="예: 신월시영")
            with col_add2:
                new_uniform_budget = st.number_input("피복 예산", min_value=0, value=0, step=100000, key="new_uniform_budget")
                new_supply_budget = st.number_input("경비물품 예산", min_value=0, value=0, step=100000, key="new_supply_budget")
            
            if st.form_submit_button("현장 추가", type="primary"):
                if new_site_name:
                    success, msg = add_monthly_summary_site(new_site_name, new_site_company, new_uniform_budget, new_supply_budget)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("현장명을 입력해주세요.")
        
        st.divider()
        
        st.markdown("#### 현장 삭제")
        summary_data_for_delete = get_all_monthly_summary()
        df_sites = summary_data_for_delete.get('피복', pd.DataFrame())
        
        if not df_sites.empty:
            site_list = df_sites[['구분', '현장명']].drop_duplicates()
            site_options = [f"{row['구분']} - {row['현장명']}" for _, row in site_list.iterrows()]
            
            col_select, col_btn = st.columns([3, 1])
            with col_select:
                selected_site_to_delete = st.selectbox("삭제할 현장 선택", options=site_options, key="delete_site_select")
            with col_btn:
                st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("현장 삭제", type="secondary", use_container_width=True):
                    if selected_site_to_delete:
                        parts = selected_site_to_delete.split(" - ", 1)
                        del_company = parts[0]
                        del_site = parts[1]
                        confirm_delete_dialog('summary_site', None, f"{del_site} ({del_company})", extra_info={'site': del_site, 'company': del_company})
        else:
            st.info("삭제할 현장이 없습니다.")
        
        st.divider()
        
        st.markdown("#### 예산 수정")
        if not df_sites.empty:
            with st.form("update_budget_form"):
                selected_site_for_budget = st.selectbox("현장 선택", options=site_options, key="budget_site_select")
                budget_type = st.radio("수정 유형", options=["피복", "경비물품"], horizontal=True, key="budget_type_radio")
                new_budget = st.number_input("새 예산", min_value=0, value=0, step=100000, key="new_budget_value")
                
                if st.form_submit_button("예산 수정", type="primary"):
                    if selected_site_for_budget:
                        parts = selected_site_for_budget.split(" - ", 1)
                        budget_company = parts[0]
                        budget_site = parts[1]
                        success, msg = update_monthly_summary_budget(budget_site, budget_company, budget_type, new_budget)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
        else:
            st.info("예산을 수정할 현장이 없습니다.")

elif menu == "관리자 모드":
    st.subheader("관리자 모드")
    st.info("현장 정보와 신청자 정보를 등록하면 신청서 작성 시 자동으로 불러올 수 있습니다.")
    
    if 'edit_site_id' not in st.session_state:
        st.session_state.edit_site_id = None
    if 'edit_applicant_id' not in st.session_state:
        st.session_state.edit_applicant_id = None
    if 'edit_email_id' not in st.session_state:
        st.session_state.edit_email_id = None
    if 'edit_supply_product_id' not in st.session_state:
        st.session_state.edit_supply_product_id = None
    if 'edit_uniform_product_id' not in st.session_state:
        st.session_state.edit_uniform_product_id = None
    
    admin_tab = st.tabs(["현장 관리", "신청자 관리", "수신자 이메일 관리", "경비용품 관리", "피복 품목 관리"])
    
    with admin_tab[0]:
        st.markdown("### 현장 정보 관리")
        
        sites = get_sites()
        
        st.markdown("#### 새 현장 등록")
        with st.form("add_site_form", clear_on_submit=True):
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                new_site_company = st.selectbox("법인", options=["미래", "다원"], key="new_site_company")
                new_site_name = st.text_input("현장명", placeholder="예: 고산센트레빌")
            with col_s2:
                new_site_address = st.text_input("배송지 주소", placeholder="예: 경기도 성남시 중원구 성남대로 1133")
                new_site_contact = st.text_input("현장 연락처 (담당자)", placeholder="예: 010-2211-9352 정봉환 경비팀장")
            
            if st.form_submit_button("현장 등록", type="primary"):
                if new_site_name:
                    add_site(new_site_name, new_site_company, new_site_address, new_site_contact)
                    add_monthly_summary_site(new_site_name, new_site_company, 0, 0)
                    st.success(f"'{new_site_name}' 현장이 등록되었습니다. (월별 집계에도 자동 추가됨)")
                    st.rerun()
                else:
                    st.error("현장명을 입력해주세요.")
        
        st.markdown("#### 등록된 현장 목록")
        if sites:
            for site in sites:
                with st.expander(f"📍 [{site.get('company', '미래')}] {site['name']}"):
                    if st.session_state.edit_site_id == site['id']:
                        with st.form(f"edit_site_form_{site['id']}"):
                            current_company = site.get('company', '미래')
                            company_options = ["미래", "다원"]
                            edit_company = st.selectbox("법인", options=company_options, index=company_options.index(current_company) if current_company in company_options else 0)
                            edit_name = st.text_input("현장명", value=site['name'])
                            edit_address = st.text_input("배송지 주소", value=site.get('address', ''))
                            edit_contact = st.text_input("현장 연락처", value=site.get('contact', ''))
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("저장", type="primary"):
                                    update_site(site['id'], edit_name, edit_company, edit_address, edit_contact)
                                    st.session_state.edit_site_id = None
                                    st.success("수정되었습니다.")
                                    st.rerun()
                            with col_cancel:
                                if st.form_submit_button("취소"):
                                    st.session_state.edit_site_id = None
                                    st.rerun()
                    else:
                        st.text(f"법인: {site.get('company', '미래')}")
                        st.text(f"주소: {site.get('address', '-')}")
                        st.text(f"연락처: {site.get('contact', '-')}")
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("수정", key=f"edit_site_{site['id']}"):
                                st.session_state.edit_site_id = site['id']
                                st.rerun()
                        with col_btn2:
                            if st.button("삭제", key=f"del_site_{site['id']}", type="secondary"):
                                confirm_delete_dialog('site', site['id'], site['name'])
        else:
            st.info("등록된 현장이 없습니다.")
    
    with admin_tab[1]:
        st.markdown("### 신청자 정보 관리")
        
        applicants_list = get_applicants()
        
        st.markdown("#### 새 신청자 등록")
        with st.form("add_applicant_form", clear_on_submit=True):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                new_applicant_name = st.text_input("신청자명", placeholder="예: 김솔휘 대리")
            with col_a2:
                new_applicant_contact = st.text_input("연락처", placeholder="예: 010-5089-3105")
            
            if st.form_submit_button("신청자 등록", type="primary"):
                if new_applicant_name:
                    add_applicant(new_applicant_name, new_applicant_contact)
                    st.success(f"'{new_applicant_name}' 신청자가 등록되었습니다.")
                    st.rerun()
                else:
                    st.error("신청자명을 입력해주세요.")
        
        st.markdown("#### 등록된 신청자 목록")
        if applicants_list:
            for app in applicants_list:
                with st.expander(f"👤 {app['name']}"):
                    if st.session_state.edit_applicant_id == app['id']:
                        with st.form(f"edit_app_form_{app['id']}"):
                            edit_app_name = st.text_input("신청자명", value=app['name'])
                            edit_app_contact = st.text_input("연락처", value=app.get('contact', ''))
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("저장", type="primary"):
                                    update_applicant(app['id'], edit_app_name, edit_app_contact)
                                    st.session_state.edit_applicant_id = None
                                    st.success("수정되었습니다.")
                                    st.rerun()
                            with col_cancel:
                                if st.form_submit_button("취소"):
                                    st.session_state.edit_applicant_id = None
                                    st.rerun()
                    else:
                        st.text(f"연락처: {app.get('contact', '-')}")
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("수정", key=f"edit_app_{app['id']}"):
                                st.session_state.edit_applicant_id = app['id']
                                st.rerun()
                        with col_btn2:
                            if st.button("삭제", key=f"del_app_{app['id']}", type="secondary"):
                                confirm_delete_dialog('applicant', app['id'], app['name'])
        else:
            st.info("등록된 신청자가 없습니다.")
    
    with admin_tab[2]:
        st.markdown("### 수신자 이메일 관리")
        st.caption("신청서 이메일 발송 시 사용할 수신자 목록입니다.")
        
        email_recipients = get_email_recipients()
        
        st.markdown("#### 새 수신자 등록")
        with st.form("add_email_form", clear_on_submit=True):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                new_company_name = st.text_input("업체명", placeholder="예: 경원피복, 제이누리")
            with col_e2:
                new_email = st.text_input("이메일", placeholder="예: example@email.com")
            
            if st.form_submit_button("수신자 등록", type="primary"):
                if new_company_name and new_email:
                    add_email_recipient(new_company_name, new_email)
                    st.success(f"'{new_company_name}' 수신자가 등록되었습니다.")
                    st.rerun()
                else:
                    st.error("업체명과 이메일을 모두 입력해주세요.")
        
        st.markdown("#### 등록된 수신자 목록")
        if email_recipients:
            for recipient in email_recipients:
                with st.expander(f"📧 {recipient['company_name']}"):
                    if st.session_state.edit_email_id == recipient['id']:
                        with st.form(f"edit_email_form_{recipient['id']}"):
                            edit_company = st.text_input("업체명", value=recipient['company_name'])
                            edit_email = st.text_input("이메일", value=recipient.get('email', ''))
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("저장", type="primary"):
                                    update_email_recipient(recipient['id'], edit_company, edit_email)
                                    st.session_state.edit_email_id = None
                                    st.success("수정되었습니다.")
                                    st.rerun()
                            with col_cancel:
                                if st.form_submit_button("취소"):
                                    st.session_state.edit_email_id = None
                                    st.rerun()
                    else:
                        st.text(f"이메일: {recipient.get('email', '-')}")
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("수정", key=f"edit_email_{recipient['id']}"):
                                st.session_state.edit_email_id = recipient['id']
                                st.rerun()
                        with col_btn2:
                            if st.button("삭제", key=f"del_email_{recipient['id']}", type="secondary"):
                                confirm_delete_dialog('email', recipient['id'], recipient['company_name'])
        else:
            st.info("등록된 수신자가 없습니다.")
    
    with admin_tab[3]:
        st.markdown("### 경비용품 품목 관리")
        st.caption("경비물품 신청 시 사용할 품목과 단가를 등록합니다.")
        
        supply_products = get_supply_products()
        
        st.markdown("#### 새 경비용품 등록")
        with st.form("add_supply_form", clear_on_submit=True):
            col_sp1, col_sp2, col_sp3 = st.columns([2, 2, 1])
            with col_sp1:
                new_supply_name = st.text_input("품목명", placeholder="예: 경광봉")
            with col_sp2:
                new_supply_spec = st.text_input("규격/사양", placeholder="예: 적색/녹색")
            with col_sp3:
                new_supply_price = st.number_input("단가(원)", min_value=0, step=100, value=0)
            
            if st.form_submit_button("품목 등록", type="primary"):
                if new_supply_name:
                    add_supply_product(new_supply_name, new_supply_spec, new_supply_price)
                    st.success(f"'{new_supply_name}' 품목이 등록되었습니다.")
                    st.rerun()
                else:
                    st.error("품목명을 입력해주세요.")
        
        st.markdown("#### 등록된 경비용품 목록")
        if supply_products:
            for prod in supply_products:
                with st.expander(f"📦 {prod['name']} - {prod.get('spec', '')} ({prod.get('unit_price', 0):,}원)"):
                    if st.session_state.edit_supply_product_id == prod['id']:
                        with st.form(f"edit_supply_form_{prod['id']}"):
                            edit_sp_name = st.text_input("품목명", value=prod['name'])
                            edit_sp_spec = st.text_input("규격/사양", value=prod.get('spec', ''))
                            edit_sp_price = st.number_input("단가(원)", min_value=0, step=100, value=prod.get('unit_price', 0))
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("저장", type="primary"):
                                    update_supply_product(prod['id'], edit_sp_name, edit_sp_spec, edit_sp_price)
                                    st.session_state.edit_supply_product_id = None
                                    st.success("수정되었습니다.")
                                    st.rerun()
                            with col_cancel:
                                if st.form_submit_button("취소"):
                                    st.session_state.edit_supply_product_id = None
                                    st.rerun()
                    else:
                        st.text(f"규격: {prod.get('spec', '-')}")
                        st.text(f"단가: {prod.get('unit_price', 0):,}원")
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("수정", key=f"edit_supply_{prod['id']}"):
                                st.session_state.edit_supply_product_id = prod['id']
                                st.rerun()
                        with col_btn2:
                            if st.button("삭제", key=f"del_supply_{prod['id']}", type="secondary"):
                                confirm_delete_dialog('supply', prod['id'], prod['name'])
        else:
            st.info("등록된 경비용품이 없습니다.")
    
    with admin_tab[4]:
        st.markdown("### 피복 품목 관리")
        st.caption("피복 신청 시 사용할 품목과 단가를 등록합니다.")
        
        uniform_products = get_uniform_products()
        
        st.markdown("#### 새 피복 품목 등록")
        with st.form("add_uniform_form", clear_on_submit=True):
            col_up1, col_up2 = st.columns([2, 1])
            with col_up1:
                new_uniform_name = st.text_input("품목명", placeholder="예: 동복 상의")
            with col_up2:
                new_uniform_price = st.number_input("단가(원)", min_value=0, step=100, value=0)
            
            if st.form_submit_button("품목 등록", type="primary"):
                if new_uniform_name:
                    add_uniform_product(new_uniform_name, new_uniform_price)
                    st.success(f"'{new_uniform_name}' 품목이 등록되었습니다.")
                    st.rerun()
                else:
                    st.error("품목명을 입력해주세요.")
        
        st.markdown("#### 등록된 피복 품목 목록")
        if uniform_products:
            for prod in uniform_products:
                with st.expander(f"👔 {prod['name']} ({prod.get('unit_price', 0):,}원)"):
                    if st.session_state.edit_uniform_product_id == prod['id']:
                        with st.form(f"edit_uniform_form_{prod['id']}"):
                            edit_up_name = st.text_input("품목명", value=prod['name'])
                            edit_up_price = st.number_input("단가(원)", min_value=0, step=100, value=prod.get('unit_price', 0))
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("저장", type="primary"):
                                    update_uniform_product(prod['id'], edit_up_name, edit_up_price)
                                    st.session_state.edit_uniform_product_id = None
                                    st.success("수정되었습니다.")
                                    st.rerun()
                            with col_cancel:
                                if st.form_submit_button("취소"):
                                    st.session_state.edit_uniform_product_id = None
                                    st.rerun()
                    else:
                        st.text(f"단가: {prod.get('unit_price', 0):,}원")
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("수정", key=f"edit_uniform_{prod['id']}"):
                                st.session_state.edit_uniform_product_id = prod['id']
                                st.rerun()
                        with col_btn2:
                            if st.button("삭제", key=f"del_uniform_{prod['id']}", type="secondary"):
                                confirm_delete_dialog('uniform', prod['id'], prod['name'])
        else:
            st.info("등록된 피복 품목이 없습니다.")

st.sidebar.divider()
st.sidebar.caption("ⓒ 2026 경비용품 및 피복 관리시스템")
