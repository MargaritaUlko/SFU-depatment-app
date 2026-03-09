
from sqladmin import ModelView
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.stream import Stream
from app.models.group import Group
from app.models.message import Message
from app.models.event import Event, EventLink
from app.models.document import Document


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-users"

    column_list = [
        User.id,
        User.full_name,
        User.email,
        User.role,
        User.is_active,
        User.created_at,
    ]
    column_searchable_list = [User.email, User.full_name]
    column_sortable_list = [User.email, User.role, User.is_active, User.created_at]
    column_default_sort = [(User.created_at, True)]

    # Не показываем хеш пароля в форме редактирования
    form_excluded_columns = [User.hashed_password]

    column_details_exclude_list = [User.hashed_password]

    can_create = False   # Регистрация через /api/v1/auth/register
    can_delete = True
    can_edit = True
    can_export = True

    column_labels = {
        User.id: "ID",
        User.full_name: "Имя",
        User.email: "Email",
        User.role: "Роль",
        User.is_active: "Активен",
        User.created_at: "Создан",
        User.updated_at: "Изменён",
    }


class RefreshTokenAdmin(ModelView, model=RefreshToken):
    name = "Refresh-токен"
    name_plural = "Refresh-токены"
    icon = "fa-solid fa-key"

    column_list = [
        RefreshToken.id,
        RefreshToken.user_id,
        RefreshToken.jti,
        RefreshToken.expires_at,
        RefreshToken.revoked,
    ]
    column_sortable_list = [RefreshToken.expires_at, RefreshToken.revoked]
    column_default_sort = [(RefreshToken.expires_at, True)]

    can_create = False
    can_edit = True    # можно отозвать (revoked=True)
    can_delete = True
    can_export = False

    column_labels = {
        RefreshToken.id: "ID",
        RefreshToken.user_id: "Пользователь",
        RefreshToken.jti: "JTI",
        RefreshToken.expires_at: "Истекает",
        RefreshToken.revoked: "Отозван",
    }


class StreamAdmin(ModelView, model=Stream):
    name = "Поток"
    name_plural = "Потоки"
    icon = "fa-solid fa-layer-group"

    column_list = [
        Stream.id,
        Stream.name,
        Stream.year,
        Stream.speciality,
        Stream.created_at,
    ]
    column_searchable_list = [Stream.name, Stream.speciality]
    column_sortable_list = [Stream.name, Stream.year, Stream.created_at]
    column_default_sort = [(Stream.year, True)]

    can_create = True
    can_edit = True
    can_delete = True

    column_labels = {
        Stream.id: "ID",
        Stream.name: "Название",
        Stream.year: "Год",
        Stream.speciality: "Специальность",
        Stream.created_at: "Создан",
        Stream.updated_at: "Изменён",
    }


class GroupAdmin(ModelView, model=Group):
    name = "Группа"
    name_plural = "Группы"
    icon = "fa-solid fa-user-group"

    column_list = [
        Group.id,
        Group.name,
        Group.year,
        Group.sfu_timetable_name,
        "stream",
        Group.created_at,
    ]
    column_searchable_list = [Group.name, Group.sfu_timetable_name]
    column_sortable_list = [Group.name, Group.year, Group.created_at]
    column_default_sort = [(Group.year, True)]

    can_create = True
    can_edit = True
    can_delete = True

    column_labels = {
        Group.id: "ID",
        Group.name: "Название",
        Group.year: "Год",
        Group.sfu_timetable_name: "Имя в расписании СФУ",
        "stream": "Поток",
        Group.created_at: "Создан",
        Group.updated_at: "Изменён",
    }


class MessageAdmin(ModelView, model=Message):
    name = "Сообщение"
    name_plural = "Сообщения"
    icon = "fa-solid fa-envelope"

    column_list = [
        Message.id,
        Message.sender_id,
        Message.target_type,
        Message.target_id,
        Message.subject,
        Message.created_at,
    ]
    column_searchable_list = [Message.subject]
    column_sortable_list = [Message.target_type, Message.created_at]
    column_default_sort = [(Message.created_at, True)]

    can_create = False   # Только через API
    can_edit = False
    can_delete = True
    can_export = True

    column_labels = {
        Message.id: "ID",
        Message.sender_id: "Отправитель",
        Message.target_type: "Тип цели",
        Message.target_id: "Цель (ID)",
        Message.subject: "Тема",
        Message.body: "Текст",
        Message.created_at: "Отправлено",
    }


class EventAdmin(ModelView, model=Event):
    name = "Событие"
    name_plural = "События"
    icon = "fa-solid fa-calendar-days"

    column_list = [
        Event.id,
        Event.title,
        Event.starts_at,
        Event.ends_at,
        Event.location,
        Event.creator_id,
        Event.created_at,
    ]
    column_searchable_list = [Event.title, Event.location]
    column_sortable_list = [Event.starts_at, Event.ends_at, Event.created_at]
    column_default_sort = [(Event.starts_at, True)]

    form_excluded_columns = [Event.links, Event.creator]

    can_create = False   # Только через API (нужно загружать links отдельно)
    can_edit = True
    can_delete = True
    can_export = True

    column_labels = {
        Event.id: "ID",
        Event.title: "Название",
        Event.annotation: "Аннотация",
        Event.starts_at: "Начало",
        Event.ends_at: "Конец",
        Event.location: "Место",
        Event.image_url: "Фото",
        Event.creator_id: "Создатель",
        Event.created_at: "Создано",
    }


class EventLinkAdmin(ModelView, model=EventLink):
    name = "Ссылка события"
    name_plural = "Ссылки событий"
    icon = "fa-solid fa-link"

    column_list = [EventLink.id, EventLink.event_id, EventLink.title, EventLink.url]
    column_searchable_list = [EventLink.title, EventLink.url]

    can_create = True
    can_edit = True
    can_delete = True


class DocumentAdmin(ModelView, model=Document):
    name = "Документ"
    name_plural = "Документы"
    icon = "fa-solid fa-file-alt"

    column_list = [
        Document.id,
        Document.title,
        Document.category,
        Document.visibility,
        Document.file_name,
        Document.uploader_id,
        Document.created_at,
    ]
    column_searchable_list = [Document.title, Document.category, Document.file_name]
    column_sortable_list = [Document.category, Document.created_at]
    column_default_sort = [(Document.created_at, True)]

    form_excluded_columns = [Document.uploader, Document.file_path]

    can_create = False   # Только через API (загрузка файла)
    can_edit = True      # Обновление метаданных
    can_delete = True
    can_export = True

    column_labels = {
        Document.id: "ID",
        Document.title: "Название",
        Document.description: "Описание",
        Document.category: "Категория",
        Document.visibility: "Видимость",
        Document.file_name: "Файл",
        Document.file_path: "Путь",
        Document.uploader_id: "Загрузил",
        Document.created_at: "Загружен",
    }
