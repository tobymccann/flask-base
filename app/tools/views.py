from flask import abort, flash, redirect, render_template, url_for, request
from flask_login import current_user, login_required
from flask_rq import get_queue

from .forms import ()
from . import tools
from .. import db
from ..decorators import admin_required
from ..email import send_email
from ..models import Role, User, EditableHTML


@tools.route('/')
@login_required
def index():
    """Tool dashboard page."""
    return render_template('tools/index.html')


@tools.route('/config-gen', methods=['GET', 'POST'])
@login_required
def config_gen():
    """Create a new user."""
    form = NewUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User {} successfully created'.format(user.full_name()),
              'form-success')
    return render_template('tools/config_gen.html', form=form)




@tools.route('/users')
@login_required
@admin_required
def get_config():
    """View all registered users."""
    users = User.query.all()
    roles = Role.query.all()
    return render_template(
        'tools/get_config.html', users=users, roles=roles)


@tools.route('/template-admin')
@login_required
@admin_required
def template_admin(template_id):
    """View a user's profile."""

    return render_template('tools/template_admin.html')




@tools.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def delete_user_request(user_id):
    """Request deletion of a config."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('tools/manage_user.html', user=user)


@tools.route('/shell')
@login_required
def shell():
    """embedded shell in a box view

    :return:
    """
    return render_template("tools/shell.html")


@app.route("/how-to-use")
@login_required
def how_to_use():
    """How to use page

    :return:
    """
    return render_template("tools/how-to-use.html")


@app.route("/template-syntax")
@login_required
def template_syntax():
    """Templating 101 page

    :return:
    """
    return render_template("template-syntax.html")


@app.route("/appliance/service_status")
@login_required
def appliance_status_json():
    """
    Appliance Status JSON call
    :return:
    """
    return jsonify(verify_appliance_status())


@app.route("/debug/list_ftp_directory")
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


@app.route("/debug/list_tftp_directory")
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
