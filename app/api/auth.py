from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import (
    get_user_by_email, create_user,
    verify_password, create_token
)

router = APIRouter()


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


@router.get("/auth/me")
async def get_me(db: AsyncSession = Depends(get_db)):
    # Token validation would go here in production
    return {"message": "authenticated"}