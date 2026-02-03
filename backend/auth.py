"""
DealSnap - OAuth/SSO Authentication
Google OAuth2 integration for user authentication
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

from backend.config import settings


# ============================================================================
# MODELS
# ============================================================================

class TokenData(BaseModel):
    """JWT token payload"""
    sub: str  # User ID (Google sub)
    email: str
    name: str
    exp: datetime


class User(BaseModel):
    """Authenticated user"""
    id: str
    email: str
    name: str
    picture: Optional[str] = None


class AuthToken(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


# ============================================================================
# JWT FUNCTIONS
# ============================================================================

def create_access_token(user: User) -> str:
    """Create JWT access token for authenticated user"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "exp": expire
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode and validate JWT access token"""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return TokenData(
            sub=payload.get("sub"),
            email=payload.get("email"),
            name=payload.get("name"),
            exp=datetime.fromtimestamp(payload.get("exp"))
        )
    except JWTError:
        return None


# ============================================================================
# GOOGLE OAUTH
# ============================================================================

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_google_auth_url(state: str = "") -> str:
    """Generate Google OAuth authorization URL"""
    if not settings.google_client_id:
        raise ValueError("Google OAuth not configured")

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.oauth_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": state
    }

    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


async def exchange_google_code(code: str) -> dict:
    """Exchange authorization code for tokens"""
    if not settings.google_client_id or not settings.google_client_secret:
        raise ValueError("Google OAuth not configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.oauth_redirect_uri,
                "grant_type": "authorization_code"
            }
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to exchange authorization code"
            )

        return response.json()


async def get_google_user_info(access_token: str) -> User:
    """Get user info from Google"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user info"
            )

        data = response.json()

        return User(
            id=data.get("id"),
            email=data.get("email"),
            name=data.get("name"),
            picture=data.get("picture")
        )


# ============================================================================
# DEPENDENCIES
# ============================================================================

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get current authenticated user from JWT token.
    Returns None if not authenticated (allows optional auth).
    """
    if not credentials:
        return None

    token_data = decode_access_token(credentials.credentials)
    if not token_data:
        return None

    # Check expiration
    if token_data.exp < datetime.now(timezone.utc):
        return None

    return User(
        id=token_data.sub,
        email=token_data.email,
        name=token_data.name
    )


async def require_auth(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    Require authenticated user.
    Raises 401 if not authenticated.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def is_oauth_configured() -> bool:
    """Check if OAuth is properly configured"""
    return bool(settings.google_client_id and settings.google_client_secret)
