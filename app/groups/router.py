from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.groups.crud import create_group, get_groups
from app.groups.schemas import GroupCreate, GroupRead
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
    _=Depends(require_roles(Role.admin)),
):
    return await create_group(db, data)


@router.get("/{group_id}", response_model=GroupRead)
async def get_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    pass


@router.put("/{group_id}", response_model=GroupRead)
async def update_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    pass


@router.patch("/{group_id}", response_model=GroupRead)
async def partially_update_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    pass


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    pass
