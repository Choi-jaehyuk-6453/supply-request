"""
Reference data module - now uses PostgreSQL database instead of JSON file.
Provides backward-compatible function signatures for app.py.
"""
from db_handler import (
    get_sites_db, add_site_db, update_site_db, delete_site_db, get_site_by_name_db,
    get_applicants_db, add_applicant_db, update_applicant_db, delete_applicant_db, get_applicant_by_name_db,
    get_supply_products_db, add_supply_product_db, update_supply_product_db, delete_supply_product_db, get_supply_product_by_name_db,
    get_uniform_products_db, add_uniform_product_db, update_uniform_product_db, delete_uniform_product_db, get_uniform_product_by_name_db,
    get_email_recipients_db, add_email_recipient_db, update_email_recipient_db, delete_email_recipient_db
)


# ============= 현장 관리 함수 =============
def get_sites():
    """모든 현장 목록 조회"""
    return get_sites_db()

def add_site(name, address, contact):
    """현장 추가"""
    return add_site_db(name, address, contact)

def update_site(site_id, name, address, contact):
    """현장 정보 수정"""
    return update_site_db(site_id, name, address, contact)

def delete_site(site_id):
    """현장 삭제"""
    return delete_site_db(site_id)

def get_site_by_name(name):
    """현장명으로 조회"""
    return get_site_by_name_db(name)

def search_sites(query):
    """현장 검색"""
    if not query:
        return get_sites()
    sites = get_sites()
    return [s for s in sites if query.lower() in s["name"].lower()]


# ============= 신청자 관리 함수 =============
def get_applicants():
    """모든 신청자 목록 조회"""
    return get_applicants_db()

def add_applicant(name, contact):
    """신청자 추가"""
    return add_applicant_db(name, contact)

def update_applicant(applicant_id, name, contact):
    """신청자 정보 수정"""
    return update_applicant_db(applicant_id, name, contact)

def delete_applicant(applicant_id):
    """신청자 삭제"""
    return delete_applicant_db(applicant_id)

def get_applicant_by_name(name):
    """신청자명으로 조회"""
    return get_applicant_by_name_db(name)

def search_applicants(query):
    """신청자 검색"""
    if not query:
        return get_applicants()
    applicants = get_applicants()
    return [a for a in applicants if query.lower() in a["name"].lower()]


# ============= 경비용품 품목 관리 함수 =============
def get_supply_products():
    """모든 경비용품 품목 조회"""
    return get_supply_products_db()

def add_supply_product(name, spec, unit_price):
    """경비용품 품목 추가"""
    return add_supply_product_db(name, spec, unit_price)

def update_supply_product(product_id, name, spec, unit_price):
    """경비용품 품목 수정"""
    return update_supply_product_db(product_id, name, spec, unit_price)

def delete_supply_product(product_id):
    """경비용품 품목 삭제"""
    return delete_supply_product_db(product_id)

def get_supply_product_by_name(name):
    """경비용품 품목명으로 조회"""
    return get_supply_product_by_name_db(name)


# ============= 피복 품목 관리 함수 =============
def get_uniform_products():
    """모든 피복 품목 조회"""
    return get_uniform_products_db()

def add_uniform_product(name, unit_price):
    """피복 품목 추가"""
    return add_uniform_product_db(name, unit_price)

def update_uniform_product(product_id, name, unit_price):
    """피복 품목 수정"""
    return update_uniform_product_db(product_id, name, unit_price)

def delete_uniform_product(product_id):
    """피복 품목 삭제"""
    return delete_uniform_product_db(product_id)

def get_uniform_product_by_name(name):
    """피복 품목명으로 조회"""
    return get_uniform_product_by_name_db(name)


# ============= 이메일 수신자 관리 함수 =============
def get_email_recipients():
    """모든 이메일 수신자 조회"""
    return get_email_recipients_db()

def add_email_recipient(company_name, email):
    """이메일 수신자 추가"""
    return add_email_recipient_db(company_name, email)

def update_email_recipient(recipient_id, company_name, email):
    """이메일 수신자 수정"""
    return update_email_recipient_db(recipient_id, company_name, email)

def delete_email_recipient(recipient_id):
    """이메일 수신자 삭제"""
    return delete_email_recipient_db(recipient_id)
