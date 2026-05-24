import os
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.file_storage import save_upload_file
from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.documents.crud import (
    _user_can_see,
    create_document,
    delete_document,
    get_document,
    get_documents,
    get_user_access_context,
    update_document,
)
from app.documents.schemas import DocumentRead, DocumentUpdate
from app.groups.model import Group
from app.streams.model import Stream
from app.users.model import Role

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=List[DocumentRead])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_documents(db, current_user)


# TODO: переделать
async def _parse_and_validate_visibility(raw: str, db: AsyncSession) -> List[str]:
    import json

    try:
        stripped = raw.strip()
        if stripped.startswith("["):
            vis_list: List[str] = json.loads(stripped)
        else:
            vis_list = [v.strip() for v in stripped.split(",") if v.strip()]
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректный формат visibility",
        )

    valid_roles = {r.value for r in Role}
    for entry in vis_list:
        if ":" not in entry:
            if entry not in valid_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Неизвестная роль: {entry}",
                )
        elif entry.startswith("role:"):
            if entry[5:] not in valid_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Неизвестная роль: {entry[5:]}",
                )
        elif entry.startswith("group:"):
            try:
                group_id = int(entry[6:])
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Некорректный ID группы: {entry}",
                )
            res = await db.execute(select(Group).where(Group.id == group_id))
            if not res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Группа не найдена: {group_id}",
                )
        elif entry.startswith("stream:"):
            try:
                stream_id = int(entry[7:])
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Некорректный ID потока: {entry}",
                )
            res = await db.execute(select(Stream).where(Stream.id == stream_id))
            if not res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Поток не найден: {stream_id}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неизвестный формат: {entry}. Используйте role:..., group:..., stream:...",
            )
    return vis_list


# TODO: переделать
@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: str = Form(...),
    visibility: str = Form(
        ...,
        description=(
            "Список через запятую. Форматы: "
            "role:student, role:teacher, group:5, stream:2"
        ),
    ),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.deputy_head, Role.admin)),
):
    vis_list = await _parse_and_validate_visibility(visibility, db)

    directory = os.path.join(settings.UPLOAD_DIR, "documents")
    file_path, original_name = await save_upload_file(file, directory)

    return await create_document(
        db,
        title=title,
        description=description,
        category=category,
        visibility=vis_list,
        file_path=file_path,
        file_name=original_name,
        uploader_id=current_user.id,
    )


@router.get("/{doc_id}", response_model=DocumentRead)
async def get_document_metadata(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден"
        )
    role_value, group_id, stream_id = await get_user_access_context(db, current_user)
    if not _user_can_see(doc, role_value, group_id, stream_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден"
        )
    return doc


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    doc = await get_document(db, doc_id)
    role_value, group_id, stream_id = await get_user_access_context(db, current_user)
    if not doc or not _user_can_see(doc, role_value, group_id, stream_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден"
        )
    if not os.path.exists(doc.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден на сервере"
        )
    return FileResponse(
        path=doc.file_path,
        filename=doc.file_name,
        media_type="application/octet-stream",
    )


@router.put("/{doc_id}", response_model=DocumentRead)
async def update_document_metadata(
    doc_id: int,
    data: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.headman, Role.admin)),
):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден"
        )
    if data.visibility is not None:
        data.visibility = await _parse_and_validate_visibility(
            ",".join(data.visibility), db
        )
    return await update_document(db, doc, data)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_endpoint(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.admin)),
):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден"
        )
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    await delete_document(db, doc)
