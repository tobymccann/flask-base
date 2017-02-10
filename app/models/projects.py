"""
SQLAlchemy data model for the web service
"""
from slugify import Slugify
from .. import db



class Project(db.Model):
    """
    Project
    =======

    Root element of the data model to organize the data within the Web service.

    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(
        db.String(128),
        index=True,
        unique=True,
        nullable=False
    )

    @property
    def name_slug(self):
        return Slugify(to_lower=False)(self.name)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Project %r>' % self.name

    def valid_config_template_name(self, config_template_name):
        """test if the given Config Template name is valid within this Project

        :param config_template_name:
        :return: True if valid, otherwise false
        """
        query_result = self.configtemplates.all()
        valid = True
        if not config_template_name:
            valid = False

        elif config_template_name == "":
            valid = False

        for obj in query_result:
            if obj.name == config_template_name:
                valid = False
                break

        return valid
