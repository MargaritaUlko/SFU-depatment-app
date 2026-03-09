from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import Role
from app.crud.stream import get_streams, create_stream
from app.schemas.stream import StreamCreate, StreamRead
from app.dependencies import get_current_user, require_roles

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
