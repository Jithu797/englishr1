import smtplib, os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL")
BASE_URL = os.getenv("BASE_URL")

def send_invite(email: str, name: str, candidate_id: str, password: str, token: str):
    """Email the candidate their credentials + magic link."""
    link = f"{BASE_URL}/?token={token}"

    body = f"""
Hello {name},

You are invited to complete your Round 1 Interview.

Login Details
- Candidate ID: {candidate_id}
- Password: {password}

Access your interview here:
{link}

Please make sure:
- Open the interview in full screen.
- Allow microphone permission when prompted.
- Complete Section 1 (Voice) and Section 2 (Written).

Regards,
Interviewer Community
"""

    msg = MIMEText(body)
    msg["Subject"] = "R1 Interview – Your Login Details"
    msg["From"] = FROM_EMAIL
    msg["To"] = email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_EMAIL, [email], msg.as_string())
