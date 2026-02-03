import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

import subprocess

def find_korean_font():
    """한글 폰트 경로 찾기 - 프로젝트 내 폰트 우선 사용"""
    project_font = os.path.join(os.path.dirname(__file__), 'fonts', 'NanumGothicCoding.ttf')
    if os.path.exists(project_font):
        return project_font
    
    try:
        result = subprocess.run(['fc-list', ':lang=ko'], capture_output=True, text=True, timeout=5)
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'NanumGothicCoding.ttf' in line or 'NanumGothic' in line:
                font_path = line.split(':')[0].strip()
                if os.path.exists(font_path):
                    return font_path
        for line in lines:
            if '.ttf' in line.lower():
                font_path = line.split(':')[0].strip()
                if os.path.exists(font_path):
                    return font_path
    except Exception:
        pass
    
    return None

def find_korean_bold_font():
    """한글 볼드 폰트 경로 찾기 - 프로젝트 내 폰트 우선 사용"""
    project_font = os.path.join(os.path.dirname(__file__), 'fonts', 'NanumGothicCoding-Bold.ttf')
    if os.path.exists(project_font):
        return project_font
    
    try:
        result = subprocess.run(['fc-list', ':lang=ko'], capture_output=True, text=True, timeout=5)
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'Bold' in line and ('NanumGothicCoding' in line or 'NanumGothic' in line):
                font_path = line.split(':')[0].strip()
                if os.path.exists(font_path):
                    return font_path
    except Exception:
        pass
    
    return None

FONT_REGISTERED = False
BOLD_FONT_AVAILABLE = False

def register_korean_fonts():
    global FONT_REGISTERED, BOLD_FONT_AVAILABLE
    if FONT_REGISTERED:
        return
    
    font_path = find_korean_font()
    bold_font_path = find_korean_bold_font()
    
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
        except Exception as e:
            print(f"Font registration error: {e}")
    
    if bold_font_path:
        try:
            pdfmetrics.registerFont(TTFont('NanumGothicBold', bold_font_path))
            BOLD_FONT_AVAILABLE = True
        except Exception as e:
            print(f"Bold font registration error: {e}")
    
    try:
        if BOLD_FONT_AVAILABLE:
            registerFontFamily('NanumGothic', 
                               normal='NanumGothic', 
                               bold='NanumGothicBold',
                               italic='NanumGothic',
                               boldItalic='NanumGothicBold')
        else:
            registerFontFamily('NanumGothic', 
                               normal='NanumGothic', 
                               bold='NanumGothic',
                               italic='NanumGothic',
                               boldItalic='NanumGothic')
    except Exception as e:
        print(f"Font family registration error: {e}")
    
    FONT_REGISTERED = True

register_korean_fonts()

def get_korean_style(name, font_size=10, alignment=TA_LEFT, bold=False, text_color=None):
    if bold and BOLD_FONT_AVAILABLE:
        font_name = 'NanumGothicBold'
    else:
        font_name = 'NanumGothic'
    style = ParagraphStyle(
        name=name,
        fontName=font_name,
        fontSize=font_size,
        leading=font_size * 1.4,
        alignment=alignment,
        wordWrap='CJK'
    )
    if text_color:
        style.textColor = text_color
    return style

def generate_uniform_pdf(data, output_path):
    """피복신청서 PDF 생성"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=10*mm,
        bottomMargin=10*mm
    )
    
    elements = []
    width, height = A4
    
    company = data.get('company', '미래')
    if company == '미래':
        logo_path = "attached_assets/미래ABM_LOGO_1768277050813.png"
        company_name = "㈜미래ABM"
        company_addr = "서울시 강남구 영동대로 708 정화빌딩 603호(우135-761) TEL:02-547-2975 FAX:02-547-2972"
    else:
        logo_path = "attached_assets/다원PMC_LOGO_1768277050810.png"
        company_name = "㈜다원PMC"
        company_addr = "서울시 강남구 영동대로 708 정화빌딩 603호 TEL:02-547-2975 FAX:02-547-2972"
    
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=50*mm, height=15*mm)
        elements.append(logo)
    
    title_style = get_korean_style('Title', 16, TA_CENTER, bold=True)
    elements.append(Paragraph(f"{company_name} 피복신청서", title_style))
    elements.append(Spacer(1, 2*mm))
    
    addr_style = get_korean_style('Addr', 8, TA_CENTER)
    elements.append(Paragraph(company_addr, addr_style))
    elements.append(Spacer(1, 5*mm))
    
    normal_style = get_korean_style('Normal', 10, TA_LEFT)
    bold_style = get_korean_style('Bold', 10, TA_LEFT, bold=True)
    
    vendor_info = "업체명 : 경원피복      Tel. 02-2272-0747    Fax. 02-2272-1119     bbs0747@hanmail.net"
    elements.append(Paragraph(vendor_info, normal_style))
    elements.append(Spacer(1, 5*mm))
    
    items = data.get('items', [])
    
    header = [
        Paragraph('직책', get_korean_style('h', 9, TA_CENTER, bold=True)),
        Paragraph('근무자', get_korean_style('h', 9, TA_CENTER, bold=True)),
        Paragraph('상의', get_korean_style('h', 9, TA_CENTER, bold=True)),
        Paragraph('하의', get_korean_style('h', 9, TA_CENTER, bold=True)),
        Paragraph('모자', get_korean_style('h', 9, TA_CENTER, bold=True)),
        Paragraph('신발', get_korean_style('h', 9, TA_CENTER, bold=True)),
        Paragraph('품목', get_korean_style('h', 9, TA_CENTER, bold=True)),
    ]
    
    table_data = [header]
    
    for item in items:
        top_size = item.get('top_size', '')
        bottom_size = item.get('bottom_size', '')
        hat_size = item.get('hat_size', '')
        shoe_size = item.get('shoe_size', '')
        if shoe_size == '선택없음':
            shoe_size = ''
        
        products = item.get('products', [])
        if not products and item.get('product'):
            products = [{'name': item.get('product', ''), 'quantity': item.get('quantity', 1)}]
        
        products_str_list = []
        for p in products:
            if p.get('name') and p.get('quantity'):
                products_str_list.append(f"{p['name']}({p['quantity']})")
        products_text = ', '.join(products_str_list)
        
        row = [
            Paragraph(item.get('position', ''), get_korean_style('c', 9, TA_CENTER)),
            Paragraph(item.get('worker', ''), get_korean_style('c', 9, TA_CENTER)),
            Paragraph(str(top_size) if top_size else '', get_korean_style('c', 9, TA_CENTER)),
            Paragraph(str(bottom_size) if bottom_size else '', get_korean_style('c', 9, TA_CENTER)),
            Paragraph(str(hat_size) if hat_size else '', get_korean_style('c', 9, TA_CENTER)),
            Paragraph(str(shoe_size) if shoe_size else '', get_korean_style('c', 9, TA_CENTER)),
            Paragraph(products_text, get_korean_style('c', 9, TA_LEFT)),
        ]
        table_data.append(row)
    
    if len(table_data) < 6:
        for _ in range(6 - len(table_data)):
            table_data.append(['', '', '', '', '', '', ''])
    
    col_widths = [18*mm, 22*mm, 16*mm, 16*mm, 16*mm, 16*mm, 70*mm]
    
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'NanumGothic', 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ROWHEIGHT', (0, 0), (-1, -1), 12*mm),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 8*mm))
    
    app_date = data.get('application_date', datetime.now().strftime('%Y. %m. %d.'))
    applicant = data.get('applicant', '')
    
    info_text = f"신청일 : {app_date}                신청자 : {applicant}"
    elements.append(Paragraph(info_text, get_korean_style('info', 10, TA_CENTER)))
    elements.append(Spacer(1, 5*mm))
    
    site_name = data.get('site_name', '')
    address = data.get('address', '')
    contact = data.get('contact', '')
    remarks = data.get('remarks', '')
    
    elements.append(Paragraph(f"수신처 : {site_name} 관리사무소", normal_style))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(f"주소: {address}", normal_style))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(f"연락처 : {contact}", normal_style))
    elements.append(Spacer(1, 5*mm))
    remarks_style = get_korean_style('Remarks', 12, TA_LEFT, bold=True, text_color=colors.red)
    elements.append(Paragraph(f"비고: {remarks}", remarks_style))
    
    doc.build(elements)
    return output_path


def generate_supplies_pdf(data, output_path):
    """경비물품신청서 PDF 생성"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=10*mm,
        bottomMargin=10*mm
    )
    
    elements = []
    
    company = data.get('company', '미래')
    if company == '미래':
        logo_path = "attached_assets/미래ABM_LOGO_1768277050813.png"
        company_name = "㈜미래ABM"
    else:
        logo_path = "attached_assets/다원PMC_LOGO_1768277050810.png"
        company_name = "㈜다원PMC"
    
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=50*mm, height=15*mm)
        elements.append(logo)
    
    title_style = get_korean_style('Title', 16, TA_CENTER, bold=True)
    elements.append(Paragraph(f"{company_name} 경비물품신청서", title_style))
    elements.append(Spacer(1, 3*mm))
    
    normal_style = get_korean_style('Normal', 10, TA_LEFT)
    right_style = get_korean_style('Right', 10, TA_RIGHT)
    
    app_date = data.get('application_date', datetime.now().strftime('%Y.%m.%d'))
    elements.append(Paragraph(f"신청일 : {app_date}", right_style))
    elements.append(Spacer(1, 5*mm))
    
    vendor_info = "업체명 : 제이누리              Tel. 02-2214-1196   Fax.02-2213-6197"
    elements.append(Paragraph(vendor_info, normal_style))
    elements.append(Spacer(1, 5*mm))
    
    info_data = [
        ['배송처', data.get('site_name', '') + ' 경비실'],
        ['주소', data.get('address', '')],
        ['연락처', data.get('contact', '')],
    ]
    
    info_table = Table(info_data, colWidths=[25*mm, 145*mm])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'NanumGothic', 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ROWHEIGHT', (0, 0), (-1, -1), 10*mm),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 5*mm))
    
    items = data.get('items', [])
    
    items_text = ""
    for item in items:
        name = item.get('name', '')
        spec = item.get('spec', '')
        qty = item.get('quantity', 0)
        if spec:
            items_text += f"{name} {spec} {qty}개, "
        else:
            items_text += f"{name} {qty}개, "
    items_text = items_text.rstrip(', ')
    
    product_summary = [
        [Paragraph('신청물품', get_korean_style('h', 10, TA_CENTER, bold=True)), 
         Paragraph(items_text, get_korean_style('c', 10, TA_LEFT))],
    ]
    
    product_summary_table = Table(product_summary, colWidths=[25*mm, 145*mm])
    product_summary_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'NanumGothic', 10),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ROWHEIGHT', (0, 0), (-1, -1), 20*mm),
    ]))
    elements.append(product_summary_table)
    elements.append(Spacer(1, 5*mm))
    
    if items:
        detail_header = [
            Paragraph('No', get_korean_style('h', 9, TA_CENTER, bold=True)),
            Paragraph('품목명', get_korean_style('h', 9, TA_CENTER, bold=True)),
            Paragraph('규격', get_korean_style('h', 9, TA_CENTER, bold=True)),
            Paragraph('수량', get_korean_style('h', 9, TA_CENTER, bold=True)),
        ]
        detail_data = [detail_header]
        
        for idx, item in enumerate(items, 1):
            name = item.get('name', '')
            spec = item.get('spec', '')
            qty = item.get('quantity', 0)
            
            detail_data.append([
                Paragraph(str(idx), get_korean_style('c', 9, TA_CENTER)),
                Paragraph(name, get_korean_style('c', 9, TA_LEFT)),
                Paragraph(spec, get_korean_style('c', 9, TA_CENTER)),
                Paragraph(str(qty), get_korean_style('c', 9, TA_CENTER)),
            ])
        
        detail_table = Table(detail_data, colWidths=[15*mm, 80*mm, 50*mm, 25*mm])
        detail_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'NanumGothic', 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ROWHEIGHT', (0, 0), (-1, -1), 8*mm),
        ]))
        elements.append(detail_table)
        elements.append(Spacer(1, 5*mm))
    
    remarks = data.get('remarks', '경비물품 입니다.')
    remark_data = [
        [Paragraph('참고사항', get_korean_style('h', 10, TA_CENTER, bold=True)), 
         Paragraph(remarks, get_korean_style('c', 12, TA_LEFT, bold=True, text_color=colors.red))],
    ]
    
    remark_table = Table(remark_data, colWidths=[25*mm, 145*mm])
    remark_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'NanumGothic', 10),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ROWHEIGHT', (0, 0), (-1, -1), 15*mm),
    ]))
    elements.append(remark_table)
    elements.append(Spacer(1, 10*mm))
    
    applicant = data.get('applicant', '')
    applicant_contact = data.get('applicant_contact', '')
    elements.append(Paragraph(f"신청자 : {applicant}              tel:{applicant_contact}", 
                             get_korean_style('app', 10, TA_CENTER)))
    
    doc.build(elements)
    return output_path


def generate_pdf(data, app_type):
    """신청 유형에 따라 PDF 생성"""
    os.makedirs('output', exist_ok=True)
    
    company = data.get('company', '미래')
    site_name = data.get('site_name', '현장')
    date_str = datetime.now().strftime('%Y%m%d')
    
    company_prefix = f"[{company}]"
    if app_type == '피복':
        type_suffix = "경비원 피복 신청서"
        filename = f"{company_prefix}{date_str}_{site_name}_{type_suffix}.pdf"
        output_path = os.path.join('output', filename)
        return generate_uniform_pdf(data, output_path)
    else:
        type_suffix = "경비용품 신청서"
        filename = f"{company_prefix}{date_str}_{site_name}_{type_suffix}.pdf"
        output_path = os.path.join('output', filename)
        return generate_supplies_pdf(data, output_path)


def generate_application_history_pdf(df, month_label):
    """신청내역 PDF 생성 - BytesIO 반환"""
    from io import BytesIO
    import pandas as pd
    
    buffer = BytesIO()
    
    register_korean_fonts()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    elements = []
    
    title_style = get_korean_style('title', 16, TA_CENTER, bold=True)
    elements.append(Paragraph(f"신청 내역 현황 ({month_label})", title_style))
    elements.append(Spacer(1, 10*mm))
    
    header = [
        Paragraph('날짜', get_korean_style('h', 8, TA_CENTER, bold=True)),
        Paragraph('법인', get_korean_style('h', 8, TA_CENTER, bold=True)),
        Paragraph('현장명', get_korean_style('h', 8, TA_CENTER, bold=True)),
        Paragraph('신청자', get_korean_style('h', 8, TA_CENTER, bold=True)),
        Paragraph('구분', get_korean_style('h', 8, TA_CENTER, bold=True)),
        Paragraph('품목명', get_korean_style('h', 8, TA_CENTER, bold=True)),
        Paragraph('수량', get_korean_style('h', 8, TA_CENTER, bold=True)),
        Paragraph('금액', get_korean_style('h', 8, TA_CENTER, bold=True)),
    ]
    
    table_data = [header]
    
    total_amount = 0
    for _, row in df.iterrows():
        date_str = pd.to_datetime(row['날짜']).strftime('%Y-%m-%d') if pd.notna(row['날짜']) else ''
        amount = int(row['합계금액']) if pd.notna(row['합계금액']) else 0
        total_amount += amount
        
        table_row = [
            Paragraph(date_str, get_korean_style('c', 7, TA_CENTER)),
            Paragraph(str(row['법인명']) if pd.notna(row['법인명']) else '', get_korean_style('c', 7, TA_CENTER)),
            Paragraph(str(row['현장명']) if pd.notna(row['현장명']) else '', get_korean_style('c', 7, TA_CENTER)),
            Paragraph(str(row['신청자']) if pd.notna(row['신청자']) else '', get_korean_style('c', 7, TA_CENTER)),
            Paragraph(str(row['구분']) if pd.notna(row['구분']) else '', get_korean_style('c', 7, TA_CENTER)),
            Paragraph(str(row['품목명']) if pd.notna(row['품목명']) else '', get_korean_style('c', 7, TA_LEFT)),
            Paragraph(str(int(row['수량'])) if pd.notna(row['수량']) else '', get_korean_style('c', 7, TA_CENTER)),
            Paragraph(f"{amount:,}" if amount > 0 else '', get_korean_style('c', 7, TA_RIGHT)),
        ]
        table_data.append(table_row)
    
    table_data.append([
        Paragraph('합계', get_korean_style('h', 8, TA_CENTER, bold=True)),
        '', '', '', '', '', '',
        Paragraph(f"{total_amount:,}원", get_korean_style('h', 8, TA_RIGHT, bold=True)),
    ])
    
    col_widths = [22*mm, 15*mm, 30*mm, 18*mm, 15*mm, 45*mm, 12*mm, 23*mm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'NanumGothic', 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('ROWHEIGHT', (0, 0), (-1, -1), 8*mm),
    ]))
    
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_monthly_summary_pdf(df, company, month_columns):
    """월별 집계 PDF 생성 - BytesIO 반환"""
    from io import BytesIO
    
    buffer = BytesIO()
    
    register_korean_fonts()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(A4[1], A4[0]),
        rightMargin=10*mm,
        leftMargin=10*mm,
        topMargin=10*mm,
        bottomMargin=10*mm
    )
    
    elements = []
    
    title_style = get_korean_style('title', 16, TA_CENTER, bold=True)
    elements.append(Paragraph(f"{company} 월별 집계 현황", title_style))
    elements.append(Spacer(1, 8*mm))
    
    header = [Paragraph('현장명', get_korean_style('h', 8, TA_CENTER, bold=True)),
              Paragraph('예산', get_korean_style('h', 8, TA_CENTER, bold=True))]
    for month in month_columns:
        header.append(Paragraph(month, get_korean_style('h', 8, TA_CENTER, bold=True)))
    header.append(Paragraph('합계', get_korean_style('h', 8, TA_CENTER, bold=True)))
    
    table_data = [header]
    
    grand_total = 0
    for _, row in df.iterrows():
        row_total = sum([int(row.get(m, 0) or 0) for m in month_columns])
        grand_total += row_total
        
        table_row = [
            Paragraph(str(row['site_name']) if 'site_name' in row else '', get_korean_style('c', 7, TA_CENTER)),
            Paragraph(f"{int(row.get('budget', 0) or 0):,}", get_korean_style('c', 7, TA_RIGHT)),
        ]
        for month in month_columns:
            val = int(row.get(month, 0) or 0)
            table_row.append(Paragraph(f"{val:,}" if val > 0 else '', get_korean_style('c', 7, TA_RIGHT)))
        table_row.append(Paragraph(f"{row_total:,}", get_korean_style('c', 7, TA_RIGHT, bold=True)))
        table_data.append(table_row)
    
    col_widths = [35*mm, 20*mm] + [18*mm] * len(month_columns) + [22*mm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'NanumGothic', 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ROWHEIGHT', (0, 0), (-1, -1), 7*mm),
    ]))
    
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
