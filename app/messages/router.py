import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_roles
from app.messages.crud import create_message, get_message, get_messages
from app.messages.schemas import MessageCreate, MessageRead
from app.users.model import Role

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def send_message(
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.headman, Role.admin)),
):
    return await create_message(db, data, current_user.id)


@router.get("", response_model=List[MessageRead])
async def list_messages(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.headman, Role.admin)),
):
    return await get_messages(db, current_user)


@router.get("/{message_id}", response_model=MessageRead)
async def get_message_detail(
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.headman, Role.admin)),
):
    msg = await get_message(db, message_id)
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Сообщение не найдено"
        )
    if current_user.role != Role.admin and msg.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )
    return msg


@router.put("/{message_id}", response_model=MessageRead)
async def update_message(
    message_id: uuid.UUID,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.headman, Role.admin)),
):
    pass


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.headman, Role.admin)),
):
    pass
