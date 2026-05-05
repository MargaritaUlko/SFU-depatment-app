from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.rooms.crud import create_room, delete_room, get_room, get_rooms, update_room
from app.rooms.schemas import RoomCreate, RoomRead, RoomUpdate
from app.users.model import Role

router = APIRouter(prefix="/rooms", tags=["rooms"])

_manage = Depends(require_roles(Role.dean, Role.deputy_head, Role.admin))


@router.get("", response_model=List[RoomRead])
async def list_rooms(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await get_rooms(db)


@router.post("", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
async def create_room_endpoint(
    data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    _=_manage,
):
    return await create_room(db, data)


@router.get("/{room_id}", response_model=RoomRead)
async def get_room_endpoint(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    room = await get_room(db, room_id)
    if not room:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Комната не найдена")
    return room


@router.patch("/{room_id}", response_model=RoomRead)
async def update_room_endpoint(
    room_id: int,
    data: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    _=_manage,
):
    room = await get_room(db, room_id)
    if not room:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Комната не найдена")
    return await update_room(db, room, data)


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room_endpoint(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    _=_manage,
):
    room = await get_room(db, room_id)
    if not room:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Комната не найдена")
    await delete_room(db, room)
