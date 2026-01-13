# 경비용품 및 피복 신청 관리 시스템

## Overview
건물관리 회사(미래ABM, 다원PMC)의 경비용품 및 피복 신청을 관리하는 웹 애플리케이션입니다.
사용자가 신청 내용을 입력하면 PDF 신청서가 생성되고, 이메일로 전송되며, 엑셀 파일에 데이터가 저장됩니다.

## Features
1. **PDF 신청서 생성**: 피복신청서 / 경비물품신청서를 각 법인 양식에 맞게 생성
2. **이메일 전송**: 생성된 PDF를 Gmail SMTP를 통해 지정된 담당자에게 전송
3. **엑셀 데이터 관리**: 신청 내역을 엑셀 파일에 저장하고 월별 집계

## Project Architecture
```
├── app.py                 # 메인 Streamlit 애플리케이션
├── pdf_generator.py       # PDF 생성 모듈 (ReportLab)
├── email_sender.py        # 이메일 전송 모듈 (SMTP)
├── excel_handler.py       # 엑셀 데이터 관리 모듈 (pandas, openpyxl)
├── attached_assets/       # 로고 이미지 및 참고 문서
│   ├── 미래ABM_LOGO_*.png
│   └── 다원PMC_LOGO_*.png
├── output/                # 생성된 PDF 파일 저장 폴더
├── fonts/                 # 한글 폰트 폴더
└── management_db.xlsx     # 신청 데이터 저장 엑셀 파일
```

## Tech Stack
- **Frontend**: Streamlit
- **PDF Generation**: ReportLab (한글 폰트: NanumGothicCoding)
- **Data Processing**: pandas, openpyxl
- **Email**: smtplib (Gmail SMTP)

## Configuration

### SMTP 설정 (Secrets)
이메일 전송을 위해 다음 시크릿을 설정해야 합니다:
- `SMTP_EMAIL`: Gmail 계정 이메일
- `SMTP_PASSWORD`: Gmail 앱 비밀번호

### 이메일 수신처
- 피복 신청: bbs0747@hanmail.net (경원피복)
- 경비물품 신청: jay@jaynuri.com (제이누리)

### 네트워크 저장소
- 데이터는 로컬 `management_db.xlsx` 파일에 저장됩니다
- 네트워크 경로(`\\192.168.0.100\보안팀\...`)가 접근 가능한 경우 자동으로 동기화됩니다
- 참고: Replit 환경에서는 Windows 네트워크 공유에 접근할 수 없으므로, 실제 사내망에서 배포 시 동기화가 작동합니다

## Recent Changes
- 2026-01-13: 초기 시스템 구축
  - Streamlit UI 구현 (사이드바, 입력 폼, 데이터 에디터)
  - PDF 생성 기능 구현 (피복신청서, 경비물품신청서)
  - 이메일 전송 모듈 구현
  - 엑셀 데이터 저장 및 월별 집계 기능 구현

## Usage
1. 사이드바에서 법인명(미래/다원)과 신청 유형(경비물품/피복) 선택
2. 기본 정보 입력 (현장명, 신청자, 주소 등)
3. 품목 입력 (Data Editor에서 추가/수정)
4. "신청서 생성" 버튼 클릭하여 PDF 생성
5. "데이터 저장" 버튼 클릭하여 엑셀에 저장
6. "이메일 전송" 버튼 클릭하여 담당자에게 발송

## Running the Application
```bash
streamlit run app.py --server.port 5000
```
