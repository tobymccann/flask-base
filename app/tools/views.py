from flask import abort, flash, redirect, render_template, url_for, request, jsonify, make_response, send_file
from flask_login import current_user, login_required

from . import tools
from .. import db
from ..decorators import admin_required
from ..models import Role, User, EditableHTML

"""
views for the Config Template data object
"""
import csv
import logging
import io
from sqlalchemy.exc import IntegrityError

from ..models import ConfigTemplate, Project, TemplateValueSet
from .forms import ConfigTemplateForm, EditConfigTemplateValuesForm
from ..utils.appliance import get_local_ip_addresses, verify_appliance_status
from ..utils.export import get_appliance_ftp_password
from ..tasks import update_local_ftp_configurations, update_local_tftp_configurations

"""
views for the resulting configuration
"""
import zipfile
from io import BytesIO
import time

"""
task queue views for the web service (mainly JSON endpoints for AJAX functions)
"""
from .. import celery

"""
views for the Template Value Set data object
"""
from .forms import TemplateValueSetForm

"""
views for the Template Variable data object
"""
from ..models import ConfigTemplate, TemplateVariable
from .forms import TemplateVariableForm



logger = logging.getLogger()


@tools.route('/')
@login_required
def index():
    """Tool dashboard page."""
    return render_template('tools/index.html')


@tools.route("/project/<int:project_id>/template/<int:config_template_id>")
def view_config_template(project_id, config_template_id):
    """read-only view of a single Config Template

    :param project_id:
    :param config_template_id:
    :return:
    """
    parent_project = Project.query.filter(Project.id == project_id).first_or_404()
    return render_template(
        "config_template/view_config_template.html",
        project=parent_project,
        config_template=ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()
    )


@tools.route("/project/<int:project_id>/configtemplate/add", methods=["GET", "POST"])
def add_config_template(project_id):
    """add a new Config Template

    :param project_id:
    :return:
    """
    parent_project = Project.query.filter(Project.id == project_id).first_or_404()

    form = ConfigTemplateForm(request.form)

    if form.validate_on_submit():
        try:
            config_template = ConfigTemplate(name="", project=parent_project)

            config_template.name = form.name.data
            config_template.template_content = form.template_content.data
            config_template.project = parent_project

            db.session.add(config_template)
            db.session.commit()

            flash("Config template <strong>%s</strong> successful created" % config_template.name, "success")

            return redirect(
                url_for(
                    "view_config_template",
                    project_id=project_id,
                    config_template_id=config_template.id
                )
            )

        except IntegrityError as ex:
            if "UNIQUE constraint failed" in str(ex):
                msg = "Config Template name already in use, please use another one"

            else:
                msg = "Config template was not created (unknown error, see log for details)"

            logger.error(msg, exc_info=True)
            flash(msg, "error")
            db.session.rollback()

        except Exception:
            msg = "Config template was not created (unknown error, see log for details)"
            logger.error(msg, exc_info=True)
            flash(msg, "error")

    return render_template(
        "config_template/add_config_template.html",
        project_id=project_id,
        project=parent_project,
        form=form
    )


@tools.route("/project/<int:project_id>/configtemplate/<int:config_template_id>/edit", methods=["GET", "POST"])
def edit_config_template(project_id, config_template_id):
    """edit a Config Template

    :param project_id:
    :param config_template_id:
    :return:
    """
    parent_project = Project.query.filter(Project.id == project_id).first_or_404()
    config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()

    form = ConfigTemplateForm(request.form, config_template)

    if form.validate_on_submit():
        try:
            if form.template_content.data != config_template.template_content:
                flash("Config Template content changed, all Template Value Sets are deleted.", "warning")

            config_template.name = form.name.data
            config_template.template_content = form.template_content.data
            config_template.project = parent_project

            db.session.add(config_template)
            db.session.commit()

            flash("Config template <strong>%s</strong> successful saved" % config_template.name, "success")

            return redirect(
                url_for(
                    "view_config_template",
                    project_id=project_id,
                    config_template_id=config_template.id
                )
            )

        except IntegrityError as ex:
            if "UNIQUE constraint failed" in str(ex):
                msg = "Config Template name already in use, please use another one"

            else:
                msg = "Config template was not created (unknown error, see log for details)"

            logger.error(msg, exc_info=True)
            flash(msg, "error")
            db.session.rollback()

        except Exception:
            msg = "Config template was not created (unknown error, see log for details)"
            logger.error(msg, exc_info=True)
            flash(msg, "error")

    return render_template(
        "config_template/edit_config_template.html",
        project_id=project_id,
        config_template=config_template,
        project=parent_project,
        form=form
    )


@tools.route(
    "/project/<int:project_id>/configtemplate/<int:config_template_id>/edit_all",
    methods=["GET", "POST"]
)
def edit_all_config_template_values(project_id, config_template_id):
    """edit all Config Template Values based on a CSV textarea

    :param project_id:
    :param config_template_id:
    :return:
    """
    Project.query.filter(Project.id == project_id).first_or_404()
    config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()

    form = EditConfigTemplateValuesForm(request.form, config_template)

    # hostname is defined in every Template Value Set
    variable_list = [
        "hostname"
    ]
    for var in config_template.variables.all():
        # hostname must be located as first entry
        if var.var_name != "hostname":
            variable_list.append(var.var_name)

    if form.validate_on_submit():
        # update values from the CSV file
        reader = csv.DictReader(io.StringIO(form.csv_content.data), delimiter=";")
        csv_lines = form.csv_content.data.splitlines()
        counter = 0
        for line in reader:
            if "hostname" in line.keys():
                if line["hostname"] is None:
                    flash("Invalid Hostname for Template Value Set: '%s'" % csv_lines[counter], "error")

                elif line["hostname"] == "":
                    flash("No Hostname defined for Template Value Set: '%s'" % form.csv_content.data.splitlines()[counter], "error")

                else:
                    # try to access an existing TemplateValueSet
                    tvs = TemplateValueSet.query.filter(
                        TemplateValueSet.config_template_id == config_template_id,
                        TemplateValueSet.hostname == line["hostname"]
                    ).first()
                    if not tvs:
                        # element not found, create and add a flush message
                        tvs = TemplateValueSet(hostname=line["hostname"], config_template=config_template)
                        flash("Create new Template Value Set for hostname <strong>%s</strong>" % line["hostname"], "success")

                    # update variable values
                    for var in variable_list:
                        if var in line.keys():
                            if line[var]:
                                tvs.update_variable_value(var_name=var, value=line[var])

                            else:
                                tvs.update_variable_value(var_name=var, value="")
                                logger.debug("Cannot find value for variable %s for TVS "
                                             "object %s using CSV line %s" % (var, repr(tvs), line))
            else:
                # hostname not defined, no creation possible
                flash("No hostname in CSV line found: %s" % line, "warning")
            counter += 1

        return redirect(url_for("view_config_template", project_id=project_id, config_template_id=config_template_id))

    else:
        form.csv_content.data = ";".join(variable_list)
        for tvs in config_template.template_value_sets.all():
            values = []
            for var in variable_list:
                values.append(tvs.get_template_value_by_name_as_string(var))
            form.csv_content.data += "\n" + ";".join(values)

    return render_template(
        "config_template/edit_all_config_template_values.html",
        project_id=project_id,
        config_template=config_template,
        form=form
    )


@tools.route("/project/<int:project_id>/configtemplate/<int:config_template_id>/delete", methods=["GET", "POST"])
def delete_config_template(project_id, config_template_id):
    """delete the Config Template

    :param project_id:
    :param config_template_id:
    :return:
    """
    Project.query.filter(Project.id == project_id).first_or_404()
    config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()

    if request.method == "POST":
        project_id = config_template.project.id
        try:
            db.session.delete(config_template)
            db.session.commit()

        except Exception:
            msg = "Config Template <strong>%s</strong> was not deleted (unknown error, see log for details)" % config_template.name
            flash(msg, "error")
            logger.error(msg, exc_info=True)
            db.session.rollback()

        flash("Config Template %s successful deleted" % config_template.name, "success")
        return redirect(url_for("view_project", project_id=project_id))

    return render_template(
        "config_template/delete_config_template.html",
        project_id=project_id,
        config_template=config_template
    )


@tools.route("/project/<int:project_id>/template/<int:config_template_id>/export")
def export_configurations(project_id, config_template_id):
    """
    Export the configuration to various locations
    :param project_id:
    :param config_template_id:
    :return:
    """
    project = Project.query.filter(Project.id == project_id).first_or_404()
    config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()

    return render_template(
        "config_template/export_configurations.html",
        project_id=project_id,
        project=project,
        config_template=config_template,
        ftp_password=get_appliance_ftp_password(),
        ip_addresses=get_local_ip_addresses(),
        appliance_status=verify_appliance_status()
    )

@tools.route("/project/template/<int:config_template_id>/valueset/<int:template_value_set_id>/config")
def view_config(config_template_id, template_value_set_id):
    """view the resulting configuration

    :param config_template_id:
    :param template_value_set_id:
    :return:
    """
    config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()
    template_value_set = TemplateValueSet.query.filter(TemplateValueSet.id == template_value_set_id).first_or_404()

    # generate configuration
    config_result = template_value_set.get_configuration_result()

    return render_template(
        "configuration/view_configuration.html",
        config_template=config_template,
        template_value_set=template_value_set,
        ftp_password=get_appliance_ftp_password(),
        ip_addresses=get_local_ip_addresses(),
        project=config_template.project,
        config_result=config_result
    )


@tools.route("/project/template/<int:config_template_id>/valueset/<int:template_value_set_id>/config_download")
def download_config(config_template_id, template_value_set_id):
    """download the resulting configuration

    :param config_template_id:
    :param template_value_set_id:
    :return:
    """
    ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()
    template_value_set = TemplateValueSet.query.filter(TemplateValueSet.id == template_value_set_id).first_or_404()

    # generate configuration
    config_result = template_value_set.get_configuration_result()

    response = make_response(config_result)
    response.headers["Content-Disposition"] = "attachment; filename=%s_config.txt" % template_value_set.hostname
    return response


@tools.route("/project/<int:project_id>/template/<int:config_template_id>/download_configs")
def download_all_config_as_zip(project_id, config_template_id):
    """generate all configuration files and download them as a ZIP archive

    :param project_id:
    :param config_template_id:
    :return:
    """
    Project.query.filter(Project.id == project_id).first_or_404()
    config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()

    # generate ZIP archive with all configurations
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for values in config_template.template_value_sets.all():
            data = zipfile.ZipInfo(values.hostname + "_config.txt")
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(data, values.get_configuration_result())
    memory_file.seek(0)

    return send_file(memory_file, attachment_filename=config_template.name + "_configs.zip", as_attachment=True)


@tools.route('/shell')
@login_required
def shell():
    """embedded shell in a box view

    :return:
    """
    return render_template("tools/shell.html")


@tools.route("/how-to-use")
@login_required
def how_to_use():
    """How to use page

    :return:
    """
    return render_template("tools/how_to_use.html")


@tools.route("/template-syntax")
@login_required
def template_syntax():
    """Templating 101 page

    :return:
    """
    return render_template("tools/template_syntax.html")


@tools.route("/appliance/service_status")
@login_required
def appliance_status_json():
    """
    Appliance Status JSON call
    :return:
    """
    return jsonify(verify_appliance_status())


@tools.route("/debug/list_ftp_directory")
@login_required
def list_ftp_directory():
    """
    debug view to create a tree structure of the FTP directory
    :return:
    """
    directory_list_html = ""

    for root, dirs, files in os.walk(app.config["FTP_DIRECTORY"]):
        directory_list_html += "<p>%s</p>\n<ul>\n" % root[len(app.config["FTP_DIRECTORY"]):]
        for file in files:
            directory_list_html += "<li>%s</li>\n" % file
        directory_list_html += "</ul>\n"

    return "<html><body>%s</body></html>" % directory_list_html


@tools.route("/debug/list_tftp_directory")
@login_required
def list_tftp_directory():
    """
    debug view to create a tree structure of the TFTP directory
    :return:
    """
    directory_list_html = ""

    for root, dirs, files in os.walk(app.config["TFTP_DIRECTORY"]):
        directory_list_html += "<p>%s</p>\n<ul>\n" % root[len(app.config["TFTP_DIRECTORY"]):]
        for file in files:
            directory_list_html += "<li>%s</li>\n" % file
        directory_list_html += "</ul>\n"

    return "<html><body>%s</body></html>" % directory_list_html

@tools.route('/task/<task_id>')
def task_status_json(task_id):
    """
    JSON API endpoint to view the state of a task
    :param task_id:
    :return:
    """
    task = celery.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', '')
        }
        if 'error' in task.info:
            response['error'] = task.info['error']

        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  # this is the exception raised
        }
    # update the response with the result of the task
    response["data"] = task.info
    return jsonify(response)

@tools.route("/project/template/<int:config_template_id>/valueset/<int:template_value_set_id>/")
def view_template_value_set(config_template_id, template_value_set_id):
    """view a single Template Value Set

    :param config_template_id:
    :param template_value_set_id:
    :return:
    """
    config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()
    return render_template(
        "template_value_set/view_template_value_set.html",
        config_template=config_template,
        project=config_template.project,
        template_value_set=TemplateValueSet.query.filter(TemplateValueSet.id == template_value_set_id).first_or_404()
    )


@tools.route("/project/template/<int:config_template_id>/valueset/add", methods=["GET", "POST"])
def add_template_value_set(config_template_id):
    """add a new Template Value Set

    :param config_template_id:
    :return:
    """
    parent_config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()
    form = TemplateValueSetForm(request.form)

    if form.validate_on_submit():
        try:
            template_value_set = TemplateValueSet(hostname="", config_template=parent_config_template)

            template_value_set.hostname = form.hostname.data
            template_value_set.config_template = parent_config_template
            template_value_set.copy_variables_from_config_template()

            db.session.add(template_value_set)
            db.session.commit()

            flash("Template Value Set successful created", "success")
            return redirect(url_for(
                "edit_template_value_set",
                template_value_set_id=template_value_set.id,
                config_template_id=parent_config_template.id
            ))

        except IntegrityError as ex:
            if "UNIQUE constraint failed" in str(ex):
                msg = "Template Value Set hostname already in use, please use another one"

            else:
                msg = "Template Value Set was not created (unknown error)"
            flash(msg, "error")
            logger.error(msg, exc_info=True)
            db.session.rollback()

        except Exception:
            msg = "Template Value Set was not created (unknown error)"
            logger.error(msg, exc_info=True)
            flash(msg, "error")
            db.session.rollback()

    return render_template(
        "template_value_set/add_template_value_set.html",
        config_template=parent_config_template,
        project=parent_config_template.project,
        form=form
    )


@tools.route(
    "/project/template/<int:config_template_id>/valueset/<int:template_value_set_id>/edit",
    methods=["GET", "POST"]
)
def edit_template_value_set(config_template_id, template_value_set_id):
    """edit a Template Value Set

    :param config_template_id:
    :param template_value_set_id:
    :return:
    """
    parent_config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()
    template_value_set = TemplateValueSet.query.filter(TemplateValueSet.id == template_value_set_id).first_or_404()

    form = TemplateValueSetForm(request.form, template_value_set)

    if form.validate_on_submit():
        try:
            template_value_set.hostname = form.hostname.data
            template_value_set.config_template = parent_config_template
            template_value_set.copy_variables_from_config_template()

            # update variable data
            for key in template_value_set.get_template_value_names():
                template_value_set.update_variable_value(var_name=key, value=request.form["edit_" + key])

            # hostname is always the same as the name of the template value set
            template_value_set.update_variable_value(var_name="hostname", value=template_value_set.hostname)

            db.session.add(template_value_set)
            db.session.commit()

            flash("Template Value Set successful saved", "success")
            return redirect(url_for(
                "view_config_template",
                project_id=parent_config_template.project.id,
                config_template_id=parent_config_template.id
            ))

        except IntegrityError as ex:
            if "UNIQUE constraint failed" in str(ex):
                msg = "Template Value Set hostname already in use, please use another one"

            else:
                msg = "Template Value Set was not created (unknown error)"
            flash(msg, "error")
            logger.error(msg, exc_info=True)
            db.session.rollback()

        except Exception:
            msg = "Template Value Set was not created (unknown error)"
            logger.error(msg, exc_info=True)
            flash(msg, "error")
            db.session.rollback()

    return render_template(
        "template_value_set/edit_template_value_set.html",
        config_template=parent_config_template,
        template_value_set=template_value_set,
        project=parent_config_template.project,
        form=form
    )


@tools.route(
    "/project/template/<int:config_template_id>/valueset/<int:template_value_set_id>/delete",
    methods=["GET", "POST"]
)
def delete_template_value_set(config_template_id, template_value_set_id):
    """delete the Config Template

    :param config_template_id:
    :param template_value_set_id:
    :return:
    """
    config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()
    template_value_set = TemplateValueSet.query.filter(TemplateValueSet.id == template_value_set_id).first_or_404()

    if request.method == "POST":
        # drop record and add message
        try:
            db.session.delete(template_value_set)
            db.session.commit()

        except:
            flash("Config Template <strong>%s</strong> was not deleted" % template_value_set.hostname, "error")

        flash("Config Template <strong>%s</strong> successful deleted" % template_value_set.hostname, "success")
        return redirect(
            url_for(
                "view_config_template",
                project_id=config_template.project.id,
                config_template_id=template_value_set.config_template.id
            )
        )

    return render_template(
        "template_value_set/delete_template_value_set.html",
        template_value_set=template_value_set,
        project=config_template.project
    )

@tools.route("/project/template/<int:config_template_id>/variable/<int:template_variable_id>/edit", methods=["GET",
                                                                                                             "POST"])
def edit_template_variable(config_template_id, template_variable_id):
    """edit a Template Variable

    :param config_template_id:
    :param template_variable_id:
    :return:
    """
    config_template = ConfigTemplate.query.filter(ConfigTemplate.id == config_template_id).first_or_404()
    template_variable = TemplateVariable.query.filter(TemplateVariable.id == template_variable_id).first_or_404()
    # edit of the hostname is not permitted
    if template_variable.var_name == "hostname":
        abort(403)

    old_var_name = template_variable.var_name

    form = TemplateVariableForm(request.form, template_variable)

    if form.validate_on_submit():
        try:
            if old_var_name != form.var_name_slug.data:
                config_template.rename_variable(old_var_name, new_name=form.var_name_slug.data)

            # update values from form
            template_variable.description = form.description.data
            template_variable.config_template = config_template

            db.session.add(template_variable)
            db.session.commit()

            flash("Template Variable successful saved", "success")

            return redirect(
                url_for(
                    "view_config_template",
                    project_id=config_template.project.id,
                    config_template_id=config_template.id
                )
            )

        except IntegrityError as ex:
            if "UNIQUE constraint failed" in str(ex):
                msg = "Template variable name already in use, please use another one"

            else:
                msg = "Template variable was not created (unknown error, see log for details)"

            logger.error(msg, exc_info=True)
            db.session.rollback()

        except Exception:
            msg = "Template variable was not created  (unknown error, see log for details)"
            logger.error(msg, exc_info=True)
            flash(msg, "error")

    return render_template(
        "template_variable/edit_template_variable.html",
        config_template=config_template,
        template_variable=template_variable,
        project=config_template.project,
        form=form
    )

@tools.route('/_update_editor_contents', methods=['POST'])
@login_required
@admin_required
def update_editor_contents():
    """Update the contents of an editor."""

    edit_data = request.form.get('edit_data')
    editor_name = request.form.get('editor_name')

    editor_contents = EditableHTML.query.filter_by(
        editor_name=editor_name).first()
    if editor_contents is None:
        editor_contents = EditableHTML(editor_name=editor_name)
    editor_contents.value = edit_data

    db.session.add(editor_contents)
    db.session.commit()

    return 'OK', 200
