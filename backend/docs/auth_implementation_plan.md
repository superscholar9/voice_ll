# Backend Authentication System Implementation Plan

> Generated: 2026-02-06
> Scheme: FastAPI Users + Cloudflare Turnstile
> Database: SQLite with SQLAlchemy Async

## Overview

This plan implements a complete user authentication system with:
- User registration with email verification
- Login with JWT tokens (access + refresh)
- Cloudflare Turnstile integration
- SQLite database with async support
- Backward compatibility with existing API Key auth

## Database Schema

### Users Table
- id: UUID (primary key)
- username: VARCHAR(50) UNIQUE NOT NULL
- email: VARCHAR(255) UNIQUE NOT NULL
- hashed_password: VARCHAR(255) NOT NULL
- is_active: BOOLEAN DEFAULT TRUE
- is_verified: BOOLEAN DEFAULT FALSE
- is_superuser: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

### Refresh Tokens Table
- id: INTEGER (primary key)
- user_id: UUID (foreign key to users)
- token_hash: VARCHAR(255) UNIQUE NOT NULL
- jti: VARCHAR(255) UNIQUE NOT NULL
- expires_at: TIMESTAMP NOT NULL
- revoked_at: TIMESTAMP NULL
- created_at: TIMESTAMP


## API Endpoints

### POST /auth/register
- Request: username, email, password, turnstile_token
- Validates Turnstile token
- Creates user (is_verified=False)
- Sends verification email
- Returns: user_id, message

### POST /auth/login
- Request: username/email, password, turnstile_token
- Validates credentials + Turnstile
- Returns: access_token, refresh_token, token_type

### POST /auth/refresh
- Request: refresh_token
- Validates and rotates refresh token
- Returns: new access_token, new refresh_token

### POST /auth/logout
- Request: refresh_token (optional)
- Revokes refresh token
- Returns: success message

### POST /auth/verify/request
- Request: email
- Sends verification email
- Returns: success message

### GET /auth/verify/confirm?token=xxx
- Validates verification token
- Sets is_verified=True
- Returns: success message

### GET /users/me
- Requires: Bearer token
- Returns: current user info


## Implementation Steps

### Step 1: Database Foundation
1. Create `backend/app/db/base.py` - SQLAlchemy Base
2. Create `backend/app/db/session.py` - Async engine and session
3. Create `backend/app/db/models/user.py` - User model
4. Create `backend/app/db/models/refresh_token.py` - RefreshToken model
5. Initialize Alembic for migrations
6. Generate initial migration

### Step 2: Authentication Core
1. Create `backend/app/auth/deps.py` - FastAPI Users dependencies
2. Create `backend/app/auth/schemas.py` - Pydantic schemas
3. Create `backend/app/auth/token_service.py` - JWT + refresh token logic
4. Configure FastAPI Users with JWT strategy

### Step 3: Cloudflare Turnstile
1. Create `backend/app/services/turnstile.py`
2. Implement server-side verification
3. Add to registration and login endpoints


### Step 4: Email Verification
1. Create `backend/app/services/mailer.py`
2. Implement email sending with SMTP
3. Generate verification tokens (JWT with short expiry)
4. Add verification endpoints

### Step 5: API Routes
1. Create `backend/app/auth/routers/auth.py` - Auth endpoints
2. Create `backend/app/auth/routers/users.py` - User endpoints
3. Register routers in main.py
4. Add CORS configuration for frontend

### Step 6: Configuration
1. Update `backend/.env` with new variables:
   - DATABASE_URL
   - JWT_SECRET_KEY
   - JWT_REFRESH_SECRET_KEY
   - TURNSTILE_SECRET_KEY
   - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
   - VERIFICATION_TOKEN_EXPIRE_MINUTES
2. Update `backend/app/core/config.py` with new settings

### Step 7: Testing & Integration
1. Test registration flow with Turnstile
2. Test login and token refresh
3. Test email verification
4. Verify backward compatibility with API Key auth
5. Update frontend to use new auth endpoints


## Dependencies

Add to `backend/requirements.txt`:

```
# Existing dependencies
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
httpx==0.26.0

# New auth dependencies
fastapi-users[sqlalchemy]==13.0.0
sqlalchemy>=2.0.0
aiosqlite==0.19.0
alembic==1.13.1
python-jose[cryptography]==3.3.0
passlib[argon2]==1.7.4
email-validator==2.1.0
aiosmtplib==3.0.1
```

## Configuration Variables

Add to `backend/.env`:

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./voice_clone.db

# JWT Tokens
JWT_SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
JWT_REFRESH_SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Cloudflare Turnstile
TURNSTILE_SECRET_KEY=<your-turnstile-secret>

# Email Verification
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your-email>
SMTP_PASSWORD=<your-app-password>
VERIFICATION_TOKEN_EXPIRE_MINUTES=60
VERIFICATION_EMAIL_FROM=noreply@voiceclone.ai

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

## Security Considerations

1. **Password Hashing**: Use Argon2 (industry standard)
2. **Token Rotation**: Refresh tokens rotate on each use
3. **Token Revocation**: Store refresh tokens in DB for revocation
4. **Rate Limiting**: Add to registration/login endpoints
5. **Anti-Enumeration**: Generic error messages for login failures
6. **HTTPS**: Enforce in production (use reverse proxy)
7. **CORS**: Whitelist frontend origin only

## Backward Compatibility

Existing API Key authentication remains functional:
- `/api/v1/voice/*` endpoints still accept `X-API-Key` header
- New JWT auth is optional for voice synthesis
- Users can choose either auth method

