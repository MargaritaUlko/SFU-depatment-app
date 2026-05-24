import os
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.file_storage import save_upload_file
from app.users.crud import update_user_avatar
from app.users.model import User

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


async def set_avatar(db: AsyncSession, user: User, file: UploadFile) -> User:
    if Path(file.filename or "").suffix.lower() not in _IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Допустимые форматы: {', '.join(_IMAGE_EXTENSIONS)}",
        )

    old_avatar = user.avatar

    directory = os.path.join(settings.UPLOAD_DIR, "avatars")
    file_path, _ = await save_upload_file(file, directory)

    user = await update_user_avatar(db, user, file_path)

    if old_avatar and os.path.exists(old_avatar):
        os.remove(old_avatar)

    return user
