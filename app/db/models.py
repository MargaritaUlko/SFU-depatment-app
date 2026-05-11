# Import all models so Alembic can discover them via Base.metadata
from app.users.model import User, Role, StudentProfile, TeacherProfile, DeanProfile  # noqa
from app.auth.model import RefreshToken  # noqa
from app.streams.model import Stream  # noqa
from app.groups.model import Group  # noqa
from app.chat.model import Chat, ChatMember, ChatMessage, ChatType  # noqa
from app.documents.model import Document  # noqa
from app.rooms.model import Room  # noqa
from app.announcements.model import Announcement, Attachment, AnnouncementStatus  # noqa
from app.lessons.model import Lesson  # noqa
from app.events.model import Event  # noqa
from app.notifications.model import Notification, NotificationReceipt  # noqa
from app.attendance.model import Attendance, AttendanceToken  # noqa
