# Import all models so Alembic can discover them via Base.metadata
from app.users.model import User, Role, StudentProfile, TeacherProfile, DeanProfile  # noqa
from app.auth.model import RefreshToken  # noqa
from app.streams.model import Stream  # noqa
from app.groups.model import Group  # noqa
from app.messages.model import Message, TargetType  # noqa
from app.documents.model import Document  # noqa
from app.rooms.model import Room  # noqa
from app.announcements.model import Announcement, Attachment, AnnouncementStatus  # noqa
from app.schedule.model import Schedule  # noqa
from app.attendance.model import AttendanceReport  # noqa
from app.events.model import Event  # noqa
from app.notifications.model import Notification, NotificationReceipt  # noqa
