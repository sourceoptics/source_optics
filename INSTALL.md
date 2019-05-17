Source Optics Install/Operations Guide
======================================

Source Optics is a Django web app that also has some simple 
backend management commands that are intended to be run from cron or a other scheduler.

It does not have any cloud requirements or network dependencies other than (presently)
needing PostgreSQL.  Testing on other databases has been limited at this point.

This guide is a work in progress, but essentially Source Optics is a standard Django app
with standard Django management commands. If you have deployed one Django app, this one
should not be very different.

We first assume your system has Python 3 installed, and 'pip' points at pip3, and you have
a PostgreSQL instance running.  'git' and 'expect' must also be in your path.

If you are developing on a Mac, we recommend using "Postgres.app" and "pgadmin".

```
# from the checkout directory

## set up the application
mkdir /etc/srcoptics
pip install -r requirements.txt

# create a role for whatever <username> you would like to run srcOptics as
sudo -u postgres createuser --createdb <username>
```

From the 'psql' prompt you will need to create a new role to allow database access:

```
# To add a new user to an existing database:
CREATE ROLE <username> WITH CREATEDB SUPERUSER;
ALTER DATABASE srcopt OWNER TO <username>;
```

Add your database configuration settings to /etc/srcoptics/conf.d/database.py:

```
DATABASES = {
            'default': {
                        'ENGINE':'django.db.backends.postgresql',
                        'USER':  'postgres',
                        'NAME': 'srcopt',   
                    }
            }
```

Now complete the setup:

```
# create a superuser and the default organization
python manage.py init -s

# run the application on port 8000
python manage.py runserver 0:8000
```

NOTE: the `init` command will be going away in future releases, and be replaced by use of the standard
django management commands for database setup.  There may be another management command for creating the initial
organization and secrets that are used to encrypt repository access credentials.

Verification
============

Visit http://servername:8000/admin and make sure there is a "root" organization added.  You may rename this.

You may now add repositories at this time using the web interface.  (See below for CLI imports).

You may also wish to add some Tag objects to help categorize things.

Do not interact with Statistics, Author, File, and File Change objects in Django Admin directly.

Before proceeding further to the web interface, lets first scan the repository or repository you have added
so there will be some graphs and statistics to view.

Django Management Commands
==========================

Once you have repos in the system, you will need to periodically pull in new commits and calculate statistics
on the repo in order to see updated information in the web interface.

This is done with a shell command:

```
python manage.py daemon
```

Options will be added to this command over time to make it work more easily with cron and other init systems.


Other Shortcuts
===============

To quickly add a large amount of repos that are part of a github organization, one can run the following:

```
python manage.py addrepo -g <github_api_url>
```

Example:

```
python manage.py addrepo -g https://api.github.com/users/<name>/repos
python manage.py addrepo -g https://api.github.com/orgs/<name>/repos
```

You may wish to return to the Django admin view in the future to add or edit tags, descriptions, and so on.

Web Interface
=============

With some repositories added to the system and now scanned, visit http://servername and verify you can
see some graphs.

Random tips
==========


* SCSS file must be compiled into CSS for changes to take effect.
  * install 'sass'
  * 'make compilecss'

If your package manager does not install the `sass` utility, the raw `sassc` compiler can be used. Here is a hacky one liner you can use to create main.css with only `sassc`:

```
cat srcoptics/static/_scss/main.scss srcoptics/static/_scss/*.scss | sassc -I srcoptics/static/_scss --style compressed -s > srcOptics/static/main.css
```


