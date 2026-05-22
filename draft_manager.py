import json
import os
from datetime import datetime

DRAFT_FILE = "drafts.json"


import json
import os
from datetime import datetime
from db_handler import get_session, Draft

DRAFT_FILE = "drafts.json"

def save_draft(draft_data):
    """새 임시저장 추가"""
    draft_id = datetime.now().strftime('%Y%m%d%H%M%S')
    saved_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    session = get_session()
    if not session:
        return draft_id
        
    try:
        draft = Draft(
            id=draft_id,
            site_name=draft_data.get('site_name', ''),
            app_type=draft_data.get('app_type', ''),
            company=draft_data.get('company', ''),
            applicant=draft_data.get('applicant', ''),
            applicant_contact=draft_data.get('applicant_contact', ''),
            address=draft_data.get('address', ''),
            contact=draft_data.get('contact', ''),
            remarks=draft_data.get('remarks', ''),
            application_date=draft_data.get('application_date', ''),
            items_json=json.dumps(draft_data.get('items', []), ensure_ascii=False),
            item_count=len(draft_data.get('items', [])),
            saved_at=saved_at
        )
        session.add(draft)
        session.commit()
    except Exception as e:
        session.rollback()
        print("Draft save error:", e)
    finally:
        session.close()
        
    return draft_id

def update_draft(draft_id, draft_data):
    """기존 임시저장 수정"""
    session = get_session()
    if not session:
        return False
        
    try:
        draft = session.query(Draft).filter_by(id=draft_id).first()
        if draft:
            draft.site_name = draft_data.get('site_name', '')
            draft.app_type = draft_data.get('app_type', '')
            draft.company = draft_data.get('company', '')
            draft.applicant = draft_data.get('applicant', '')
            draft.applicant_contact = draft_data.get('applicant_contact', '')
            draft.address = draft_data.get('address', '')
            draft.contact = draft_data.get('contact', '')
            draft.remarks = draft_data.get('remarks', '')
            draft.application_date = draft_data.get('application_date', '')
            draft.items_json = json.dumps(draft_data.get('items', []), ensure_ascii=False)
            draft.item_count = len(draft_data.get('items', []))
            draft.saved_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print("Draft update error:", e)
        return False
    finally:
        session.close()

def get_draft(draft_id):
    """특정 임시저장 조회"""
    session = get_session()
    if not session:
        return None
        
    try:
        draft = session.query(Draft).filter_by(id=draft_id).first()
        if draft:
            return {
                'id': draft.id,
                'site_name': draft.site_name,
                'app_type': draft.app_type,
                'company': draft.company,
                'applicant': draft.applicant,
                'applicant_contact': draft.applicant_contact,
                'address': draft.address,
                'contact': draft.contact,
                'remarks': draft.remarks,
                'application_date': draft.application_date,
                'items': json.loads(draft.items_json) if draft.items_json else [],
                'saved_at': draft.saved_at
            }
        return None
    except Exception as e:
        print("Draft get error:", e)
        return None
    finally:
        session.close()

def delete_draft(draft_id):
    """임시저장 삭제"""
    session = get_session()
    if not session:
        return
        
    try:
        draft = session.query(Draft).filter_by(id=draft_id).first()
        if draft:
            session.delete(draft)
            session.commit()
    except Exception as e:
        session.rollback()
        print("Draft delete error:", e)
    finally:
        session.close()

def get_draft_list():
    """임시저장 목록 조회 (요약 정보)"""
    session = get_session()
    if not session:
        return []
        
    try:
        drafts = session.query(Draft).order_by(Draft.saved_at.desc()).all()
        return [
            {
                'id': d.id,
                'company': d.company,
                'app_type': d.app_type,
                'site_name': d.site_name,
                'applicant': d.applicant,
                'saved_at': d.saved_at,
                'item_count': d.item_count
            }
            for d in drafts
        ]
    except Exception as e:
        print("Draft list error:", e)
        return []
    finally:
        session.close()

def migrate_json_drafts_to_db():
    """기존 drafts.json 파일의 내용을 DB로 마이그레이션"""
    if not os.path.exists(DRAFT_FILE):
        return
        
    try:
        with open(DRAFT_FILE, 'r', encoding='utf-8') as f:
            old_drafts = json.load(f)
            
        session = get_session()
        if not session:
            return
            
        for draft_data in old_drafts:
            draft_id = draft_data.get('id')
            if not draft_id:
                continue
                
            existing = session.query(Draft).filter_by(id=draft_id).first()
            if not existing:
                draft = Draft(
                    id=draft_id,
                    site_name=draft_data.get('site_name', ''),
                    app_type=draft_data.get('app_type', ''),
                    company=draft_data.get('company', ''),
                    applicant=draft_data.get('applicant', ''),
                    applicant_contact=draft_data.get('applicant_contact', ''),
                    address=draft_data.get('address', ''),
                    contact=draft_data.get('contact', ''),
                    remarks=draft_data.get('remarks', ''),
                    application_date=draft_data.get('application_date', ''),
                    items_json=json.dumps(draft_data.get('items', []), ensure_ascii=False),
                    item_count=len(draft_data.get('items', [])),
                    saved_at=draft_data.get('saved_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                )
                session.add(draft)
        
        session.commit()
        session.close()
        
        # 마이그레이션 후 파일 이름 변경하여 재실행 방지
        os.rename(DRAFT_FILE, DRAFT_FILE + ".migrated")
        print("drafts.json migration completed.")
    except Exception as e:
        print("Draft migration error:", e)
