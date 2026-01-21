# 경비용품 및 피복 신청 관리 시스템

## Overview
건물관리 회사(미래ABM, 다원PMC)의 경비용품 및 피복 신청을 관리하는 웹 애플리케이션입니다.
사용자가 신청 내용을 입력하면 PDF 신청서가 생성되고, 이메일로 전송되며, PostgreSQL 데이터베이스에 데이터가 저장됩니다.

## Features
1. **PDF 신청서 생성**: 피복신청서 / 경비물품신청서를 각 법인 양식에 맞게 생성
2. **이메일 전송**: Naver SMTP를 통해 지정된 담당자에게 전송
3. **PostgreSQL 데이터 관리**: 신청 내역 및 월별 집계를 데이터베이스에 저장 (배포 후에도 유지)
4. **관리자 모드**: 현장, 신청자, 품목 정보를 미리 등록하여 자동완성 기능 지원 (DB 저장)
5. **품목 단가 관리**: 경비용품/피복 품목별 단가 등록 및 금액 자동 계산
6. **임시저장**: 작성 중인 신청서를 임시저장하고 나중에 불러오기

## Project Architecture
```
├── app.py                 # 메인 Streamlit 애플리케이션
├── pdf_generator.py       # PDF 생성 모듈 (ReportLab)
├── email_sender.py        # 이메일 전송 모듈 (SMTP)
├── db_handler.py          # PostgreSQL 데이터베이스 관리 모듈 (SQLAlchemy)
├── reference_data.py      # 현장/신청자 참조 데이터 관리 (DB 래퍼)
├── draft_manager.py       # 임시저장 관리 모듈
├── attached_assets/       # 로고 이미지 및 참고 문서
│   ├── 미래ABM_LOGO_*.png
│   └── 다원PMC_LOGO_*.png
├── output/                # 생성된 PDF 파일 저장 폴더
└── fonts/                 # 한글 폰트 폴더
```

## Database Schema
PostgreSQL 테이블 구조:
- **applications**: 신청 내역 (날짜, 유형, 회사, 현장, 신청자, 품목, 수량, 단가, 금액)
- **monthly_summary**: 월별 집계 (회사, 현장, 예산, 1-12월 실적)
- **sites**: 현장 정보 (현장명, 주소, 연락처)
- **applicants**: 신청자 정보 (이름, 연락처)
- **supply_products**: 경비용품 품목 (품목명, 규격, 단가)
- **uniform_products**: 피복 품목 (품목명, 단가)
- **email_recipients**: 이메일 수신자 (업체명, 이메일)

## Tech Stack
- **Frontend**: Streamlit
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **PDF Generation**: ReportLab (한글 폰트: NanumGothicCoding)
- **Data Processing**: pandas
- **Email**: smtplib (Naver SMTP)

## Configuration

### SMTP 설정 (Secrets)
이메일 전송을 위해 다음 시크릿을 설정해야 합니다:
- `SMTP_EMAIL`: Naver 계정 이메일
- `SMTP_PASSWORD`: Naver 앱 비밀번호

### 이메일 수신처
- 피복 신청: bbs0747@hanmail.net (경원피복)
- 경비물품 신청: jay@jaynuri.com (제이누리)

### 데이터베이스
- `DATABASE_URL` 환경변수로 PostgreSQL 연결
- 앱 시작 시 자동으로 테이블 생성 및 기존 데이터 마이그레이션

## Recent Changes
- 2026-01-21: 폰트 문제 해결
  - 프로젝트 내 fonts/ 폴더에 한글 폰트(NanumGothicCoding) 포함
  - 시스템 폰트 대신 프로젝트 폰트 우선 사용으로 환경 간 일관성 확보
  - 개발/프로덕션 환경 모두에서 PDF 생성 정상 작동
- 2026-01-21: 임시저장/재신청 품목 데이터 구조 수정
  - 새로운 3품목 구조(품목1~3, 수량1~3)로 자동 변환
- 2026-01-19: 관리자 모드 데이터 PostgreSQL 마이그레이션
  - 현장, 신청자, 경비용품, 피복 품목, 이메일 수신자 데이터를 DB에 저장
  - JSON 파일 기반에서 PostgreSQL 기반으로 변경
  - 배포 후에도 관리자 모드에서 등록한 데이터가 유지됨
- 2026-01-19: 월별 집계 및 신청 내역 PostgreSQL 마이그레이션
  - Excel 파일 기반에서 PostgreSQL 기반으로 변경
  - 기존 Excel 데이터 자동 마이그레이션
  - 월별 집계에서 현장 추가/삭제/예산 수정 기능
- 2026-01-13: 품목 단가 관리 기능 추가
  - 관리자 모드에 경비용품 품목 관리 탭 추가 (품목명, 규격, 단가)
  - 관리자 모드에 피복 품목 관리 탭 추가 (품목명, 단가)
  - 신청서 작성 시 등록된 품목 선택하면 단가 자동 적용
- 2026-01-13: 관리자 모드 및 자동완성 기능 추가
- 2026-01-13: 초기 시스템 구축

## Usage
1. 사이드바에서 법인명(미래/다원)과 신청 유형(경비물품/피복) 선택
2. 기본 정보 입력 (현장명, 신청자, 주소 등)
3. 품목 입력 (Data Editor에서 추가/수정)
4. "신청서 생성" 버튼 클릭하여 PDF 생성
5. "데이터 저장" 버튼 클릭하여 DB에 저장
6. "이메일 전송" 버튼 클릭하여 담당자에게 발송

## Running the Application
```bash
streamlit run app.py --server.port 5000
```
