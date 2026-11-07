from app.constants import INBOX_STATUSES
from app.schemas.messages import parse_message_update
from app.services import messages

from . import bp
from ._crud import inbox_routes

inbox_routes(bp, "messages", messages, parse_message_update, INBOX_STATUSES)
