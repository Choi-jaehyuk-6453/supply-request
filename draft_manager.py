import json
import os
from datetime import datetime

DRAFT_FILE = "drafts.json"


def load_drafts():
    """임시저장된 신청서 목록 로드"""
    if os.path.exists(DRAFT_FILE):
        try:
            with open(DRAFT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_drafts(drafts):
    """임시저장 목록 저장"""
    with open(DRAFT_FILE, 'w', encoding='utf-8') as f:
        json.dump(drafts, f, ensure_ascii=False, indent=2)


def save_draft(draft_data):
    """새 임시저장 추가"""
    drafts = load_drafts()
    
    draft_id = datetime.now().strftime('%Y%m%d%H%M%S')
    draft_data['id'] = draft_id
    draft_data['saved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    drafts.append(draft_data)
    save_drafts(drafts)
    
    return draft_id


def update_draft(draft_id, draft_data):
    """기존 임시저장 수정"""
    drafts = load_drafts()
    
    for i, draft in enumerate(drafts):
        if draft['id'] == draft_id:
            draft_data['id'] = draft_id
            draft_data['saved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            drafts[i] = draft_data
            save_drafts(drafts)
            return True
    
    return False


def get_draft(draft_id):
    """특정 임시저장 조회"""
    drafts = load_drafts()
    for draft in drafts:
        if draft['id'] == draft_id:
            return draft
    return None


def delete_draft(draft_id):
    """임시저장 삭제"""
    drafts = load_drafts()
    drafts = [d for d in drafts if d['id'] != draft_id]
    save_drafts(drafts)


def get_draft_list():
    """임시저장 목록 조회 (요약 정보)"""
    drafts = load_drafts()
    return [
        {
            'id': d['id'],
            'company': d.get('company', ''),
            'app_type': d.get('app_type', ''),
            'site_name': d.get('site_name', ''),
            'applicant': d.get('applicant', ''),
            'saved_at': d.get('saved_at', ''),
            'item_count': len(d.get('items', []))
        }
        for d in drafts
    ]
