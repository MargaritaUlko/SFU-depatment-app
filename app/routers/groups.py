import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import Role
from app.crud.group import get_groups, get_group, create_group
from app.schemas.group import GroupCreate, GroupRead
from app.dependencies import get_current_user, require_roles

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
