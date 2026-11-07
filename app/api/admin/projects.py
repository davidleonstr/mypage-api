from app.schemas.projects import parse_project
from app.services import projects

from . import bp
from ._crud import crud_routes

crud_routes(bp, "projects", projects.table, parse_project)
