import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


EMAIL_CONFIG = {
    '피복': {
        'to': 'bbs0747@hanmail.net',
        'vendor_name': '경원피복',
        'subject_prefix': '피복 신청서'
    },
    '경비물품': {
        'to': 'jay@jaynuri.com',
        'vendor_name': '제이누리',
        'subject_prefix': '경비물품 신청서'
    }
}

def get_default_email(app_type):
    """신청 유형별 기본 수신자 이메일 반환"""
    config = EMAIL_CONFIG.get(app_type, EMAIL_CONFIG['경비물품'])
    return config['to']

def get_vendor_name(app_type):
    """신청 유형별 업체명 반환"""
    config = EMAIL_CONFIG.get(app_type, EMAIL_CONFIG['경비물품'])
    return config.get('vendor_name', '')


def send_email(smtp_email, smtp_password, to_email, subject, body, attachment_path=None):
    """네이버 SMTP를 통한 이메일 전송"""
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            filename = os.path.basename(attachment_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            msg.attach(part)
        
        server = smtplib.SMTP('smtp.naver.com', 587)
        server.starttls()
        server.login(smtp_email, smtp_password)
        
        text = msg.as_string()
        server.sendmail(smtp_email, to_email, text)
        server.quit()
        
        return True, "이메일이 성공적으로 전송되었습니다."
    
    except smtplib.SMTPAuthenticationError:
        return False, "이메일 인증에 실패했습니다. 네이버 메일 설정에서 SMTP 사용을 활성화하고 비밀번호를 확인해주세요."
    except smtplib.SMTPException as e:
        return False, f"이메일 전송 중 오류가 발생했습니다: {str(e)}"
    except Exception as e:
        return False, f"예상치 못한 오류가 발생했습니다: {str(e)}"


def send_application_email(smtp_email, smtp_password, app_type, company, site_name, pdf_path, custom_to_email=None):
    """신청서 이메일 전송"""
    config = EMAIL_CONFIG.get(app_type, EMAIL_CONFIG['경비물품'])
    
    to_email = custom_to_email if custom_to_email else config['to']
    subject = f"[{company}] {site_name} {config['subject_prefix']}"
    
    body = f"""안녕하세요.

{company} {site_name}에서 {app_type} 신청서를 보내드립니다.

첨부된 신청서를 확인해 주시기 바랍니다.

감사합니다.
"""
    
    return send_email(smtp_email, smtp_password, to_email, subject, body, pdf_path)
