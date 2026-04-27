import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from app.db.session import get_db
from app.users.crud import get_user_by_email, create_user, authenticate_user, get_user
from app.users.model import Role
from app.users.schemas import UserCreate, UserRead
from app.auth.schemas import TokenResponse, RefreshRequest, LogoutRequest
from app.auth.service import (
    create_access_token,
    create_refresh_token_value,
    save_refresh_token,
    revoke_refresh_token,
    is_refresh_token_valid,
    decode_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже зарегистрирован")
    data.role = Role.student
    return await create_user(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт деактивирован")

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token, jti, expires_at = create_refresh_token_value(str(user.id))
    await save_refresh_token(db, jti, user.id, expires_at)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный refresh-токен")

    jti = payload.get("jti", "")
    if not await is_refresh_token_valid(db, jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен отозван или истёк")

    user_id = uuid.UUID(payload["sub"])
    user = await get_user(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")

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
