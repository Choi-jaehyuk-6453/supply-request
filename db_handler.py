"""
Database handler module for PostgreSQL storage.
Replaces Excel-based storage for persistent data across deployments.
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Text
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
                product_name = item.get('product', '')
                spec = ''
                quantity = item.get('quantity', 1)
                unit_price = item.get('unit_price', 0)
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
        
        if total_amount > 0:
            month = date_obj.month
            update_monthly_summary_db(site_name, company, app_type, month, total_amount)
        
        session.close()
        return True, "데이터가 성공적으로 저장되었습니다."
    
    except Exception as e:
        session.rollback()
        session.close()
        return False, f"데이터 저장 중 오류가 발생했습니다: {str(e)}"


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
    """월별 집계 업데이트"""
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
        else:
            session.close()
            return False, f"현장 '{site_name}'을(를) 찾을 수 없습니다."
    
    except Exception as e:
        session.rollback()
        session.close()
        return False, f"월별 집계 업데이트 오류: {str(e)}"


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
