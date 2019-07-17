Source Optics Install/Operations Guide
======================================

Source Optics is a Django web app that also has some simple 
backend management commands that are intended to be run from cron or a other scheduler.

It does not have any cloud requirements or network dependencies other than (presently)
needing PostgreSQL.  Testing on other databases has been limited at this point but we limit
database features used to keep it portable.

This guide is evolving (feedback welcome), but essentially Source Optics is a standard Django app
with standard Django management commands. If you have deployed one Django app, this one
should not be very different.

We first assume your system has Python 3 installed, and 'pip' points at pip3, and you have
a PostgreSQL instance running.  'git' and 'expect' must also be in your path.

If you are developing on a Mac, we recommend using "Postgres.app" and "pgadmin".

```
# from the checkout directory

## set up the application
mkdir /etc/source_optics
pip install -r requirements.txt

# create a role for whatever <username> you would like to run source_optics as
sudo -u postgres createuser --createdb <username>
```

From the 'psql' prompt you will need to create a new role to allow database access:

```
# To add a new user to an existing database:
CREATE ROLE <username> WITH CREATEDB SUPERUSER;
ALTER DATABASE source_optics OWNER TO <username>;
```

Add your database configuration settings to /etc/source_optics/conf.d/database.py:

```
DATABASES = {
            'default': {
                        'ENGINE':'django.db.backends.postgresql',
                        'USER':  'postgres',
                        'NAME': 'USERNAME_FROM_ABOVE',   
                    }
            }
```

Now complete the setup:

```
python manage.py migrate

python manage.py createsuperuser

# create the initial secret for credential encryption in the database and the default organization object
python manage.py init -s

# run the application on port 8000
python manage.py runserver 0:8000
```


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
python manage.py scan
```

This should normally be invoked with ssh-agent in order to allow working with SSH keys and passphrases, which
are used for some git checkouts:

```
ssh-agent python manage.py scan
```

Is enough.

A supervisord config may be supplied in the near future.

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

This command will be split soon into different commands for github and gitlab.

Web Interface
=============

With some repositories added to the system and now scanned, visit http://servername and verify you can
see some graphs.

Random development tips
=======================


* SCSS must be compiled into CSS for changes to take effect.
  * sudo gem install sass
  * 'make css'
```


