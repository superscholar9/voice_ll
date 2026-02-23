"""Email service for sending verification emails."""
from datetime import datetime, timedelta
from jose import jwt
from aiosmtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


def create_verification_token(email: str) -> str:
    """Create email verification token."""
    expire = datetime.utcnow() + timedelta(minutes=settings.VERIFICATION_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "verification"
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")


def verify_verification_token(token: str) -> str | None:
    """Verify email verification token and return email."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "verification":
            return None
        return payload.get("sub")
    except Exception:
        return None


async def send_verification_email(email: str, username: str) -> bool:
    """Send email verification link."""
    token = create_verification_token(email)
    verification_url = f"{settings.FRONTEND_URL}/verify?token={token}"
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Verify your VoiceClone.ai account"
    message["From"] = settings.VERIFICATION_EMAIL_FROM
    message["To"] = email
    
    html = f"""
    <html>
      <body>
        <h2>Welcome to VoiceClone.ai, {username}!</h2>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{verification_url}">Verify Email</a></p>
        <p>This link will expire in {settings.VERIFICATION_TOKEN_EXPIRE_MINUTES} minutes.</p>
      </body>
    </html>
    """
    
    message.attach(MIMEText(html, "html"))
    
    try:
        async with SMTP(hostname=settings.SMTP_HOST, port=settings.SMTP_PORT) as smtp:
            await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            await smtp.send_message(message)
        return True
    except Exception:
        return False
