"""Cloudflare Turnstile verification service."""
import httpx
from app.core.config import settings


async def verify_turnstile_token(token: str, remote_ip: str = None) -> bool:
    """
    Verify Cloudflare Turnstile token.
    
    Args:
        token: Turnstile token from frontend
        remote_ip: User's IP address (optional)
    
    Returns:
        True if token is valid, False otherwise
    """
    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    
    payload = {
        "secret": settings.TURNSTILE_SECRET_KEY,
        "response": token,
    }
    
    if remote_ip:
        payload["remoteip"] = remote_ip
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            result = response.json()
            return result.get("success", False)
    except Exception:
        return False
