from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.streams.crud import create_stream, get_streams
from app.streams.schemas import StreamCreate, StreamRead
from app.users.model import Role

router = APIRouter(prefix="/streams", tags=["streams"])


@router.get("", response_model=List[StreamRead])
async def list_streams(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await get_streams(db)


@router.post("", response_model=StreamRead, status_code=status.HTTP_201_CREATED)
async def create_stream_endpoint(
    data: StreamCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.admin)),
):
    return await create_stream(db, data)


@router.get("/{stream_id}", response_model=StreamRead)
async def get_stream(
    stream_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    pass


@router.put("/{stream_id}", response_model=StreamRead)
async def update_stream(
    stream_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    pass


@router.patch("/{stream_id}", response_model=StreamRead)
async def partially_update_stream(
    stream_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    pass


@router.delete("/{stream_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stream(
    stream_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    pass
