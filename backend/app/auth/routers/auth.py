"""Authentication routes."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.db.session import get_async_session
from app.db.models import User, RefreshToken
from app.auth.schemas import UserCreate, LoginRequest, TokenResponse, RefreshTokenRequest
from app.auth.token_service import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    hash_token,
)
from app.services.turnstile import verify_turnstile_token
from app.services.mailer import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


@router.post("/register", status_code=201)
async def register(
    user_data: UserCreate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Register a new user with Turnstile verification."""
    # Verify Turnstile token
    client_ip = request.client.host if request.client else None
    is_valid = await verify_turnstile_token(user_data.turnstile_token, client_ip)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid Turnstile token")
    
    # Check if username exists
    result = await session.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    result = await session.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_verified=False,
        is_active=True,
    )
    session.add(new_user)
    await session.commit()
    
    # Send verification email
    await send_verification_email(user_data.email, user_data.username)
    
    return {"message": "Registration successful. Please check your email to verify your account."}


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Login with username/email and password."""
    # Verify Turnstile token
    client_ip = request.client.host if request.client else None
    is_valid = await verify_turnstile_token(login_data.turnstile_token, client_ip)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid Turnstile token")
    
    # Find user by username or email
    result = await session.execute(
        select(User).where(
            (User.username == login_data.username) | (User.email == login_data.username)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or not pwd_context.verify(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    # Create tokens
    access_token = create_access_token(str(user.id))
    refresh_token, jti = create_refresh_token(str(user.id))
    
    # Store refresh token in database
    token_hash = hash_token(refresh_token)
    expires_at = datetime.utcnow() + timedelta(days=7)
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        jti=jti,
        expires_at=expires_at,
    )
    session.add(db_token)
    await session.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Refresh access token using refresh token."""
    # Verify refresh token
    result = verify_refresh_token(refresh_data.refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user_id, jti = result
    
    # Check if token exists and not revoked
    token_hash = hash_token(refresh_data.refresh_token)
    db_result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.jti == jti,
            RefreshToken.revoked_at.is_(None),
        )
    )
    db_token = db_result.scalar_one_or_none()
    
    if not db_token:
        raise HTTPException(status_code=401, detail="Token revoked or not found")
    
    if db_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Token expired")
    
    # Revoke old token
    db_token.revoked_at = datetime.utcnow()
    
    # Create new tokens
    new_access_token = create_access_token(user_id)
    new_refresh_token, new_jti = create_refresh_token(user_id)
    
    # Store new refresh token
    new_token_hash = hash_token(new_refresh_token)
    expires_at = datetime.utcnow() + timedelta(days=7)
    new_db_token = RefreshToken(
        user_id=db_token.user_id,
        token_hash=new_token_hash,
        jti=new_jti,
        expires_at=expires_at,
    )
    session.add(new_db_token)
    await session.commit()
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout")
async def logout(
    refresh_data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Logout by revoking refresh token."""
    token_hash = hash_token(refresh_data.refresh_token)
    
    result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    db_token = result.scalar_one_or_none()
    
    if db_token:
        db_token.revoked_at = datetime.utcnow()
        await session.commit()
    
    return {"message": "Logged out successfully"}


@router.post("/verify/request")
async def request_verification(
    email: str,
    session: AsyncSession = Depends(get_async_session),
):
    """Request email verification link."""
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a verification link has been sent"}
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    await send_verification_email(user.email, user.username)
    return {"message": "Verification email sent"}


@router.get("/verify/confirm")
async def confirm_verification(
    token: str,
    session: AsyncSession = Depends(get_async_session),
):
    """Confirm email verification."""
    from app.services.mailer import verify_verification_token
    
    email = verify_verification_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_verified = True
    await session.commit()
    
    return {"message": "Email verified successfully"}
