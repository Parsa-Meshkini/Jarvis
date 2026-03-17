import logging
import urllib.parse
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import (
    get_user_by_email, create_user,
    verify_password, create_token
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(redirect_slashes=False)

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL  = "https://www.googleapis.com/oauth2/v2/userinfo"

# Scopes — profile + email + calendar
GOOGLE_SCOPES = " ".join([
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/calendar",
])


class RegisterRequest(BaseModel):
    name:     str
    email:    str
    password: str


class LoginRequest(BaseModel):
    email:    str
    password: str


class AuthResponse(BaseModel):
    token: str
    user:  dict


@router.post("/auth/register", response_model=AuthResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(body.email, db)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user  = await create_user(body.name, body.email, body.password, db)
    token = create_token(str(user.id), user.email)
    return AuthResponse(
        token=token,
        user={"id": str(user.id), "name": user.name, "email": user.email},
    )


@router.post("/auth/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(body.email, db)
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(str(user.id), user.email)
    return AuthResponse(
        token=token,
        user={"id": str(user.id), "name": user.name, "email": user.email},
    )


@router.get("/auth/google")
async def google_login():
    """Redirect user to Google OAuth consent screen."""
    params = {
        "client_id":     settings.GOOGLE_CLIENT_ID,
        "redirect_uri":  settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         GOOGLE_SCOPES,
        "access_type":   "offline",   # get refresh token
        "prompt":        "consent",   # always show consent to get refresh token
    }
    query = urllib.parse.urlencode(params)
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{query}")


@router.get("/auth/google/callback")
async def google_callback(code: str = None, error: str = None, db: AsyncSession = Depends(get_db)):
    """Google redirects here after user consents."""

    if error:
        logger.error(f"Google OAuth error: {error}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error={error}")

    if not code:
        logger.error("No code received from Google")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=no_code")

    try:
        async with httpx.AsyncClient() as client:
            # Exchange code for tokens
            token_res = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code":          code,
                    "client_id":     settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri":  settings.GOOGLE_REDIRECT_URI,
                    "grant_type":    "authorization_code",
                },
            )
            tokens = token_res.json()
            logger.info(f"Token exchange response: {token_res.status_code}")

            if "error" in tokens:
                logger.error(f"Token error: {tokens}")
                return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=token_failed")

            # Get user info
            user_res = await client.get(
                GOOGLE_USER_URL,
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            google_user = user_res.json()
            logger.info(f"Google user: {google_user.get('email')}")

        email         = google_user.get("email")
        name          = google_user.get("name", email)
        refresh_token = tokens.get("refresh_token", "")

        if not email:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=no_email")

        # Find or create user
        user = await get_user_by_email(email, db)
        if not user:
            user = await create_user(
                name=name,
                email=email,
                password="google-oauth",
                db=db,
            )

        # Save Google tokens to memory
        if refresh_token:
            from app.agents.memory import save_preference
            await save_preference("google_refresh_token", refresh_token)
            await save_preference("google_calendar_email", email)
            await save_preference("name", name)

        # Create JWT
        token = create_token(str(user.id), user.email)

        import urllib.parse
        redirect_url = (
            f"{settings.FRONTEND_URL}/auth/callback"
            f"?token={token}"
            f"&name={urllib.parse.quote(name)}"
            f"&email={urllib.parse.quote(email)}"
        )
        logger.info(f"Redirecting to: {redirect_url}")
        return RedirectResponse(url=redirect_url)

    except Exception as exc:
        logger.error(f"Google callback error: {exc}", exc_info=True)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=server_error")