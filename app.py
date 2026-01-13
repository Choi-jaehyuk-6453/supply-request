import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

from pdf_generator import generate_pdf
from email_sender import send_application_email, get_default_email
from excel_handler import append_to_master, get_master_data, get_monthly_summary, initialize_excel
from reference_data import (
    get_sites, get_applicants, add_site, update_site, delete_site,
    add_applicant, update_applicant, delete_applicant, get_site_by_name, get_applicant_by_name,
    add_email_recipient, update_email_recipient, delete_email_recipient, get_email_recipients,
    get_supply_products, add_supply_product, update_supply_product, delete_supply_product, get_supply_product_by_name,
    get_uniform_products, add_uniform_product, update_uniform_product, delete_uniform_product, get_uniform_product_by_name
)
from draft_manager import save_draft, get_draft, delete_draft, get_draft_list, update_draft

st.set_page_config(
    page_title="경비용품 및 피복 신청 관리 시스템",
    page_icon="📋",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f4e79;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
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
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "신청서 작성"
if 'selected_company' not in st.session_state:
    st.session_state.selected_company = "미래"
if 'selected_app_type' not in st.session_state:
    st.session_state.selected_app_type = "경비물품"

menu_options = ["신청서 작성", "데이터 조회", "월별 집계", "관리자 모드"]
company_options = ["미래", "다원"]
app_type_options = ["경비물품", "피복"]

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
                            if loaded.get('app_type') == '경비물품':
                                st.session_state.supplies_items = loaded.get('items', [])
                            else:
                                st.session_state.uniform_items = loaded.get('items', [])
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
                        delete_draft(draft['id'])
                        st.success("삭제되었습니다.")
                        st.rerun()
    
    draft_meta = st.session_state.draft_metadata
    if draft_meta:
        st.info(f"📂 임시저장 데이터를 불러왔습니다: {draft_meta.get('site_name', '')}")
    
    st.subheader("기본 정보 입력")
    
    sites = get_sites()
    applicants_list = get_applicants()
    
    site_names = ["직접 입력"] + [s["name"] for s in sites]
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
        
        selected_site = st.selectbox(
            "현장명 선택",
            options=site_names,
            index=site_index,
            help="등록된 현장을 선택하거나 '직접 입력'을 선택하세요"
        )
        
        if selected_site == "직접 입력":
            default_site_value = draft_site_name if draft_meta else ''
            site_name = st.text_input(
                "현장명",
                value=default_site_value,
                placeholder="예: 고산센트레빌, 성남메트로칸",
                key="manual_site"
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
            help="등록된 신청자를 선택하거나 '직접 입력'을 선택하세요"
        )
        
        if selected_applicant == "직접 입력":
            default_applicant_value = draft_applicant if draft_meta else ''
            applicant = st.text_input(
                "신청자",
                value=default_applicant_value,
                placeholder="예: 김솔휘 대리",
                key="manual_applicant"
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
    
    st.divider()
    
    st.subheader("품목 입력")
    
    if app_type == "경비물품":
        st.info("경비물품을 입력해주세요. 등록된 품목을 선택하면 단가가 자동으로 입력됩니다.")
        
        supply_product_list = get_supply_products()
        supply_options = ["직접 입력"] + [p['name'] for p in supply_product_list]
        
        if 'supplies_items' not in st.session_state:
            st.session_state.supplies_items = [
                {'품목명': '', '규격': '', '수량': 1, '단가': 0, '금액': 0}
            ]
        
        col_add_sup, col_del_sup = st.columns([1, 5])
        with col_add_sup:
            if st.button("➕ 행 추가", use_container_width=True, key="add_supply"):
                st.session_state.supplies_items.append({'품목명': '', '규격': '', '수량': 1, '단가': 0, '금액': 0})
                st.rerun()
        
        st.markdown("**No | 품목 선택 | 규격 | 수량 | 단가 | 금액 | 삭제**")
        
        supplies_to_delete = []
        total_supply_amount = 0
        for idx, item in enumerate(st.session_state.supplies_items):
            with st.container():
                cols = st.columns([0.4, 2.5, 1.5, 0.8, 1.2, 1.2, 0.4])
                with cols[0]:
                    st.write(f"**{idx+1}**")
                with cols[1]:
                    current_product = item.get('품목명', '')
                    if current_product in supply_options:
                        default_idx = supply_options.index(current_product)
                    else:
                        default_idx = 0
                    selected = st.selectbox('품목', supply_options, index=default_idx, key=f"sup_select_{idx}", label_visibility="collapsed")
                    
                    if selected == "직접 입력":
                        item['품목명'] = st.text_input('품목명', value=item.get('품목명', '') if item.get('품목명', '') not in supply_options else '', key=f"sup_name_{idx}", label_visibility="collapsed", placeholder="품목명 입력")
                    else:
                        item['품목명'] = selected
                        product_info = get_supply_product_by_name(selected)
                        if product_info:
                            item['단가'] = product_info.get('unit_price', 0)
                            if product_info.get('spec'):
                                item['규격'] = product_info.get('spec', '')
                with cols[2]:
                    item['규격'] = st.text_input('규격', value=item.get('규격', ''), key=f"sup_spec_{idx}", label_visibility="collapsed", placeholder="규격/옵션")
                with cols[3]:
                    item['수량'] = st.number_input('수량', value=item.get('수량', 1), min_value=1, key=f"sup_qty_{idx}", label_visibility="collapsed")
                with cols[4]:
                    item['단가'] = st.number_input('단가', value=item.get('단가', 0), min_value=0, step=100, key=f"sup_price_{idx}", label_visibility="collapsed")
                with cols[5]:
                    item['금액'] = item['수량'] * item['단가']
                    st.write(f"{item['금액']:,}원")
                    total_supply_amount += item['금액']
                with cols[6]:
                    if st.button("🗑️", key=f"del_sup_{idx}"):
                        supplies_to_delete.append(idx)
        
        if supplies_to_delete:
            for idx in sorted(supplies_to_delete, reverse=True):
                st.session_state.supplies_items.pop(idx)
            st.rerun()
        
        st.markdown(f"**합계: {total_supply_amount:,}원**")
        
        edited_supplies = pd.DataFrame(st.session_state.supplies_items)
    
    else:
        st.info("피복 신청 품목을 입력해주세요. 등록된 품목을 선택하면 단가가 자동으로 입력됩니다.")
        
        uniform_product_list = get_uniform_products()
        uniform_options = ["직접 입력"] + [p['name'] for p in uniform_product_list]
        
        top_sizes = ['이하', '90', '95', '100', '105', '110', '115', '120', '이상']
        bottom_sizes = ['이하', '28', '30', '32', '34', '36', '38', '40', '42', '이상']
        hat_sizes = ['대', '중', '소']
        
        if 'uniform_items' not in st.session_state:
            st.session_state.uniform_items = [
                {'업종': '경비직', '직책': '경비원', '근무자': '', '상의': '100', '하의': '32', '모자': '중', '품목': '회색동복', '수량': 1, '단가': 0, '금액': 0}
            ]
        
        col_add, col_del = st.columns([1, 5])
        with col_add:
            if st.button("➕ 행 추가", use_container_width=True):
                st.session_state.uniform_items.append(
                    {'업종': '경비직', '직책': '경비원', '근무자': '', '상의': '100', '하의': '32', '모자': '중', '품목': '회색동복', '수량': 1, '단가': 0, '금액': 0}
                )
                st.rerun()
        
        st.markdown("**No | 업종 | 직책 | 근무자 | 상의 | 하의 | 모자 | 품목 | 수량 | 단가 | 금액 | 삭제**")
        
        items_to_delete = []
        total_uniform_amount = 0
        for idx, item in enumerate(st.session_state.uniform_items):
            with st.container():
                cols = st.columns([0.35, 0.7, 0.7, 1.1, 0.6, 0.6, 0.5, 1.8, 0.6, 0.9, 0.9, 0.35])
                with cols[0]:
                    st.write(f"**{idx+1}**")
                with cols[1]:
                    item['업종'] = st.selectbox('업종', ['관리직', '경비직'], index=['관리직', '경비직'].index(item.get('업종', '경비직')), key=f"job_{idx}", label_visibility="collapsed")
                with cols[2]:
                    item['직책'] = st.text_input('직책', value=item.get('직책', '경비원'), key=f"pos_{idx}", label_visibility="collapsed")
                with cols[3]:
                    item['근무자'] = st.text_input('근무자', value=item.get('근무자', ''), key=f"worker_{idx}", label_visibility="collapsed", placeholder="이름")
                with cols[4]:
                    item['상의'] = st.selectbox('상의', top_sizes, index=top_sizes.index(item.get('상의', '100')) if item.get('상의', '100') in top_sizes else 3, key=f"top_{idx}", label_visibility="collapsed")
                with cols[5]:
                    item['하의'] = st.selectbox('하의', bottom_sizes, index=bottom_sizes.index(item.get('하의', '32')) if item.get('하의', '32') in bottom_sizes else 3, key=f"bot_{idx}", label_visibility="collapsed")
                with cols[6]:
                    item['모자'] = st.selectbox('모자', hat_sizes, index=hat_sizes.index(item.get('모자', '중')) if item.get('모자', '중') in hat_sizes else 1, key=f"hat_{idx}", label_visibility="collapsed")
                with cols[7]:
                    current_uniform = item.get('품목', '')
                    if current_uniform in uniform_options:
                        default_uniform_idx = uniform_options.index(current_uniform)
                    else:
                        default_uniform_idx = 0
                    selected_uniform = st.selectbox('품목', uniform_options, index=default_uniform_idx, key=f"unif_select_{idx}", label_visibility="collapsed")
                    
                    if selected_uniform == "직접 입력":
                        item['품목'] = st.text_input('품목명', value=item.get('품목', '') if item.get('품목', '') not in uniform_options else '', key=f"prod_{idx}", label_visibility="collapsed", placeholder="품목 입력")
                    else:
                        item['품목'] = selected_uniform
                        uniform_info = get_uniform_product_by_name(selected_uniform)
                        if uniform_info:
                            item['단가'] = uniform_info.get('unit_price', 0)
                with cols[8]:
                    item['수량'] = st.number_input('수량', value=item.get('수량', 1), min_value=1, key=f"unif_qty_{idx}", label_visibility="collapsed")
                with cols[9]:
                    item['단가'] = st.number_input('단가', value=item.get('단가', 0), min_value=0, step=100, key=f"unif_price_{idx}", label_visibility="collapsed")
                with cols[10]:
                    item['금액'] = item['수량'] * item['단가']
                    st.write(f"{item['금액']:,}원")
                    total_uniform_amount += item['금액']
                with cols[11]:
                    if st.button("🗑️", key=f"del_{idx}"):
                        items_to_delete.append(idx)
        
        if items_to_delete:
            for idx in sorted(items_to_delete, reverse=True):
                st.session_state.uniform_items.pop(idx)
            st.rerun()
        
        st.markdown(f"**합계: {total_uniform_amount:,}원**")
        
        edited_uniform = pd.DataFrame(st.session_state.uniform_items)
    
    default_remarks = draft_meta.get('remarks', '') if draft_meta else ''
    remarks = st.text_area(
        "비고 / 참고사항",
        value=default_remarks,
        placeholder="추가 참고사항을 입력하세요"
    )
    
    st.divider()
    
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
                            unit_price = int(row.get('단가', 0))
                            quantity = int(row['수량'])
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
                        if row['품목']:
                            unit_price = int(row.get('단가', 0))
                            quantity = int(row.get('수량', 1))
                            amount = unit_price * quantity
                            total_amount += amount
                            items.append({
                                'job_type': row['업종'],
                                'position': row['직책'],
                                'worker': row['근무자'],
                                'top_size': row['상의'],
                                'bottom_size': row['하의'],
                                'hat_size': row['모자'],
                                'product': row['품목'],
                                'quantity': quantity,
                                'unit_price': unit_price,
                                'amount': amount
                            })
                    form_data['items'] = items
                    form_data['total_amount'] = total_amount
                
                try:
                    pdf_path = generate_pdf(form_data, app_type)
                    st.session_state.pdf_generated = True
                    st.session_state.pdf_path = pdf_path
                    st.session_state.form_data = form_data
                    st.session_state.items = items
                    
                    success, message = append_to_master(form_data, app_type, items)
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
            st.session_state.loaded_draft_id = None
            st.session_state.pdf_generated = False
            st.session_state.pdf_path = None
            st.session_state.form_data = None
            st.session_state.draft_metadata = None
            if 'supplies_items' in st.session_state:
                del st.session_state.supplies_items
            if 'uniform_items' in st.session_state:
                del st.session_state.uniform_items
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

elif menu == "데이터 조회":
    st.subheader("신청 내역 조회")
    
    initialize_excel()
    df = get_master_data()
    
    if not df.empty:
        df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        
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
            grouped = filtered_df.groupby(['날짜', '법인명', '현장명', '신청자', '구분']).agg({
                '품목명': lambda x: ', '.join(x.astype(str).unique()),
                '합계금액': 'sum'
            }).reset_index()
            grouped.columns = ['날짜', '법인명', '현장명', '신청자', '구분', '품목', '총액']
            grouped['품목수'] = filtered_df.groupby(['날짜', '법인명', '현장명', '신청자', '구분']).size().values
            
            col_metric1, col_metric2 = st.columns(2)
            with col_metric1:
                st.metric("총 건수", f"{len(grouped)}건")
            with col_metric2:
                unique_sites = filtered_df['현장명'].nunique()
                st.metric("현장 수", f"{unique_sites}개")
            grouped['날짜_str'] = pd.to_datetime(grouped['날짜']).dt.strftime('%Y-%m-%d')
            
            header_cols = st.columns([1.2, 0.8, 1.2, 1, 2, 0.6, 0.4])
            header_cols[0].markdown("**날짜**")
            header_cols[1].markdown("**구분**")
            header_cols[2].markdown("**현장명**")
            header_cols[3].markdown("**신청자**")
            header_cols[4].markdown("**품목**")
            header_cols[5].markdown("**품목수**")
            header_cols[6].markdown("**수정신청**")
            
            st.divider()
            
            for idx, row in grouped.iterrows():
                row_cols = st.columns([1.2, 0.8, 1.2, 1, 2, 0.6, 0.4])
                row_cols[0].write(row['날짜_str'])
                row_cols[1].write(row['구분'])
                row_cols[2].write(row['현장명'])
                row_cols[3].write(row['신청자'])
                row_cols[4].write(row['품목'])
                row_cols[5].write(f"{row['품목수']}개")
                
                btn_key = f"edit_{row['날짜_str']}_{row['현장명']}_{row['신청자']}_{row['구분']}_{idx}"
                if row_cols[6].button("✏️", key=btn_key):
                    display_df_temp = filtered_df.copy()
                    display_df_temp['날짜_str'] = display_df_temp['날짜'].dt.strftime('%Y-%m-%d')
                    
                    app_items = display_df_temp[
                        (display_df_temp['날짜_str'] == row['날짜_str']) & 
                        (display_df_temp['현장명'] == row['현장명']) & 
                        (display_df_temp['신청자'] == row['신청자']) &
                        (display_df_temp['구분'] == row['구분'])
                    ]
                    
                    if row['구분'] == '경비물품':
                        items_list = []
                        for _, item_row in app_items.iterrows():
                            items_list.append({
                                '품목명': item_row['품목명'],
                                '규격': str(item_row['규격']) if pd.notna(item_row['규격']) else '',
                                '수량': int(item_row['수량'])
                            })
                        st.session_state.supplies_items = items_list
                    else:
                        items_list = []
                        for _, item_row in app_items.iterrows():
                            spec = str(item_row['규격']) if pd.notna(item_row['규격']) else ''
                            top_size = '100'
                            bottom_size = '32'
                            hat_size = '중'
                            
                            if '상의:' in spec:
                                try:
                                    parts = spec.split('/')
                                    for part in parts:
                                        if part.startswith('상의:'):
                                            top_size = part.replace('상의:', '')
                                        elif part.startswith('하의:'):
                                            bottom_size = part.replace('하의:', '')
                                        elif part.startswith('모자:'):
                                            hat_size = part.replace('모자:', '')
                                except:
                                    pass
                            
                            items_list.append({
                                '업종': '경비직',
                                '직책': '경비원',
                                '근무자': '',
                                '상의': top_size,
                                '하의': bottom_size,
                                '모자': hat_size,
                                '품목': item_row['품목명']
                            })
                        st.session_state.uniform_items = items_list
                    
                    st.session_state.draft_metadata = {
                        'site_name': row['현장명'],
                        'applicant': row['신청자'],
                        'applicant_contact': '',
                        'address': '',
                        'contact': '',
                        'remarks': '',
                        'application_date': row['날짜_str']
                    }
                    
                    st.session_state.loaded_draft_id = None
                    st.session_state.pending_menu = "신청서 작성"
                    st.session_state.pending_company = row['법인명']
                    st.session_state.pending_app_type = row['구분']
                    st.rerun()
            
            st.divider()
            
            csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 엑셀 다운로드 (CSV)",
                data=csv,
                file_name=f"신청내역_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("검색 조건에 맞는 데이터가 없습니다.")
    else:
        st.info("저장된 데이터가 없습니다.")

elif menu == "월별 집계":
    st.subheader("월별 비용 집계")
    
    initialize_excel()
    df_summary = get_monthly_summary()
    
    if not df_summary.empty:
        st.dataframe(df_summary, use_container_width=True)
        
        st.divider()
        
        df_master = get_master_data()
        if not df_master.empty:
            df_master['날짜'] = pd.to_datetime(df_master['날짜'], errors='coerce')
            df_master['년월'] = df_master['날짜'].dt.strftime('%Y-%m')
            
            pivot = pd.pivot_table(
                df_master,
                values='합계금액',
                index='현장명',
                columns='년월',
                aggfunc='sum',
                fill_value=0
            )
            
            st.subheader("현장별 월별 집계표")
            st.dataframe(pivot, use_container_width=True)
    else:
        st.info("집계할 데이터가 없습니다.")

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
                new_site_name = st.text_input("현장명", placeholder="예: 고산센트레빌")
                new_site_address = st.text_input("배송지 주소", placeholder="예: 경기도 성남시 중원구 성남대로 1133")
            with col_s2:
                new_site_contact = st.text_input("현장 연락처 (담당자)", placeholder="예: 010-2211-9352 정봉환 경비팀장")
            
            if st.form_submit_button("현장 등록", type="primary"):
                if new_site_name:
                    add_site(new_site_name, new_site_address, new_site_contact)
                    st.success(f"'{new_site_name}' 현장이 등록되었습니다.")
                    st.rerun()
                else:
                    st.error("현장명을 입력해주세요.")
        
        st.markdown("#### 등록된 현장 목록")
        if sites:
            for site in sites:
                with st.expander(f"📍 {site['name']}"):
                    if st.session_state.edit_site_id == site['id']:
                        with st.form(f"edit_site_form_{site['id']}"):
                            edit_name = st.text_input("현장명", value=site['name'])
                            edit_address = st.text_input("배송지 주소", value=site.get('address', ''))
                            edit_contact = st.text_input("현장 연락처", value=site.get('contact', ''))
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("저장", type="primary"):
                                    update_site(site['id'], edit_name, edit_address, edit_contact)
                                    st.session_state.edit_site_id = None
                                    st.success("수정되었습니다.")
                                    st.rerun()
                            with col_cancel:
                                if st.form_submit_button("취소"):
                                    st.session_state.edit_site_id = None
                                    st.rerun()
                    else:
                        st.text(f"주소: {site.get('address', '-')}")
                        st.text(f"연락처: {site.get('contact', '-')}")
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("수정", key=f"edit_site_{site['id']}"):
                                st.session_state.edit_site_id = site['id']
                                st.rerun()
                        with col_btn2:
                            if st.button("삭제", key=f"del_site_{site['id']}", type="secondary"):
                                delete_site(site['id'])
                                st.success(f"'{site['name']}' 현장이 삭제되었습니다.")
                                st.rerun()
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
                                delete_applicant(app['id'])
                                st.success(f"'{app['name']}' 신청자가 삭제되었습니다.")
                                st.rerun()
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
                                delete_email_recipient(recipient['id'])
                                st.success(f"'{recipient['company_name']}' 수신자가 삭제되었습니다.")
                                st.rerun()
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
                                delete_supply_product(prod['id'])
                                st.success(f"'{prod['name']}' 품목이 삭제되었습니다.")
                                st.rerun()
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
                                delete_uniform_product(prod['id'])
                                st.success(f"'{prod['name']}' 품목이 삭제되었습니다.")
                                st.rerun()
        else:
            st.info("등록된 피복 품목이 없습니다.")

st.sidebar.divider()
st.sidebar.caption("© 2026 건물관리 시스템")
