import re

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.groups.model import Group
from app.lessons.model import Lesson
from app.users.model import Role, User

SFU_API = "https://edu.sfu-kras.ru/api/timetable/get"


async def _fetch_group_timetable(group_name: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(SFU_API, params={"target": group_name})
        response.raise_for_status()
        data = response.json()
    if data.get("type") != "group":
        return []
    return data.get("timetable", [])


def _parse_teacher_name(teacher_name: str) -> tuple[str, str | None, str | None]:
    # "Иванов И.И." -> ("Иванов", "И", "И")
    parts = teacher_name.strip().split(None, 1)
    surname = parts[0] if parts else ""
    if len(parts) < 2:
        return surname, None, None
    letters = re.findall(r"[А-ЯЁA-Z]", parts[1])
    name_initial = letters[0] if len(letters) >= 1 else None
    patronymic_initial = letters[1] if len(letters) >= 2 else None
    return surname, name_initial, patronymic_initial


async def _resolve_teacher(db: AsyncSession, teacher_name: str) -> int | None:
    if not teacher_name:
        return None
    surname, name_initial, patronymic_initial = _parse_teacher_name(teacher_name)
    conditions = [User.surname.ilike(surname), User.role == Role.teacher]
    if name_initial:
        conditions.append(User.name.ilike(f"{name_initial}%"))
    if patronymic_initial:
        conditions.append(User.patronymic.ilike(f"{patronymic_initial}%"))

    result = await db.execute(select(User).where(*conditions))
    users = result.scalars().all()
    # если нашли ровно одного — матч, иначе неоднозначно
    return users[0].id if len(users) == 1 else None


def _parse_time(time_str: str) -> tuple[str, str]:
    # "09:00-10:30" -> ("09:00", "10:30")
    if "-" in time_str:
        parts = time_str.split("-", 1)
        return parts[0].strip(), parts[1].strip()
    return time_str, time_str


async def sync_lessons(db: AsyncSession) -> dict:
    groups_result = await db.execute(select(Group))
    groups = list(groups_result.scalars().all())

    created = 0
    skipped = 0
    errors: list[str] = []

    for group in groups:
        try:
            timetable = await _fetch_group_timetable(group.name)
        except Exception as e:
            errors.append(f"{group.name}: {e}")
            continue

        for entry in timetable:
            subject = entry.get("subject") or entry.get("name", "")
            if not subject:
                continue

            day = int(entry.get("day", 0))
            week = int(entry.get("week", 0))
            time_start, time_end = _parse_time(entry.get("time", ""))

            existing = await db.execute(
                select(Lesson).where(
                    Lesson.group_id == group.id,
                    Lesson.day == day,
                    Lesson.week == week,
                    Lesson.time_start == time_start,
                    Lesson.subject == subject,
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            teacher_name = entry.get("teacher", "") or ""
            teacher_id = await _resolve_teacher(db, teacher_name)

            db.add(Lesson(
                group_id=group.id,
                teacher_id=teacher_id,
                teacher_name=teacher_name or None,
                day=day,
                week=week,
                time_start=time_start,
                time_end=time_end,
                subject=subject,
                lesson_type=entry.get("type"),
                room=entry.get("room"),
                building=entry.get("building"),
            ))
            created += 1

    await db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}
