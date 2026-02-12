"""
Database handler module for PostgreSQL storage.
Replaces Excel-based storage for persistent data across deployments.
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd

DATABASE_URL = os.environ.get('DATABASE_URL')

engine = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()


class Application(Base):
    """신청 내역 테이블"""
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    app_type = Column(String(50), nullable=False)
    company = Column(String(50), nullable=False)
    site_name = Column(String(200), nullable=False)
    applicant = Column(String(100), nullable=False)
    product_name = Column(String(200))
    spec = Column(String(200))
    quantity = Column(Integer, default=1)
    unit_price = Column(Integer, default=0)
    total_amount = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class MonthlySummary(Base):
    """월별 집계 테이블"""
    __tablename__ = 'monthly_summary'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company = Column(String(50), nullable=False)
    site_name = Column(String(200), nullable=False)
    app_type = Column(String(50), nullable=False)
    budget = Column(Integer, default=0)
    month_01 = Column(Integer, default=0)
    month_02 = Column(Integer, default=0)
    month_03 = Column(Integer, default=0)
    month_04 = Column(Integer, default=0)
    month_05 = Column(Integer, default=0)
    month_06 = Column(Integer, default=0)
    month_07 = Column(Integer, default=0)
    month_08 = Column(Integer, default=0)
    month_09 = Column(Integer, default=0)
    month_10 = Column(Integer, default=0)
    month_11 = Column(Integer, default=0)
    month_12 = Column(Integer, default=0)


class Site(Base):
    """현장 정보 테이블"""
    __tablename__ = 'sites'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    company = Column(String(50), default='미래')
    address = Column(String(500))
    contact = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime)


class Applicant(Base):
    """신청자 정보 테이블"""
    __tablename__ = 'applicants'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    contact = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime)


class SupplyProduct(Base):
    """경비용품 품목 테이블"""
    __tablename__ = 'supply_products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    spec = Column(String(200))
    unit_price = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime)


class UniformProduct(Base):
    """피복 품목 테이블"""
    __tablename__ = 'uniform_products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    unit_price = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime)


class EmailRecipient(Base):
    """이메일 수신자 테이블"""
    __tablename__ = 'email_recipients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime)


class PdfFile(Base):
    """PDF 파일 저장 테이블"""
    __tablename__ = 'pdf_files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(500), nullable=False, unique=True)
    file_data = Column(LargeBinary, nullable=False)
    app_type = Column(String(50))
    company = Column(String(50))
    site_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)


def init_db():
    """데이터베이스 테이블 초기화"""
    if engine:
        Base.metadata.create_all(bind=engine)
        return True
    return False


def get_session():
    """DB 세션 반환"""
    if SessionLocal:
        return SessionLocal()
    return None


def append_to_master_db(date_str, app_type, company, site_name, applicant, items):
    """신청 내역을 DB에 저장"""
    session = get_session()
    if not session:
        return False, "데이터베이스 연결 오류"
    
    try:
        if '.' in date_str:
            date_obj = datetime.strptime(date_str.replace('.', '-').replace(' ', '').rstrip('-'), '%Y-%m-%d').date()
        else:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        total_amount = 0
        for item in items:
            if app_type == '피복':
                products = item.get('products', [])
                worker = item.get('worker', '')
                top_size = item.get('top_size', '')
                bottom_size = item.get('bottom_size', '')
                hat_size = item.get('hat_size', '')
                shoe_size = item.get('shoe_size', '')
                spec_parts = []
                if worker:
                    spec_parts.append(f"근무자:{worker}")
                if top_size and top_size != '선택없음':
                    spec_parts.append(f"상의:{top_size}")
                if bottom_size and bottom_size != '선택없음':
                    spec_parts.append(f"하의:{bottom_size}")
                if hat_size and hat_size != '선택없음':
                    spec_parts.append(f"모자:{hat_size}")
                if shoe_size and shoe_size != '선택없음':
                    spec_parts.append(f"신발:{shoe_size}")
                spec_str = '/'.join(spec_parts) if spec_parts else ''
                
                for product in products:
                    product_name = product.get('name', '')
                    quantity = product.get('quantity', 1)
                    unit_price = product.get('unit_price', 0)
                    item_total = quantity * unit_price
                    total_amount += item_total
                    
                    application = Application(
                        date=date_obj,
                        app_type=app_type,
                        company=company,
                        site_name=site_name,
                        applicant=applicant,
                        product_name=product_name,
                        spec=spec_str,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_amount=item_total
                    )
                    session.add(application)
            else:
                product_name = item.get('name', '')
                spec = item.get('spec', '')
                quantity = item.get('quantity', 1)
                unit_price = item.get('unit_price', 0)
                item_total = quantity * unit_price
                total_amount += item_total
                
                application = Application(
                    date=date_obj,
                    app_type=app_type,
                    company=company,
                    site_name=site_name,
                    applicant=applicant,
                    product_name=product_name,
                    spec=spec,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_amount=item_total
                )
                session.add(application)
        
        session.commit()
        session.close()
        
        summary_message = ""
        if total_amount > 0:
            month = date_obj.month
            amount_with_vat = int(total_amount * 1.1)
            success, msg = update_monthly_summary_db(site_name, company, app_type, month, amount_with_vat)
            if not success:
                summary_message = f" (주의: {msg})"
        
        return True, f"데이터가 성공적으로 저장되었습니다.{summary_message}"
    
    except Exception as e:
        session.rollback()
        session.close()
        return False, f"데이터 저장 중 오류가 발생했습니다: {str(e)}"


def delete_application_db(date_str, site_name, applicant, app_type, company):
    """신청 내역 삭제 및 월별 집계 업데이트 (단일 트랜잭션)"""
    session = get_session()
    if not session:
        return False, "데이터베이스 연결 오류"
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        applications = session.query(Application).filter(
            Application.date == date_obj,
            Application.site_name == site_name,
            Application.applicant == applicant,
            Application.app_type == app_type,
            Application.company == company
        ).all()
        
        if not applications:
            session.close()
            return False, "삭제할 데이터를 찾을 수 없습니다."
        
        total_amount = sum(app.total_amount for app in applications)
        month = date_obj.month
        app_count = len(applications)
        
        for app in applications:
            session.delete(app)
        
        if total_amount > 0:
            amount_with_vat = int(total_amount * 1.1)
            summary = session.query(MonthlySummary).filter_by(
                company=company,
                site_name=site_name,
                app_type=app_type
            ).first()
            
            if summary:
                month_cols = {
                    1: 'month_01', 2: 'month_02', 3: 'month_03', 4: 'month_04',
                    5: 'month_05', 6: 'month_06', 7: 'month_07', 8: 'month_08',
                    9: 'month_09', 10: 'month_10', 11: 'month_11', 12: 'month_12'
                }
                col_name = month_cols.get(month)
                if col_name:
                    current_value = getattr(summary, col_name, 0) or 0
                    new_value = max(0, current_value - amount_with_vat)
                    setattr(summary, col_name, new_value)
        
        session.commit()
        session.close()
        return True, f"{app_count}건의 신청 내역이 삭제되었습니다."
    
    except Exception as e:
        session.rollback()
        session.close()
        return False, f"삭제 중 오류가 발생했습니다: {str(e)}"


def get_master_data_db():
    """신청 내역 조회"""
    session = get_session()
    if not session:
        return pd.DataFrame()
    
    try:
        applications = session.query(Application).all()
        
        data = []
        for app in applications:
            data.append({
                '날짜': app.date,
                '구분': app.app_type,
                '법인명': app.company,
                '현장명': app.site_name,
                '신청자': app.applicant,
                '품목명': app.product_name,
                '규격': app.spec,
                '수량': app.quantity,
                '단가': app.unit_price,
                '합계금액': app.total_amount
            })
        
        session.close()
        return pd.DataFrame(data)
    except Exception as e:
        session.close()
        return pd.DataFrame()


def get_monthly_summary_db():
    """월별 요약 조회"""
    session = get_session()
    if not session:
        return pd.DataFrame()
    
    try:
        df = get_master_data_db()
        if df.empty:
            session.close()
            return pd.DataFrame()
        
        df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        df['년월'] = df['날짜'].dt.strftime('%Y-%m')
        
        summary = df.groupby(['년월', '법인명', '구분'])['합계금액'].sum().reset_index()
        summary.columns = ['년월', '법인명', '구분', '총액']
        
        session.close()
        return summary
    except Exception:
        session.close()
        return pd.DataFrame()


def get_all_monthly_summary_db():
    """전체 월별 집계 데이터 조회 (피복 + 경비물품)"""
    session = get_session()
    if not session:
        return {'피복': pd.DataFrame(), '경비물품': pd.DataFrame()}
    
    try:
        summaries = session.query(MonthlySummary).all()
        
        uniform_data = []
        supply_data = []
        
        for s in summaries:
            total = (s.month_01 + s.month_02 + s.month_03 + s.month_04 + 
                    s.month_05 + s.month_06 + s.month_07 + s.month_08 + 
                    s.month_09 + s.month_10 + s.month_11 + s.month_12)
            available = s.budget - total
            
            row = {
                '구분': s.company,
                '현장명': s.site_name,
                '예산': s.budget,
                '1월': s.month_01, '2월': s.month_02, '3월': s.month_03,
                '4월': s.month_04, '5월': s.month_05, '6월': s.month_06,
                '7월': s.month_07, '8월': s.month_08, '9월': s.month_09,
                '10월': s.month_10, '11월': s.month_11, '12월': s.month_12,
                '합계': total,
                '가용': available
            }
            
            if s.app_type == '피복':
                uniform_data.append(row)
            else:
                supply_data.append(row)
        
        session.close()
        return {
            '피복': pd.DataFrame(uniform_data),
            '경비물품': pd.DataFrame(supply_data)
        }
    except Exception as e:
        session.close()
        return {'피복': pd.DataFrame(), '경비물품': pd.DataFrame()}


def update_monthly_summary_db(site_name, company, app_type, month, amount):
    """월별 집계 업데이트 (관리자 모드에서 등록된 현장만 업데이트)"""
    session = get_session()
    if not session:
        return False, "데이터베이스 연결 오류"
    
    try:
        summary = session.query(MonthlySummary).filter_by(
            company=company, 
            site_name=site_name, 
            app_type=app_type
        ).first()
        
        if not summary:
            session.close()
            return False, f"현장 '{site_name}'이(가) 월별 집계에 등록되지 않았습니다. 관리자 모드에서 현장을 먼저 등록해주세요."
        
        month_cols = {
            1: 'month_01', 2: 'month_02', 3: 'month_03', 4: 'month_04',
            5: 'month_05', 6: 'month_06', 7: 'month_07', 8: 'month_08',
            9: 'month_09', 10: 'month_10', 11: 'month_11', 12: 'month_12'
        }
        
        col_name = month_cols.get(month)
        if col_name:
            current_value = getattr(summary, col_name, 0) or 0
            setattr(summary, col_name, current_value + amount)
        
        session.commit()
        session.close()
        return True, "월별 집계가 업데이트되었습니다."
    
    except Exception as e:
        session.rollback()
        session.close()
        return False, f"월별 집계 업데이트 오류: {str(e)}"


def recalculate_all_monthly_summaries():
    """기존 신청 내역 기반으로 월별 집계 재계산 (VAT 10% 포함)"""
    session = get_session()
    if not session:
        return False, "데이터베이스 연결 오류"
    
    try:
        session.query(MonthlySummary).update({
            'month_01': 0, 'month_02': 0, 'month_03': 0, 'month_04': 0,
            'month_05': 0, 'month_06': 0, 'month_07': 0, 'month_08': 0,
            'month_09': 0, 'month_10': 0, 'month_11': 0, 'month_12': 0
        })
        
        applications = session.query(Application).all()
        
        month_cols = {
            1: 'month_01', 2: 'month_02', 3: 'month_03', 4: 'month_04',
            5: 'month_05', 6: 'month_06', 7: 'month_07', 8: 'month_08',
            9: 'month_09', 10: 'month_10', 11: 'month_11', 12: 'month_12'
        }
        
        updated_count = 0
        for app in applications:
            summary = session.query(MonthlySummary).filter_by(
                company=app.company,
                site_name=app.site_name,
                app_type=app.app_type
            ).first()
            
            if summary and app.total_amount > 0:
                month = app.date.month
                col_name = month_cols.get(month)
                if col_name:
                    current_value = getattr(summary, col_name, 0) or 0
                    amount_with_vat = int(app.total_amount * 1.1)
                    setattr(summary, col_name, current_value + amount_with_vat)
                    updated_count += 1
        
        session.commit()
        session.close()
        return True, f"월별 집계가 재계산되었습니다. ({updated_count}건 처리, VAT 10% 포함)"
    
    except Exception as e:
        session.rollback()
        session.close()
        return False, f"재계산 오류: {str(e)}"


def add_monthly_summary_site_db(site_name, company, uniform_budget, supply_budget):
    """월별 집계에 새 현장 추가"""
    session = get_session()
    if not session:
        return False, "데이터베이스 연결 오류"
    
    try:
        existing = session.query(MonthlySummary).filter_by(
            company=company, 
            site_name=site_name
        ).first()
        
        if existing:
            session.close()
            return False, f"'{site_name}'은(는) 이미 등록된 현장입니다."
        
        uniform_summary = MonthlySummary(
            company=company,
            site_name=site_name,
            app_type='피복',
            budget=uniform_budget
        )
        session.add(uniform_summary)
        
        supply_summary = MonthlySummary(
            company=company,
            site_name=site_name,
            app_type='경비물품',
            budget=supply_budget
        )
        session.add(supply_summary)
        
        session.commit()
        session.close()
        return True, f"'{site_name}' 현장이 추가되었습니다."
    
    except Exception as e:
        session.rollback()
        session.close()
        return False, f"현장 추가 오류: {str(e)}"


def delete_monthly_summary_site_db(site_name, company):
    """월별 집계에서 현장 삭제"""
    session = get_session()
    if not session:
        return False, "데이터베이스 연결 오류"
    
    try:
        session.query(MonthlySummary).filter_by(
            company=company, 
            site_name=site_name
        ).delete()
        
        session.commit()
        session.close()
        return True, f"'{site_name}' 현장이 삭제되었습니다."
    
    except Exception as e:
        session.rollback()
        session.close()
        return False, f"현장 삭제 오류: {str(e)}"


def update_monthly_summary_budget_db(site_name, company, app_type, new_budget):
    """월별 집계에서 현장 예산 수정"""
    session = get_session()
    if not session:
        return False, "데이터베이스 연결 오류"
    
    try:
        summary = session.query(MonthlySummary).filter_by(
            company=company, 
            site_name=site_name, 
            app_type=app_type
        ).first()
        
        if summary:
            summary.budget = new_budget
            session.commit()
            session.close()
            return True, f"'{site_name}'의 {app_type} 예산이 {new_budget:,}원으로 수정되었습니다."
        else:
            session.close()
            return False, f"'{site_name}'을(를) 찾을 수 없습니다."
    
    except Exception as e:
        session.rollback()
        session.close()
        return False, f"예산 수정 오류: {str(e)}"


def migrate_excel_to_db():
    """기존 엑셀 데이터를 DB로 마이그레이션"""
    session = get_session()
    if not session:
        return False, "데이터베이스 연결 오류"
    
    try:
        init_db()
        
        existing_summary = session.query(MonthlySummary).first()
        if existing_summary:
            session.close()
            return True, "이미 마이그레이션된 데이터가 있습니다."
        
        MONTHLY_FILE = "monthly_summary.xlsx"
        if os.path.exists(MONTHLY_FILE):
            try:
                df_uniform = pd.read_excel(MONTHLY_FILE, sheet_name='피복')
                df_supply = pd.read_excel(MONTHLY_FILE, sheet_name='경비물품 등')
                
                def safe_int(val):
                    if pd.isna(val) or val is None:
                        return 0
                    try:
                        return int(val)
                    except (ValueError, TypeError):
                        return 0
                
                for _, row in df_uniform.iterrows():
                    company_val = row.get('구분', '')
                    site_val = row.get('현장명', '')
                    if pd.isna(company_val) or pd.isna(site_val) or not company_val or not site_val:
                        continue
                    
                    summary = MonthlySummary(
                        company=str(company_val),
                        site_name=str(site_val),
                        app_type='피복',
                        budget=safe_int(row.get('예산', 0)),
                        month_01=safe_int(row.get('1월', 0)),
                        month_02=safe_int(row.get('2월', 0)),
                        month_03=safe_int(row.get('3월', 0)),
                        month_04=safe_int(row.get('4월', 0)),
                        month_05=safe_int(row.get('5월', 0)),
                        month_06=safe_int(row.get('6월', 0)),
                        month_07=safe_int(row.get('7월', 0)),
                        month_08=safe_int(row.get('8월', 0)),
                        month_09=safe_int(row.get('9월', 0)),
                        month_10=safe_int(row.get('10월', 0)),
                        month_11=safe_int(row.get('11월', 0)),
                        month_12=safe_int(row.get('12월', 0))
                    )
                    session.add(summary)
                
                for _, row in df_supply.iterrows():
                    company_val = row.get('구분', '')
                    site_val = row.get('현장명', '')
                    if pd.isna(company_val) or pd.isna(site_val) or not company_val or not site_val:
                        continue
                    
                    summary = MonthlySummary(
                        company=str(company_val),
                        site_name=str(site_val),
                        app_type='경비물품',
                        budget=safe_int(row.get('예산', 0)),
                        month_01=safe_int(row.get('1월', 0)),
                        month_02=safe_int(row.get('2월', 0)),
                        month_03=safe_int(row.get('3월', 0)),
                        month_04=safe_int(row.get('4월', 0)),
                        month_05=safe_int(row.get('5월', 0)),
                        month_06=safe_int(row.get('6월', 0)),
                        month_07=safe_int(row.get('7월', 0)),
                        month_08=safe_int(row.get('8월', 0)),
                        month_09=safe_int(row.get('9월', 0)),
                        month_10=safe_int(row.get('10월', 0)),
                        month_11=safe_int(row.get('11월', 0)),
                        month_12=safe_int(row.get('12월', 0))
                    )
                    session.add(summary)
                
                session.commit()
                session.close()
                return True, f"월별 집계 데이터 마이그레이션 완료 (피복: {len(df_uniform)}건, 경비물품: {len(df_supply)}건)"
            
            except Exception as e:
                session.rollback()
                session.close()
                return False, f"엑셀 데이터 마이그레이션 오류: {str(e)}"
        else:
            session.close()
            return True, "마이그레이션할 엑셀 파일이 없습니다. 빈 DB로 시작합니다."
    
    except Exception as e:
        session.close()
        return False, f"마이그레이션 오류: {str(e)}"


# ============= 현장 관리 함수 =============
def get_sites_db():
    """모든 현장 목록 조회"""
    session = get_session()
    if not session:
        return []
    try:
        sites = session.query(Site).all()
        result = [{"id": s.id, "name": s.name, "company": s.company or "미래", "address": s.address or "", "contact": s.contact or ""} for s in sites]
        session.close()
        return result
    except Exception:
        session.close()
        return []

def add_site_db(name, company, address, contact):
    """현장 추가"""
    session = get_session()
    if not session:
        return None
    try:
        site = Site(name=name, company=company, address=address, contact=contact, created_at=datetime.now())
        session.add(site)
        session.commit()
        result = {"id": site.id, "name": site.name, "company": site.company, "address": site.address, "contact": site.contact}
        session.close()
        return result
    except Exception:
        session.rollback()
        session.close()
        return None

def update_site_db(site_id, name, company, address, contact):
    """현장 정보 수정"""
    session = get_session()
    if not session:
        return None
    try:
        site = session.query(Site).filter(Site.id == site_id).first()
        if site:
            site.name = name
            site.company = company
            site.address = address
            site.contact = contact
            site.updated_at = datetime.now()
            session.commit()
            result = {"id": site.id, "name": site.name, "company": site.company, "address": site.address, "contact": site.contact}
            session.close()
            return result
        session.close()
        return None
    except Exception:
        session.rollback()
        session.close()
        return None

def delete_site_db(site_id):
    """현장 삭제"""
    session = get_session()
    if not session:
        return False
    try:
        site = session.query(Site).filter(Site.id == site_id).first()
        if site:
            session.delete(site)
            session.commit()
            session.close()
            return True
        session.close()
        return False
    except Exception:
        session.rollback()
        session.close()
        return False

def get_site_by_name_db(name):
    """현장명으로 조회"""
    session = get_session()
    if not session:
        return None
    try:
        site = session.query(Site).filter(Site.name == name).first()
        if site:
            result = {"id": site.id, "name": site.name, "address": site.address or "", "contact": site.contact or ""}
            session.close()
            return result
        session.close()
        return None
    except Exception:
        session.close()
        return None


# ============= 신청자 관리 함수 =============
def get_applicants_db():
    """모든 신청자 목록 조회"""
    session = get_session()
    if not session:
        return []
    try:
        applicants = session.query(Applicant).all()
        result = [{"id": a.id, "name": a.name, "contact": a.contact or ""} for a in applicants]
        session.close()
        return result
    except Exception:
        session.close()
        return []

def add_applicant_db(name, contact):
    """신청자 추가"""
    session = get_session()
    if not session:
        return None
    try:
        applicant = Applicant(name=name, contact=contact, created_at=datetime.now())
        session.add(applicant)
        session.commit()
        result = {"id": applicant.id, "name": applicant.name, "contact": applicant.contact}
        session.close()
        return result
    except Exception:
        session.rollback()
        session.close()
        return None

def update_applicant_db(applicant_id, name, contact):
    """신청자 정보 수정"""
    session = get_session()
    if not session:
        return None
    try:
        applicant = session.query(Applicant).filter(Applicant.id == applicant_id).first()
        if applicant:
            applicant.name = name
            applicant.contact = contact
            applicant.updated_at = datetime.now()
            session.commit()
            result = {"id": applicant.id, "name": applicant.name, "contact": applicant.contact}
            session.close()
            return result
        session.close()
        return None
    except Exception:
        session.rollback()
        session.close()
        return None

def delete_applicant_db(applicant_id):
    """신청자 삭제"""
    session = get_session()
    if not session:
        return False
    try:
        applicant = session.query(Applicant).filter(Applicant.id == applicant_id).first()
        if applicant:
            session.delete(applicant)
            session.commit()
            session.close()
            return True
        session.close()
        return False
    except Exception:
        session.rollback()
        session.close()
        return False

def get_applicant_by_name_db(name):
    """신청자명으로 조회"""
    session = get_session()
    if not session:
        return None
    try:
        applicant = session.query(Applicant).filter(Applicant.name == name).first()
        if applicant:
            result = {"id": applicant.id, "name": applicant.name, "contact": applicant.contact or ""}
            session.close()
            return result
        session.close()
        return None
    except Exception:
        session.close()
        return None


# ============= 경비용품 품목 관리 함수 =============
def get_supply_products_db():
    """모든 경비용품 품목 조회"""
    session = get_session()
    if not session:
        return []
    try:
        products = session.query(SupplyProduct).all()
        result = [{"id": p.id, "name": p.name, "spec": p.spec or "", "unit_price": p.unit_price or 0} for p in products]
        session.close()
        return result
    except Exception:
        session.close()
        return []

def add_supply_product_db(name, spec, unit_price):
    """경비용품 품목 추가"""
    session = get_session()
    if not session:
        return None
    try:
        product = SupplyProduct(name=name, spec=spec, unit_price=int(unit_price), created_at=datetime.now())
        session.add(product)
        session.commit()
        result = {"id": product.id, "name": product.name, "spec": product.spec, "unit_price": product.unit_price}
        session.close()
        return result
    except Exception:
        session.rollback()
        session.close()
        return None

def update_supply_product_db(product_id, name, spec, unit_price):
    """경비용품 품목 수정"""
    session = get_session()
    if not session:
        return None
    try:
        product = session.query(SupplyProduct).filter(SupplyProduct.id == product_id).first()
        if product:
            product.name = name
            product.spec = spec
            product.unit_price = int(unit_price)
            product.updated_at = datetime.now()
            session.commit()
            result = {"id": product.id, "name": product.name, "spec": product.spec, "unit_price": product.unit_price}
            session.close()
            return result
        session.close()
        return None
    except Exception:
        session.rollback()
        session.close()
        return None

def delete_supply_product_db(product_id):
    """경비용품 품목 삭제"""
    session = get_session()
    if not session:
        return False
    try:
        product = session.query(SupplyProduct).filter(SupplyProduct.id == product_id).first()
        if product:
            session.delete(product)
            session.commit()
            session.close()
            return True
        session.close()
        return False
    except Exception:
        session.rollback()
        session.close()
        return False

def get_supply_product_by_name_db(name):
    """경비용품 품목명으로 조회"""
    session = get_session()
    if not session:
        return None
    try:
        product = session.query(SupplyProduct).filter(SupplyProduct.name == name).first()
        if product:
            result = {"id": product.id, "name": product.name, "spec": product.spec or "", "unit_price": product.unit_price or 0}
            session.close()
            return result
        session.close()
        return None
    except Exception:
        session.close()
        return None


# ============= 피복 품목 관리 함수 =============
def get_uniform_products_db():
    """모든 피복 품목 조회"""
    session = get_session()
    if not session:
        return []
    try:
        products = session.query(UniformProduct).all()
        result = [{"id": p.id, "name": p.name, "unit_price": p.unit_price or 0} for p in products]
        session.close()
        return result
    except Exception:
        session.close()
        return []

def add_uniform_product_db(name, unit_price):
    """피복 품목 추가"""
    session = get_session()
    if not session:
        return None
    try:
        product = UniformProduct(name=name, unit_price=int(unit_price), created_at=datetime.now())
        session.add(product)
        session.commit()
        result = {"id": product.id, "name": product.name, "unit_price": product.unit_price}
        session.close()
        return result
    except Exception:
        session.rollback()
        session.close()
        return None

def update_uniform_product_db(product_id, name, unit_price):
    """피복 품목 수정"""
    session = get_session()
    if not session:
        return None
    try:
        product = session.query(UniformProduct).filter(UniformProduct.id == product_id).first()
        if product:
            product.name = name
            product.unit_price = int(unit_price)
            product.updated_at = datetime.now()
            session.commit()
            result = {"id": product.id, "name": product.name, "unit_price": product.unit_price}
            session.close()
            return result
        session.close()
        return None
    except Exception:
        session.rollback()
        session.close()
        return None

def delete_uniform_product_db(product_id):
    """피복 품목 삭제"""
    session = get_session()
    if not session:
        return False
    try:
        product = session.query(UniformProduct).filter(UniformProduct.id == product_id).first()
        if product:
            session.delete(product)
            session.commit()
            session.close()
            return True
        session.close()
        return False
    except Exception:
        session.rollback()
        session.close()
        return False

def get_uniform_product_by_name_db(name):
    """피복 품목명으로 조회"""
    session = get_session()
    if not session:
        return None
    try:
        product = session.query(UniformProduct).filter(UniformProduct.name == name).first()
        if product:
            result = {"id": product.id, "name": product.name, "unit_price": product.unit_price or 0}
            session.close()
            return result
        session.close()
        return None
    except Exception:
        session.close()
        return None


# ============= 이메일 수신자 관리 함수 =============
def get_email_recipients_db():
    """모든 이메일 수신자 조회"""
    session = get_session()
    if not session:
        return []
    try:
        recipients = session.query(EmailRecipient).all()
        result = [{"id": r.id, "company_name": r.company_name, "email": r.email} for r in recipients]
        session.close()
        return result
    except Exception:
        session.close()
        return []

def add_email_recipient_db(company_name, email):
    """이메일 수신자 추가"""
    session = get_session()
    if not session:
        return None
    try:
        recipient = EmailRecipient(company_name=company_name, email=email, created_at=datetime.now())
        session.add(recipient)
        session.commit()
        result = {"id": recipient.id, "company_name": recipient.company_name, "email": recipient.email}
        session.close()
        return result
    except Exception:
        session.rollback()
        session.close()
        return None

def update_email_recipient_db(recipient_id, company_name, email):
    """이메일 수신자 수정"""
    session = get_session()
    if not session:
        return None
    try:
        recipient = session.query(EmailRecipient).filter(EmailRecipient.id == recipient_id).first()
        if recipient:
            recipient.company_name = company_name
            recipient.email = email
            recipient.updated_at = datetime.now()
            session.commit()
            result = {"id": recipient.id, "company_name": recipient.company_name, "email": recipient.email}
            session.close()
            return result
        session.close()
        return None
    except Exception:
        session.rollback()
        session.close()
        return None

def delete_email_recipient_db(recipient_id):
    """이메일 수신자 삭제"""
    session = get_session()
    if not session:
        return False
    try:
        recipient = session.query(EmailRecipient).filter(EmailRecipient.id == recipient_id).first()
        if recipient:
            session.delete(recipient)
            session.commit()
            session.close()
            return True
        session.close()
        return False
    except Exception:
        session.rollback()
        session.close()
        return False


def migrate_reference_data_to_db():
    """JSON 파일의 참조 데이터를 DB로 마이그레이션"""
    import json
    
    DATA_FILE = "reference_data.json"
    if not os.path.exists(DATA_FILE):
        return True, "마이그레이션할 JSON 파일이 없습니다."
    
    session = get_session()
    if not session:
        return False, "데이터베이스 연결 오류"
    
    try:
        existing_site = session.query(Site).first()
        if existing_site:
            session.close()
            return True, "이미 참조 데이터가 DB에 있습니다."
        
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        site_count = 0
        for site in data.get("sites", []):
            s = Site(name=site.get("name", ""), address=site.get("address", ""), contact=site.get("contact", ""))
            session.add(s)
            site_count += 1
        
        applicant_count = 0
        for app in data.get("applicants", []):
            a = Applicant(name=app.get("name", ""), contact=app.get("contact", ""))
            session.add(a)
            applicant_count += 1
        
        supply_count = 0
        for prod in data.get("supply_products", []):
            p = SupplyProduct(name=prod.get("name", ""), spec=prod.get("spec", ""), unit_price=prod.get("unit_price", 0))
            session.add(p)
            supply_count += 1
        
        uniform_count = 0
        for prod in data.get("uniform_products", []):
            p = UniformProduct(name=prod.get("name", ""), unit_price=prod.get("unit_price", 0))
            session.add(p)
            uniform_count += 1
        
        email_count = 0
        for recip in data.get("email_recipients", []):
            r = EmailRecipient(company_name=recip.get("company_name", ""), email=recip.get("email", ""))
            session.add(r)
            email_count += 1
        
        session.commit()
        session.close()
        return True, f"참조 데이터 마이그레이션 완료 (현장: {site_count}, 신청자: {applicant_count}, 경비용품: {supply_count}, 피복: {uniform_count}, 이메일: {email_count})"
    except Exception as e:
        session.rollback()
        session.close()
        return False, f"참조 데이터 마이그레이션 오류: {str(e)}"


def save_pdf_to_db(filename, file_data, app_type=None, company=None, site_name=None):
    """PDF 파일을 DB에 저장"""
    session = get_session()
    if not session:
        return False
    
    try:
        existing = session.query(PdfFile).filter_by(filename=filename).first()
        if existing:
            existing.file_data = file_data
            existing.app_type = app_type
            existing.company = company
            existing.site_name = site_name
        else:
            pdf = PdfFile(
                filename=filename,
                file_data=file_data,
                app_type=app_type,
                company=company,
                site_name=site_name
            )
            session.add(pdf)
        session.commit()
        session.close()
        return True
    except Exception as e:
        session.rollback()
        session.close()
        print(f"PDF DB 저장 오류: {str(e)}")
        return False


def get_pdf_from_db(filename):
    """DB에서 PDF 파일 데이터 가져오기"""
    session = get_session()
    if not session:
        return None
    
    try:
        pdf = session.query(PdfFile).filter_by(filename=filename).first()
        if pdf:
            data = bytes(pdf.file_data)
            session.close()
            return data
        session.close()
        return None
    except Exception as e:
        session.close()
        print(f"PDF DB 조회 오류: {str(e)}")
        return None


def migrate_existing_pdfs_to_db():
    """output/ 폴더의 기존 PDF 파일을 DB로 마이그레이션"""
    output_dir = "output"
    if not os.path.exists(output_dir):
        return 0
    
    count = 0
    for filename in os.listdir(output_dir):
        if filename.endswith('.pdf'):
            filepath = os.path.join(output_dir, filename)
            try:
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                if save_pdf_to_db(filename, file_data):
                    count += 1
            except Exception as e:
                print(f"PDF 마이그레이션 오류 ({filename}): {str(e)}")
    return count
