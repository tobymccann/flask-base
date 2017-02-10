from flask_wtf import Form
from .. import db


class ProjectForm():
    project_form = model_form(
        Project,
        base_class=Form,
        db_session=db.session,
        exclude_fk=True
    )