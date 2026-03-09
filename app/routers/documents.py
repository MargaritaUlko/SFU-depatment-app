import uuid
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import Role
from app.crud.document import (
    create_document, get_documents, get_document, update_document, delete_document,
    _user_can_see,
)
from app.schemas.document import DocumentRead, DocumentUpdate
from app.dependencies import get_current_user, require_roles
from app.services.file_storage import save_upload_file
from app.core.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=List[DocumentRead])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_documents(db, current_user)


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: str = Form(...),
    visibility: str = Form(..., description='Роли через запятую: student,teacher,head,admin'),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.head, Role.admin)),
):
    import json
    try:
        # Принимаем и JSON ["student","teacher"] и просто student,teacher
        stripped = visibility.strip()
        if stripped.startswith("["):
            vis_list: List[str] = json.loads(stripped)
        else:
            vis_list = [v.strip() for v in stripped.split(",") if v.strip()]
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный формат visibility")

    valid_roles = {r.value for r in Role}
    for r in vis_list:
        if r not in valid_roles:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Неизвестная роль: {r}")

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
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    doc = await get_document(db, doc_id)
    if not doc or not _user_can_see(doc, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")
    return doc


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    doc = await get_document(db, doc_id)
    if not doc or not _user_can_see(doc, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден на сервере")
    return FileResponse(
        path=doc.file_path,
        filename=doc.file_name,
        media_type="application/octet-stream",
    )


@router.put("/{doc_id}", response_model=DocumentRead)
async def update_document_metadata(
    doc_id: uuid.UUID,
    data: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.head, Role.admin)),
):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")
    return await update_document(db, doc, data)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_endpoint(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.admin)),
):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")
    # Удаляем физический файл
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    await delete_document(db, doc)
