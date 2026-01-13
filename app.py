import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

from pdf_generator import generate_pdf
from email_sender import send_application_email, get_default_email
from excel_handler import append_to_master, get_master_data, get_monthly_summary, initialize_excel
from reference_data import (
    get_sites, get_applicants, add_site, update_site, delete_site,
    add_applicant, update_applicant, delete_applicant, get_site_by_name, get_applicant_by_name
)

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

with st.sidebar:
    st.header("설정")
    
    company = st.selectbox(
        "법인명",
        options=["미래", "다원"],
        index=0
    )
    
    app_type = st.selectbox(
        "신청 유형",
        options=["경비물품", "피복"],
        index=0
    )
    
    st.divider()
    
    menu = st.radio(
        "메뉴",
        options=["신청서 작성", "데이터 조회", "월별 집계", "관리자 모드"],
        index=0
    )

st.markdown('<p class="main-header">경비용품 및 피복 신청 관리 시스템</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-header">현재 선택: {company} ABM / {app_type} 신청</p>', unsafe_allow_html=True)

if menu == "신청서 작성":
    
    st.subheader("기본 정보 입력")
    
    sites = get_sites()
    applicants_list = get_applicants()
    
    site_names = ["직접 입력"] + [s["name"] for s in sites]
    applicant_names = ["직접 입력"] + [a["name"] for a in applicants_list]
    
    site_info = None
    applicant_info = None
    
    col1, col2 = st.columns(2)
    
    with col1:
        application_date = st.date_input(
            "신청일",
            value=date.today(),
            format="YYYY-MM-DD"
        )
        
        selected_site = st.selectbox(
            "현장명 선택",
            options=site_names,
            index=0,
            help="등록된 현장을 선택하거나 '직접 입력'을 선택하세요"
        )
        
        if selected_site == "직접 입력":
            site_name = st.text_input(
                "현장명",
                placeholder="예: 고산센트레빌, 성남메트로칸",
                key="manual_site"
            )
        else:
            site_name = selected_site
            site_info = get_site_by_name(selected_site)
        
        selected_applicant = st.selectbox(
            "신청자 선택",
            options=applicant_names,
            index=0,
            help="등록된 신청자를 선택하거나 '직접 입력'을 선택하세요"
        )
        
        if selected_applicant == "직접 입력":
            applicant = st.text_input(
                "신청자",
                placeholder="예: 김솔휘 대리",
                key="manual_applicant"
            )
        else:
            applicant = selected_applicant
            applicant_info = get_applicant_by_name(selected_applicant)
    
    with col2:
        if applicant_info:
            default_applicant_contact = applicant_info.get("contact", "")
        else:
            default_applicant_contact = ""
        
        applicant_contact = st.text_input(
            "신청자 연락처",
            value=default_applicant_contact,
            placeholder="예: 010-5089-3105"
        )
        
        if site_info:
            default_address = site_info.get("address", "")
            default_contact = site_info.get("contact", "")
        else:
            default_address = ""
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
        st.info("경비물품을 입력해주세요.")
        
        if 'supplies_items' not in st.session_state:
            st.session_state.supplies_items = [
                {'품목명': '', '규격': '', '수량': 1}
            ]
        
        col_add_sup, col_del_sup = st.columns([1, 5])
        with col_add_sup:
            if st.button("➕ 행 추가", use_container_width=True, key="add_supply"):
                st.session_state.supplies_items.append({'품목명': '', '규격': '', '수량': 1})
                st.rerun()
        
        supplies_to_delete = []
        for idx, item in enumerate(st.session_state.supplies_items):
            with st.container():
                cols = st.columns([0.5, 3, 2, 1, 0.5])
                with cols[0]:
                    st.write(f"**{idx+1}**")
                with cols[1]:
                    item['품목명'] = st.text_input('품목명', value=item.get('품목명', ''), key=f"sup_name_{idx}", label_visibility="collapsed", placeholder="품목명 입력")
                with cols[2]:
                    item['규격'] = st.text_input('규격', value=item.get('규격', ''), key=f"sup_spec_{idx}", label_visibility="collapsed", placeholder="규격/옵션")
                with cols[3]:
                    item['수량'] = st.number_input('수량', value=item.get('수량', 1), min_value=1, key=f"sup_qty_{idx}", label_visibility="collapsed")
                with cols[4]:
                    if st.button("🗑️", key=f"del_sup_{idx}"):
                        supplies_to_delete.append(idx)
        
        if supplies_to_delete:
            for idx in sorted(supplies_to_delete, reverse=True):
                st.session_state.supplies_items.pop(idx)
            st.rerun()
        
        st.markdown("**No | 품목명 | 규격 | 수량**", help="각 항목을 입력하세요")
        
        edited_supplies = pd.DataFrame(st.session_state.supplies_items)
    
    else:
        st.info("피복 신청 품목을 입력해주세요.")
        
        top_sizes = ['이하', '90', '95', '100', '105', '110', '115', '120', '이상']
        bottom_sizes = ['이하', '28', '30', '32', '34', '36', '38', '40', '42', '이상']
        hat_sizes = ['대', '중', '소']
        
        if 'uniform_items' not in st.session_state:
            st.session_state.uniform_items = [
                {'업종': '경비직', '직책': '경비원', '근무자': '', '상의': '100', '하의': '32', '모자': '중', '품목': '회색동복'}
            ]
        
        col_add, col_del = st.columns([1, 5])
        with col_add:
            if st.button("➕ 행 추가", use_container_width=True):
                st.session_state.uniform_items.append(
                    {'업종': '경비직', '직책': '경비원', '근무자': '', '상의': '100', '하의': '32', '모자': '중', '품목': '회색동복'}
                )
                st.rerun()
        
        items_to_delete = []
        for idx, item in enumerate(st.session_state.uniform_items):
            with st.container():
                cols = st.columns([0.5, 1, 1, 1.5, 1, 1, 1, 2, 0.5])
                with cols[0]:
                    st.write(f"**{idx+1}**")
                with cols[1]:
                    item['업종'] = st.selectbox('업종', ['관리직', '경비직'], index=['관리직', '경비직'].index(item.get('업종', '경비직')), key=f"job_{idx}", label_visibility="collapsed")
                with cols[2]:
                    item['직책'] = st.text_input('직책', value=item.get('직책', '경비원'), key=f"pos_{idx}", label_visibility="collapsed")
                with cols[3]:
                    item['근무자'] = st.text_input('근무자', value=item.get('근무자', ''), key=f"worker_{idx}", label_visibility="collapsed", placeholder="이름 입력")
                with cols[4]:
                    item['상의'] = st.selectbox('상의', top_sizes, index=top_sizes.index(item.get('상의', '100')) if item.get('상의', '100') in top_sizes else 3, key=f"top_{idx}", label_visibility="collapsed")
                with cols[5]:
                    item['하의'] = st.selectbox('하의', bottom_sizes, index=bottom_sizes.index(item.get('하의', '32')) if item.get('하의', '32') in bottom_sizes else 3, key=f"bot_{idx}", label_visibility="collapsed")
                with cols[6]:
                    item['모자'] = st.selectbox('모자', hat_sizes, index=hat_sizes.index(item.get('모자', '중')) if item.get('모자', '중') in hat_sizes else 1, key=f"hat_{idx}", label_visibility="collapsed")
                with cols[7]:
                    item['품목'] = st.text_input('품목', value=item.get('품목', '회색동복'), key=f"prod_{idx}", label_visibility="collapsed", placeholder="품목 입력")
                with cols[8]:
                    if st.button("🗑️", key=f"del_{idx}"):
                        items_to_delete.append(idx)
        
        if items_to_delete:
            for idx in sorted(items_to_delete, reverse=True):
                st.session_state.uniform_items.pop(idx)
            st.rerun()
        
        st.markdown("**업종 | 직책 | 근무자 | 상의 | 하의 | 모자 | 품목**", help="각 항목을 입력하세요")
        
        edited_uniform = pd.DataFrame(st.session_state.uniform_items)
    
    remarks = st.text_area(
        "비고 / 참고사항",
        placeholder="추가 참고사항을 입력하세요"
    )
    
    st.divider()
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
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
                    for _, row in edited_supplies.iterrows():
                        if row['품목명']:
                            items.append({
                                'name': row['품목명'],
                                'spec': row.get('규격', ''),
                                'quantity': int(row['수량'])
                            })
                    form_data['items'] = items
                else:
                    items = []
                    for _, row in edited_uniform.iterrows():
                        if row['품목']:
                            items.append({
                                'job_type': row['업종'],
                                'position': row['직책'],
                                'worker': row['근무자'],
                                'top_size': row['상의'],
                                'bottom_size': row['하의'],
                                'hat_size': row['모자'],
                                'product': row['품목']
                            })
                    form_data['items'] = items
                
                try:
                    pdf_path = generate_pdf(form_data, app_type)
                    st.session_state.pdf_generated = True
                    st.session_state.pdf_path = pdf_path
                    st.session_state.form_data = form_data
                    st.session_state.items = items
                    st.success(f"PDF가 생성되었습니다: {os.path.basename(pdf_path)}")
                except Exception as e:
                    st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
    
    with col_btn2:
        if st.button("데이터 저장 (엑셀)", use_container_width=True):
            if st.session_state.form_data and st.session_state.get('items'):
                success, message = append_to_master(
                    st.session_state.form_data,
                    app_type,
                    st.session_state.items
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.warning("먼저 신청서를 생성해주세요.")
    
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
                smtp_email = st.secrets.get("SMTP_EMAIL", "")
                smtp_password = st.secrets.get("SMTP_PASSWORD", "")
            except Exception:
                smtp_email = ""
                smtp_password = ""
            
            if not smtp_email or not smtp_password:
                st.warning("SMTP 설정이 필요합니다. Secrets에 SMTP_EMAIL과 SMTP_PASSWORD를 설정해주세요.")
            
            default_email = get_default_email(app_type)
            
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
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            companies = ['전체'] + df['법인명'].dropna().unique().tolist()
            selected_company = st.selectbox("법인명 필터", companies)
        
        with col_filter2:
            types = ['전체'] + df['구분'].dropna().unique().tolist()
            selected_type = st.selectbox("구분 필터", types)
        
        filtered_df = df.copy()
        if selected_company != '전체':
            filtered_df = filtered_df[filtered_df['법인명'] == selected_company]
        if selected_type != '전체':
            filtered_df = filtered_df[filtered_df['구분'] == selected_type]
        
        st.dataframe(filtered_df, use_container_width=True)
        
        if not filtered_df.empty:
            total = filtered_df['합계금액'].sum()
            st.metric("조회 결과 총액", f"₩{total:,.0f}")
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
    
    admin_tab = st.tabs(["현장 관리", "신청자 관리"])
    
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
                    col_e1, col_e2, col_e3 = st.columns([2, 2, 1])
                    with col_e1:
                        st.text(f"주소: {site.get('address', '-')}")
                    with col_e2:
                        st.text(f"연락처: {site.get('contact', '-')}")
                    with col_e3:
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
                    col_ap1, col_ap2 = st.columns([3, 1])
                    with col_ap1:
                        st.text(f"연락처: {app.get('contact', '-')}")
                    with col_ap2:
                        if st.button("삭제", key=f"del_app_{app['id']}", type="secondary"):
                            delete_applicant(app['id'])
                            st.success(f"'{app['name']}' 신청자가 삭제되었습니다.")
                            st.rerun()
        else:
            st.info("등록된 신청자가 없습니다.")

st.sidebar.divider()
st.sidebar.caption("© 2026 건물관리 시스템")
