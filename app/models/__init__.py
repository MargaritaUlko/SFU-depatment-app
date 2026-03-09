# Import all models so Alembic can discover them
from app.models.user import User, Role  # noqa
from app.models.refresh_token import RefreshToken  # noqa
from app.models.stream import Stream  # noqa
from app.models.group import Group  # noqa
from app.models.message import Message, TargetType  # noqa
from app.models.event import Event, EventLink  # noqa
from app.models.document import Document  # noqa
