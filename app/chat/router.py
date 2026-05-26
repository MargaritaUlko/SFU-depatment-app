from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import decode_token
from app.chat.crud import (
    create_group_chat,
    get_all_chats,
    get_chat,
    get_chat_messages,
    get_or_create_direct_chat,
    get_user_chats,
    save_message,
)
from app.chat.manager import manager
from app.chat.schemas import ChatMessageCreate, ChatMessageRead, ChatRead, GroupChatCreate
from app.db.session import get_db
from app.dependencies import get_current_user
from app.users.crud import get_user
from app.users.model import Role

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=List[ChatRead])
async def list_chats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role == Role.admin:
        return await get_all_chats(db)
    return await get_user_chats(db, current_user.id)


@router.post(
    "/direct/{user_id}", response_model=ChatRead, status_code=status.HTTP_201_CREATED
)
async def open_direct_chat(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя создать чат с собой")
    other = await get_user(db, user_id)
    if not other:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return await get_or_create_direct_chat(db, current_user.id, user_id)


@router.post("/group", response_model=ChatRead, status_code=status.HTTP_201_CREATED)
async def create_group_chat_route(
    body: GroupChatCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.id not in body.member_ids:
        body.member_ids.append(current_user.id)
    return await create_group_chat(db, body.group_id, body.member_ids)


@router.get("/{chat_id}/messages", response_model=List[ChatMessageRead])
async def list_messages(
    chat_id: int,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    chat = await get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    if current_user.role != Role.admin and current_user.id not in {m.user_id for m in chat.members}:
        raise HTTPException(status_code=403, detail="Нет доступа к чату")
    return await get_chat_messages(db, chat_id, limit=limit, offset=offset)


@router.post("/{chat_id}/messages", response_model=ChatMessageRead, status_code=status.HTTP_201_CREATED)
async def send_message(
    chat_id: int,
    body: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    chat = await get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    if current_user.role != Role.admin and current_user.id not in {m.user_id for m in chat.members}:
        raise HTTPException(status_code=403, detail="Нет доступа к чату")
    msg = await save_message(db, chat_id, current_user.id, body.body)
    await manager.broadcast(chat_id, {
        "id": msg.id,
        "chat_id": chat_id,
        "sender_id": current_user.id,
        "body": body.body,
        "created_at": msg.created_at.isoformat(),
    })
    return msg


@router.websocket("/{chat_id}/ws")
async def websocket_chat(
    chat_id: int,
    ws: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    await ws.accept()

    payload = decode_token(token)
    if not payload:
        await ws.close(code=4001)
        return

    user = await get_user(db, int(payload["sub"]))
    if not user or not user.is_active:
        await ws.close(code=4001)
        return

    chat = await get_chat(db, chat_id)
    if not chat or user.id not in {m.user_id for m in chat.members}:
        await ws.close(code=4003)
        return

    await manager.connect(chat_id, ws)
    try:
        while True:
            body = await ws.receive_text()
            if not body.strip():
                continue
            msg = await save_message(db, chat_id, user.id, body)
            await manager.broadcast(
                chat_id,
                {
                    "id": msg.id,
                    "chat_id": chat_id,
                    "sender_id": user.id,
                    "body": body,
                    "created_at": msg.created_at.isoformat(),
                },
            )
    except WebSocketDisconnect:
        manager.disconnect(chat_id, ws)
