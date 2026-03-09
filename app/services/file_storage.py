import os
import uuid
from pathlib import Path
from fastapi import UploadFile


async def save_upload_file(file: UploadFile, directory: str) -> tuple[str, str]:
    """
    Save uploaded file to `directory`.
    Returns (file_path, original_filename).
    """
    os.makedirs(directory, exist_ok=True)
    suffix = Path(file.filename).suffix if file.filename else ""
    stored_name = f"{uuid.uuid4()}{suffix}"
    file_path = os.path.join(directory, stored_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return file_path, file.filename or stored_name
