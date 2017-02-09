from flask import Blueprint

tools = Blueprint('tools', __name__)

from . import views  # noqa
