# flask-base [![Code Climate](https://codeclimate.com/github/tobymccann/flask-base/badges/gpa.svg)](https://codeclimate.com/github/tobymccann/flask-base/coverage)[![Issue Count](https://codeclimate.com/github/tobymccann/flask-base/badges/issue_count.svg)](https://codeclimate.com/github/tobymccann/flask-base) ![python3.x](https://img.shields.io/badge/python-3.x-brightgreen.svg)
<img src="readme_media/logo@2x.png" width="400"/>

A Flask application template with the boilerplate code already done for you. 



## What's included?

* Blueprints
* User and permissions management
* Flask-SQLAlchemy for databases
* Flask-WTF for forms
* Flask-Assets for asset management and SCSS compilation
* Flask-Mail for sending emails
* gzip compression
* Celery + Redis for handling asynchronous tasks
* ZXCVBN password strength checker  
* CKEditor for editing pages

## Demos

Home Page:

![home](readme_media/home.gif "home") 

Registering User:

![registering](readme_media/register.gif "register")

Admin Homepage:

![admin](readme_media/admin.gif "admin")

Admin Editing Page:

![edit page](readme_media/editpage.gif "editpage") 

Admin Editing Users:

![edit user](readme_media/edituser.gif "edituser")

Admin Adding a User: 

![add user](readme_media/adduser.gif "add user")

## Setting up

##### Clone the repo

```
$ git clone https://github.com/tobymccann/flask-base.git
$ cd flask-base
```

##### Initialize a virtualenv

```
$ python3 -m venv env
$ source env/bin/activate
```

##### (If you're on a mac) Make sure xcode tools are installed

```
$ xcode-select --install
```

##### Add Environment Variables 

Create a file called `config.env` that contains environment variables in the following syntax: `ENVIRONMENT_VARIABLE=value`. For example,
the mailing environment variables can be set as the following. Any mail service should work.
```
MAIL_USERNAME=SendgridUsername
MAIL_PASSWORD=SendgridPassword
SECRET_KEY=SuperRandomStringToBeUsedForEncryption
```
**Note: do not include the `config.env` file in any commits. This should remain private.**

##### Install the dependencies

```
$ pip install -r requirements.txt
```

##### Other dependencies for running locally

You need to install [Redis](http://redis.io/), and [Sass](http://sass-lang.com/). Chances are, these commands will work:


**Sass:**

```
$ gem install sass
```

**Redis:**

_Mac (using [homebrew](http://brew.sh/)):_

```
$ brew install redis
```

_Linux:_

```
$ sudo apt-get install redis-server
```

You will also need to install **PostgresQL**

_Mac (using homebrew):_

```
brew install postgresql
```

_Linux:_

```
sudo apt-get install libpq-dev
```


##### Create the database

```
$ python manage.py recreate_db
```

##### Other setup (e.g. creating roles in database)

```
$ python manage.py setup_dev
```

Note that this will create an admin user with email and password specified by the `ADMIN_EMAIL` and `ADMIN_PASSWORD` config variables. If not specified, they are both `flask-base-admin@example.com` and `password` respectively.

##### [Optional] Add fake data to the database

```
$ python manage.py add_fake_data
```

## Running the app

```
$ source env/bin/activate
$ honcho start -f Local
```

## Formatting code

Before you submit changes to flask-base, you may want to auto format your code with `python manage.py format`.


## Contributing
Contributions are welcome! Check out our [Waffle board](https://waffle.io/tobymccann/flask-base) which automatically syncs with this project's GitHub issues. Please refer to our [Code of Conduct](./CONDUCT.md) for more information.

## Documentation Changes

To make changes to the documentation refer to the [Mkdocs documentation](http://www.mkdocs.org/#installation) for setup. 

To create a new documentation page, add a file to the `docs/` directory and edit `mkdocs.yml` to reference the file. 

When the new files are merged into `master` and pushed to github. Run `mkdocs gh-deploy` to update the online documentation.

## License
[MIT License](LICENSE.md)
