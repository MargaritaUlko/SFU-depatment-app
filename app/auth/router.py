import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LogoutRequest, RefreshRequest, TokenResponse
from app.auth.service import (
    create_access_token,
    create_refresh_token_value,
    decode_token,
    is_refresh_token_valid,
    revoke_refresh_token,
    save_refresh_token,
)
from app.db.session import get_db
from app.dependencies import get_current_user
from app.users.crud import authenticate_user, create_user, get_user, get_user_by_email
from app.users.model import Role, User
from app.users.schemas import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже зарегистрирован"
        )
    data.role = Role.student
    return await create_user(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт деактивирован"
        )

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token, jti, expires_at = create_refresh_token_value(str(user.id))
    await save_refresh_token(db, jti, user.id, expires_at)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh-токен",
        )

    jti = payload.get("jti", "")
    if not await is_refresh_token_valid(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен отозван или истёк"
        )

    user_id = int(payload["sub"])
    user = await get_user(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден"
        )

    await revoke_refresh_token(db, jti)
    access_token = create_access_token(str(user.id), user.role.value)
    new_refresh, new_jti, expires_at = create_refresh_token_value(str(user.id))
    await save_refresh_token(db, new_jti, user.id, expires_at)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: LogoutRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if payload and payload.get("type") == "refresh":
        jti = payload.get("jti", "")
        await revoke_refresh_token(db, jti)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
