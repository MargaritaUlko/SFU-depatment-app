import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.users.crud import (
    create_user,
    get_user,
    get_user_by_email,
    get_users,
    update_user,
)
from app.users.model import Role
from app.users.schemas import UserCreate, UserRead, UserRoleUpdate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.admin)),
):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже зарегистрирован"
        )
    return await create_user(db, data)


@router.get("", response_model=List[UserRead])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.headman, Role.admin)),
):
    return await get_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserRead)
async def get_user_profile(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )
    return user


@router.put("/{user_id}", response_model=UserRead)
async def update_user_profile(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )
    return await update_user(db, user, data)


@router.patch("/{user_id}/role", response_model=UserRead)
async def change_user_role(
    user_id: uuid.UUID,
    data: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.admin)),
):
    pass


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.admin)),
):
    pass
