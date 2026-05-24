from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.model import Document
from app.documents.schemas import DocumentUpdate
from app.groups.model import Group
from app.users.model import Role, StudentProfile, User


async def create_document(
    db: AsyncSession,
    title: str,
    description: Optional[str],
    category: str,
    visibility: List[str],
    file_path: str,
    file_name: str,
    uploader_id: int,
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


async def get_user_access_context(
    db: AsyncSession, user: User
) -> tuple[str, Optional[int], Optional[int]]:
    group_id = None
    stream_id = None
    if user.role in (Role.student, Role.headman):
        res = await db.execute(
            select(StudentProfile.group_id, Group.stream_id)
            .join(Group, Group.id == StudentProfile.group_id, isouter=True)
            .where(StudentProfile.user_id == user.id)
        )
        row = res.one_or_none()
        if row:
            group_id, stream_id = row
    return user.role.value, group_id, stream_id


def _user_can_see(
    doc: Document,
    role_value: str,
    group_id: Optional[int],
    stream_id: Optional[int],
) -> bool:
    checks = {f"role:{role_value}"}
    if group_id is not None:
        checks.add(f"group:{group_id}")
    if stream_id is not None:
        checks.add(f"stream:{stream_id}")
    return bool(checks & set(doc.visibility or []))


async def get_documents(db: AsyncSession, user: User) -> List[Document]:
    role_value, group_id, stream_id = await get_user_access_context(db, user)
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    return [d for d in docs if _user_can_see(d, role_value, group_id, stream_id)]


async def get_document(db: AsyncSession, doc_id: int) -> Optional[Document]:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    return result.scalar_one_or_none()


async def update_document(
    db: AsyncSession, doc: Document, data: DocumentUpdate
) -> Document:
    if data.title is not None:
        doc.title = data.title
    if data.description is not None:
        doc.description = data.description
    if data.category is not None:
        doc.category = data.category
    if data.visibility is not None:
        doc.visibility = data.visibility
    await db.commit()
    await db.refresh(doc)
    return doc


async def delete_document(db: AsyncSession, doc: Document) -> None:
    await db.delete(doc)
    await db.commit()
