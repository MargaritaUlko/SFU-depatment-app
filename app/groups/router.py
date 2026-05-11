from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.groups.crud import create_group, delete_group, get_group_by_id, get_groups, update_group
from app.groups.schemas import GroupCreate, GroupRead, GroupUpdate
from app.users.model import Role

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=List[GroupRead])
async def list_groups(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await get_groups(db)


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
async def create_group_endpoint(
    data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.dean, Role.admin)),
):
    return await create_group(db, data)


@router.get("/{group_id}", response_model=GroupRead)
async def get_group_endpoint(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    group = await get_group_by_id(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Группа не найдена")
    return group


@router.patch("/{group_id}", response_model=GroupRead)
async def update_group_endpoint(
    group_id: int,
    data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.dean, Role.admin)),
):
    group = await get_group_by_id(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Группа не найдена")
    return await update_group(db, group, data)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group_endpoint(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.dean, Role.admin)),
):
    group = await get_group_by_id(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Группа не найдена")
    await delete_group(db, group)
