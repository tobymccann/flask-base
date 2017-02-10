from flask import Blueprint

projects = Blueprint('projects', __name__)

from . import views  # noqa
from .context_processors import inject_all_project_data