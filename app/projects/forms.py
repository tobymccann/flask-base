from flask_wtf import FlaskForm
from wtforms.ext.sqlalchemy.orm import model_form
from ..models import Project
from .. import db

ProjectForm = model_form(
    Project,
    base_class=FlaskForm,
    db_session=db.session,
    exclude_fk=True
)
