"""
views for the Project data object
"""
import logging
from flask import render_template, url_for, redirect, request, flash
from sqlalchemy.exc import IntegrityError

from .. import db
from .forms import ProjectForm
from ..models import Project

logger = logging.getLogger()





@projects.route("/project/")
def view_all_projects():
    """view a list of all Projects

    :return:
    """
    return render_template("project/view_all_projects.html", projects=Project.query.all())


@projects.route("/project/<int:project_id>")
def view_project(project_id):
    """View a single Project

    :param project_id:
    :return:
    """
    return render_template(
            "project/view_project.html",
            project=Project.query.filter(Project.id == project_id).first_or_404()
    )


@projects.route("/project/add", methods=["GET", "POST"])
def add_project():
    """add a new Project

    :return:
    """
    form = ProjectForm(request.form)

    if form.validate_on_submit():
        try:
            project = Project(name="")

            project.name = form.name.data
            db.session.add(project)
            db.session.commit()

            flash("Project <strong>%s</strong> successful created" % project.name, "success")

            return redirect(url_for("view_project", project_id=project.id))

        except IntegrityError as ex:
            if "UNIQUE constraint failed" in str(ex):
                msg = "Project name already in use, please use another one"

            else:
                msg = "Project was not created (unknown error, see log for details)"

            flash(msg, "error")
            logger.error(msg, exc_info=True)
            db.session.rollback()

        except Exception:
            msg = "Project was not created (unknown error, see log for details)"
            logger.error(msg, exc_info=True)
            flash(msg, "error")
            db.session.rollback()

    return render_template("project/add_project.html", form=form)


@projects.route("/project/<int:project_id>/edit", methods=["GET", "POST"])
def edit_project(project_id):
    """edit a Project

    :param project_id:
    :return:
    """
    project = Project.query.get(project_id)

    form = ProjectForm(request.form, project)

    if form.validate_on_submit():
        try:
            project.name = form.name.data
            db.session.add(project)
            db.session.commit()

            flash("Project <strong>%s</strong> successful saved" % project.name, "success")

            return redirect(url_for("view_project", project_id=project.id))

        except IntegrityError as ex:
            if "UNIQUE constraint failed" in str(ex):
                msg = "Project name already in use, please use another one"

            else:
                msg = "Project was not saved (unknown error, see log for details)"

            flash(msg, "error")
            logger.error(msg, exc_info=True)
            db.session.rollback()

        except Exception:
            msg = "Project was not saved (unknown error, see log for details)"
            logger.error(msg, exc_info=True)
            flash(msg, "error")
            db.session.rollback()

    return render_template("project/edit_project.html", project=project, form=form)


@projects.route("/project/<int:project_id>/delete", methods=["GET", "POST"])
def delete_project(project_id):
    """delete the Project

    :param project_id:
    :return:
    """
    project = Project.query.filter(Project.id == project_id).first_or_404()

    if request.method == "POST":
        # drop record and add message
        try:
            db.session.delete(project)
            db.session.commit()

        except:
            msg = "Project <strong>%s</strong> was not deleted" % project.name
            flash(msg, "error")
            logger.error(msg, exc_info=True)
            db.session.rollback()

        flash("Project <strong>%s</strong> successful deleted" % project.name, "success")
        return redirect(url_for("view_all_projects"))

    return render_template("project/delete_project.html", project=project)
