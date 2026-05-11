from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.streams.crud import create_stream, delete_stream, get_stream, get_streams, update_stream
from app.streams.schemas import StreamCreate, StreamRead, StreamUpdate
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
    _=Depends(require_roles(Role.dean, Role.admin)),
):
    return await create_stream(db, data)


@router.get("/{stream_id}", response_model=StreamRead)
async def get_stream_endpoint(
    stream_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stream = await get_stream(db, stream_id)
    if stream is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Поток не найден")
    return stream



@router.patch("/{stream_id}", response_model=StreamRead)
async def update_stream_endpoint(
    stream_id: int,
    data: StreamUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.dean, Role.admin)),
):
    stream = await get_stream(db, stream_id)
    if stream is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Поток не найден")
    return await update_stream(db, stream, data)


@router.delete("/{stream_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stream_endpoint(
    stream_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.dean, Role.admin)),
):
    stream = await get_stream(db, stream_id)
    if stream is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Поток не найден")
    await delete_stream(db, stream)
