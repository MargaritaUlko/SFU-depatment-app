import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import Document
from app.models.user import User, Role
from app.schemas.document import DocumentUpdate


async def create_document(
    db: AsyncSession,
    title: str,
    description: Optional[str],
    category: str,
    visibility: List[str],
    file_path: str,
    file_name: str,
    uploader_id: uuid.UUID,
) -> Document:
    doc = Document(
        title=title,
        description=description,
        category=category,
        visibility=visibility,
        file_path=file_path,
        file_name=file_name,
        uploader_id=uploader_id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


def _user_can_see(doc: Document, user: User) -> bool:
    return user.role.value in (doc.visibility or [])


async def get_documents(db: AsyncSession, user: User) -> List[Document]:
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    return [d for d in docs if _user_can_see(d, user)]


async def get_document(db: AsyncSession, doc_id: uuid.UUID) -> Optional[Document]:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    return result.scalar_one_or_none()


async def update_document(db: AsyncSession, doc: Document, data: DocumentUpdate) -> Document:
    if data.title is not None:
        doc.title = data.title
    if data.description is not None:
        doc.description = data.description
    if data.category is not None:
        doc.category = data.category
    if data.visibility is not None:
        doc.visibility = [r.value for r in data.visibility]
    await db.commit()
    await db.refresh(doc)
    return doc


async def delete_document(db: AsyncSession, doc: Document) -> None:
    await db.delete(doc)
    await db.commit()
