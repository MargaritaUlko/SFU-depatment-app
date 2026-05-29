import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LogoutRequest, PasswordResetRequest, RefreshRequest, TokenResponse
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
from app.core.email import send_credentials_email, send_password_reset_email
from app.core.security import generate_password, hash_password
from app.users.crud import authenticate_user, create_student_profile, create_user, get_user, get_user_by_email, get_me_profile
from app.users.model import Role, User
from app.users.schemas import StudentRegister, UserCreate, UserRead
from app.users.service import build_me_response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: StudentRegister, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже зарегистрирован"
        )
    user_data = UserCreate(
        name=data.name,
        surname=data.surname,
        patronymic=data.patronymic,
        email=data.email,
        password=data.password,
        role=Role.student,
    )
    user = await create_user(db, user_data)
    await create_student_profile(db, user.id, data.group_id)
    return user


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


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(data: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    if not user:
        return
    new_password = generate_password()
    user.hashed_password = await asyncio.to_thread(hash_password, new_password)
    await db.commit()
    full_name = f"{user.surname} {user.name}"
    try:
        await send_password_reset_email(user.email, full_name, new_password)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("Не удалось отправить письмо %s: %s", user.email, exc)


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile_data = await get_me_profile(db, current_user)
    return build_me_response(current_user, profile_data)
