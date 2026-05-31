import uuid
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import User
import os
from fastapi import Depends, HTTPException, Request

SECRET_KEY = os.getenv("SECRET_KEY", "jarvis-secret-key-change-in-production")
ALGORITHM  = "HS256"
TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: str, email: str) -> str:
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": user_id, "email": email, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return {}


def _extract_bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth:
        return ""
    parts = auth.split(" ", 1)
    if len(parts) != 2:
        return ""
    scheme, token = parts[0].strip().lower(), parts[1].strip()
    if scheme != "bearer":
        return ""
    return token


async def get_current_user(request: Request) -> dict:
    """
    FastAPI dependency that returns JWT claims.
    Raises 401 when token is missing/invalid.
    """
    token = _extract_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    claims = decode_token(token)
    if not claims.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token")
    return claims


async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(name: str, email: str, password: str, db: AsyncSession) -> User:
    user = User(
        name=name,
        email=email,
        password=hash_password(password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user