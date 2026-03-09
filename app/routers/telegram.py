from fastapi import APIRouter, Depends
from app.dependencies import require_roles
from app.models.user import Role

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/send")
async def telegram_send(
    _=Depends(require_roles(Role.teacher, Role.head, Role.admin)),
):
    """Заглушка отправки в Telegram — всегда возвращает not_implemented."""
    return {"status": "not_implemented"}
