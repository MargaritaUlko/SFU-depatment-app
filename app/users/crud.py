from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.groups.model import Group
from app.lessons.model import Lesson
from app.users.model import DeanProfile, Role, StudentProfile, TeacherProfile, User
from app.users.schemas import DeanProfileUpdate, StudentProfileUpdate, TeacherProfileUpdate, UserCreate


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_visible_users(
    db: AsyncSession,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
) -> List[User]:
    if current_user.role in (Role.admin, Role.dean, Role.deputy_head):
        result = await db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    if current_user.role in (Role.student, Role.headman):
        group_subq = select(StudentProfile.group_id).where(
            StudentProfile.user_id == current_user.id
        )
        groupmates_subq = select(StudentProfile.user_id).where(
            StudentProfile.group_id.in_(group_subq)
        )
        q = (
            select(User)
            .where(User.id.in_(groupmates_subq) | (User.role == Role.teacher))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(q)
        return list(result.scalars().all())

    if current_user.role == Role.teacher:
        taught_groups_subq = (
            select(Lesson.group_id).where(Lesson.teacher_id == current_user.id).distinct()
        )
        students_subq = select(StudentProfile.user_id).where(
            StudentProfile.group_id.in_(taught_groups_subq)
        )
        q = (
            select(User)
            .where(User.id.in_(students_subq) | (User.role == Role.deputy_head))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(q)
        return list(result.scalars().all())

    return []


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    user = User(
        email=data.email,
        name=data.name,
        surname=data.surname,
        patronymic=data.patronymic,
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    await db.flush()

    if data.role in (Role.teacher, Role.deputy_head):
        db.add(TeacherProfile(user_id=user.id))
    elif data.role == Role.dean:
        db.add(DeanProfile(user_id=user.id))

    await db.commit()
    await db.refresh(user)
    return user


async def create_student_profile(db: AsyncSession, user_id: int, group_id: int) -> StudentProfile:
    profile = StudentProfile(user_id=user_id, group_id=group_id)
    db.add(profile)
    await db.commit()
    return profile


async def get_teachers(db: AsyncSession, skip: int = 0, limit: int = 100):
    q = (
        select(User, TeacherProfile)
        .outerjoin(TeacherProfile, TeacherProfile.user_id == User.id)
        .where(User.role.in_([Role.teacher, Role.deputy_head]))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(q)
    return result.all()


async def update_student_profile(db: AsyncSession, user: User, data: StudentProfileUpdate) -> None:
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise ValueError("Профиль не найден. Группа назначается деканатом")
    for field in ("phone", "telegram", "vk"):
        value = getattr(data, field)
        if value is not None:
            setattr(profile, field, value)
    await db.commit()


async def update_student_group(db: AsyncSession, user_id: int, group_id: int) -> None:
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = StudentProfile(user_id=user_id, group_id=group_id)
        db.add(profile)
    else:
        profile.group_id = group_id
    await db.commit()


async def update_teacher_profile(db: AsyncSession, user: User, data: TeacherProfileUpdate) -> None:
    result = await db.execute(select(TeacherProfile).where(TeacherProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = TeacherProfile(user_id=user.id)
        db.add(profile)
        await db.flush()
    for field in ("department", "positions", "phone", "cabinet"):
        value = getattr(data, field)
        if value is not None:
            setattr(profile, field, value)
    await db.commit()


async def update_dean_profile(db: AsyncSession, user: User, data: DeanProfileUpdate) -> None:
    result = await db.execute(select(DeanProfile).where(DeanProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = DeanProfile(user_id=user.id, faculty=data.faculty or "")
        db.add(profile)
        await db.flush()
    for field in ("faculty", "position", "phone", "cabinet"):
        value = getattr(data, field)
        if value is not None:
            setattr(profile, field, value)
    await db.commit()


async def update_user(db: AsyncSession, user: User, data: dict) -> User:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_password(db: AsyncSession, user: User, data: dict) -> User:
    user.hashed_password = hash_password(data.new_password)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_role(db: AsyncSession, user: User, role: Role) -> User:
    user.role = role
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_avatar(db: AsyncSession, user: User, file_path: str) -> User:
    user.avatar = file_path
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.commit()


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def search_users_by_surname(
    db: AsyncSession, surname: str, skip: int = 0, limit: int = 100
) -> List[User]:
    result = await db.execute(
        select(User).where(User.surname.ilike(f"%{surname}%")).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_groups_by_teacher(db: AsyncSession, teacher_id: int) -> list[Group]:
    q = (
        select(Group.id)
        .join(Lesson, Lesson.group_id == Group.id)
        .where(Lesson.teacher_id == teacher_id)
        .distinct()
    )
    result = await db.execute(q)
    return list(result.scalars().all())
