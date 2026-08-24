"""Import all models so metadata is populated for Alembic autogenerate."""
from app.models.base import Base  # noqa: F401
from app.models.reference import Category, Department, Priority, SupportTeam  # noqa: F401
from app.models.ticket import (  # noqa: F401
    Ticket, TicketAttachment, TicketMessage, TicketStatusEvent,
)
from app.models.user import (  # noqa: F401
    Permission, RefreshToken, Role, User, role_permissions, user_roles,
)
from app.models.security import (  # noqa: F401
    AuditLog, ClientSession, OTPRecord, PasswordResetToken,
)
from app.models.notification import Notification, NotificationDelivery  # noqa: F401
from app.models.ai import AIAcknowledgment, AIAnalysis  # noqa: F401
