Source Optics Install/Operations Guide
======================================

Source Optics is a Django web app that also has some simple 
backend management commands that are intended to be run from cron or another scheduler.

It does not have any cloud requirements or network dependencies other than (presently)
needing PostgreSQL.  

It can scan repos from any HTTP/S git server (public repos only) or SSH based repositories (public
or private).

Testing on other databases has been limited at this point but we limit
database features used to keep it portable.

If you have deployed one Django app, this one should not be very different.

We first assume your system has Python 3 installed, and 'pip' points at pip3, and you have
a PostgreSQL instance running.  'git' and 'expect' must also be in your path.  If this is 
not the case, take care of this before proceeding.

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
python manage.py generate_secret
python manage.py runserver 0:8000
```


Django Admin and Object Setup
=============================

Visit http://servername:8000/admin and create an Organization.  Normally organizations represent
courses (at a university) or departments (at a workplace).

You should also add some Credential objects, which are used when checking out private repositories.

With these two in place, you may now add repositories at this time using the web interface. For each
repository, provide a name, select an Organization, and optionally pick a credential object to use if
the repository is not public. You may also add repositories via the import command, which is detailed
below.

Do not interact with Statistics, Author, File, and File Change objects in Django Admin directly, as these
are too low level.  Instead, use the API and UI to explore this data.

Before proceeding further to the web interface, lets first scan the repository or repository you have added
so there will be some graphs and statistics to view.

Scan Commands
=============

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

To scan just a single organization (or organizations matching a substring), you can run as follows:

```
ssh-agent python manage.py scan -o csc201
```

You can also *disable* organizations or repositories in Django admin, to prevent them from being
scanned. Disabled repos will still appear in the UI. The ability to *hide* organizations may come
in a later release.

Other Shortcuts
===============

CLI commands to import all repos in a github organization will be added soon.  This will require
specifying a github user URL or organization URL, as well as a Source Optics organization and 
optionally, a credential object.


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


