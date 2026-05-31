import logging
import urllib.parse
from urllib.parse import urlencode
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, AsyncSessionLocal
from app.services.auth_service import (
    get_user_by_email, create_user,
    verify_password, create_token
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(redirect_slashes=False)

# 303 See Other — follow with GET (clearer than 307 for OAuth flows)
_BROWSER_REDIRECT = 303

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
@router.get("/auth/google/")
async def google_login(request: Request):
    """Redirect user to Google OAuth consent screen."""
    # Use the configured redirect URI (must match Google Console exactly)
    params = {
        "client_id":     settings.GOOGLE_CLIENT_ID,
        "redirect_uri":  settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         GOOGLE_SCOPES,
        "access_type":   "offline",
        "prompt":        "consent",
    }
    query = urllib.parse.urlencode(params)
    redirect_to = f"{GOOGLE_AUTH_URL}?{query}"
    logger.info(
        "Google OAuth consent redirect host=%s (status HTML redirect)",
        urllib.parse.urlparse(redirect_to).netloc,
    )
    safe_url = redirect_to.replace("\\", "\\\\").replace("'", "\\'")
    html = f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Redirecting…</title>
    <script>
      window.location.replace('{safe_url}');
    </script>
  </head>
  <body>
    Redirecting to <a href="{redirect_to}">{redirect_to}</a>…
  </body>
</html>"""
    return HTMLResponse(
        content=html,
        status_code=200,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
    )


def _frontend_redirect(path: str) -> RedirectResponse:
    """Redirect browser to the SPA.

    Using an HTML + JS redirect can avoid some browsers blocking https->http
    navigation that sometimes happens with plain HTTP redirects.
    """
    base = settings.FRONTEND_URL.rstrip("/")
    url = f"{base}{path}" if path.startswith("/") else f"{base}/{path}"

    safe_url = url.replace("\\", "\\\\").replace("'", "\\'")
    html = f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Redirecting…</title>
    <script>
      window.location.replace('{safe_url}');
    </script>
  </head>
  <body>
    Redirecting to <a href="{url}">{url}</a>…
  </body>
</html>"""
    return HTMLResponse(content=html, status_code=200)


@router.get("/auth/google/callback")
async def google_callback(request: Request):
    """Google redirects here after user consents (may include iss, scope, authuser, etc.)."""

    qp = request.query_params
    error = qp.get("error")
    code = qp.get("code")

    if error:
        logger.error(f"Google OAuth error: {error}")
        return _frontend_redirect(f"/login?{urlencode({'error': error})}")

    if not code or not str(code).strip():
        logger.error(
            "No code in callback — query keys: %s",
            list(qp.keys()),
        )
        return _frontend_redirect(f"/login?{urlencode({'error': 'no_code'})}")

    try:
        # Avoid `get_db` dependency cleanup surprises by managing DB session here.
        async with AsyncSessionLocal() as db:
            async with httpx.AsyncClient(timeout=30.0) as client:
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
                    return _frontend_redirect(f"/login?{urlencode({'error': 'token_failed'})}")

                # Get user info
                user_res = await client.get(
                    GOOGLE_USER_URL,
                    headers={"Authorization": f"Bearer {tokens['access_token']}"},
                )
                google_user = user_res.json()
                logger.info(f"Google user: {google_user.get('email')}")

            email = google_user.get("email")
            name = google_user.get("name", email)
            refresh_token = tokens.get("refresh_token", "")

            if not email:
                return _frontend_redirect(f"/login?{urlencode({'error': 'no_email'})}")

            # Find or create user
            user = await get_user_by_email(email, db)
            is_new_user = False
            if not user:
                is_new_user = True
                user = await create_user(
                    name=name,
                    email=email,
                    password="google-oauth",
                    db=db,
                )

            # Save Google tokens to memory (uses its own sessions internally)
            if refresh_token:
                from app.agents.memory import save_preference
                await save_preference("google_refresh_token", refresh_token)
                await save_preference("google_calendar_email", email)
                await save_preference("name", name)

            # Create JWT — must be url-encoded in query string (JWT can contain +, =, &)
            token = create_token(str(user.id), user.email)
            redirect_url = (
                f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback?"
                + urlencode(
                    {
                        "token": token,
                        "name": name,
                        "email": email,
                        "id": str(user.id),
                        "is_new_user": "1" if is_new_user else "0",
                    }
                )
            )
            logger.info(
                "Google OAuth redirect (FRONTEND_URL=%s, destination_host=%s)",
                settings.FRONTEND_URL,
                urllib.parse.urlparse(redirect_url).netloc,
            )
            return HTMLResponse(
                content=f"""<!doctype html>
<html><head><meta charset="utf-8" /><script>
window.location.replace({redirect_url!r});
</script></head><body>Redirecting…</body></html>""",
                status_code=200,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
            )

    except Exception as exc:
        logger.error(f"Google callback error: {exc}", exc_info=True)
        return _frontend_redirect(f"/login?{urlencode({'error': 'server_error'})}")