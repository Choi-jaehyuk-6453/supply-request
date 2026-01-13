import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

from pdf_generator import generate_pdf
from email_sender import send_application_email, get_default_email
from excel_handler import append_to_master, get_master_data, get_monthly_summary, initialize_excel

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
        options=["신청서 작성", "데이터 조회", "월별 집계"],
        index=0
    )

st.markdown('<p class="main-header">경비용품 및 피복 신청 관리 시스템</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-header">현재 선택: {company} ABM / {app_type} 신청</p>', unsafe_allow_html=True)

if menu == "신청서 작성":
    
    st.subheader("기본 정보 입력")
    
    col1, col2 = st.columns(2)
    
    with col1:
        application_date = st.date_input(
            "신청일",
            value=date.today(),
            format="YYYY-MM-DD"
        )
        
        site_name = st.text_input(
            "현장명",
            placeholder="예: 고산센트레빌, 성남메트로칸"
        )
        
        applicant = st.text_input(
            "신청자",
            placeholder="예: 김솔휘 대리"
        )
    
    with col2:
        applicant_contact = st.text_input(
            "신청자 연락처",
            placeholder="예: 010-5089-3105"
        )
        
        address = st.text_input(
            "배송지 주소",
            placeholder="예: 경기도 성남시 중원구 성남대로 1133"
        )
        
        contact = st.text_input(
            "현장 연락처 (담당자)",
            placeholder="예: 010-2211-9352 정봉환 경비팀장"
        )
    
    st.divider()
    
    st.subheader("품목 입력")
    
    if app_type == "경비물품":
        st.info("경비물품을 추가해주세요. 행을 추가하려면 표 하단의 + 버튼을 클릭하세요.")
        
        if 'supplies_items' not in st.session_state:
            st.session_state.supplies_items = pd.DataFrame({
                '품목명': [''],
                '규격(옵션)': [''],
                '수량': [1],
                '단가': [0]
            })
        
        edited_supplies = st.data_editor(
            st.session_state.supplies_items,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                '품목명': st.column_config.TextColumn('품목명', required=True),
                '규격(옵션)': st.column_config.TextColumn('규격(옵션)'),
                '수량': st.column_config.NumberColumn('수량', min_value=1, default=1),
                '단가': st.column_config.NumberColumn('단가', min_value=0, default=0, format="₩%d")
            }
        )
        
        st.session_state.supplies_items = edited_supplies
        
        if not edited_supplies.empty:
            edited_supplies['합계'] = edited_supplies['수량'] * edited_supplies['단가']
            total_amount = edited_supplies['합계'].sum()
            st.metric("총 합계 금액", f"₩{total_amount:,.0f}")
    
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
                                'spec': row['규격(옵션)'],
                                'quantity': int(row['수량']),
                                'unit_price': int(row['단가'])
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

st.sidebar.divider()
st.sidebar.caption("© 2026 건물관리 시스템")
