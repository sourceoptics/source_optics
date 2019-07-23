Source Optics Install/Operations Guide
======================================

Source Optics is a Django web app that also has some simple 
backend management commands that are intended to be run from cron or another scheduler.

If you have deployed one Django app, this one should not be very different.

It does not have any cloud requirements or network dependencies other than (presently)
needing PostgreSQL. Testing on other databases has been limited at this point but we limit
database features used to keep it portable.

It can scan repos from any HTTP/S git server (public repos only) or SSH based repositories (public
or private).  You do not need to be using GitHub, though some features like API imports of repositories
and webhooks have been written primarily for GitHub and GitHub Enterprise.

We first assume your system has Python 3 installed, and 'pip' points at pip3, and you have
a PostgreSQL instance running.  'git' and 'expect' must also be in your path.  If this is 
not the case, take care of this before proceeding.

If you are developing on a Mac, we recommend using "Postgres.app" and "pgadmin".

Initial Steps
=============

```
# from the checkout directory

## set up the application
mkdir /etc/source_optics
pip install -r requirements.txt

Database Setup
==============

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

Continuing Setup
================


Now complete the setup:

```
python manage.py migrate
python manage.py createsuperuser
python manage.py generate_secret
python manage.py runserver 0:8000
```

The generate_secret command generates a symetric key in /etc/sourceoptics/cred.key.  If you lose this
file you will need to run the command again and re-edit any credential objects in Django Admin to allow
them to be re-encrypted with a new key.  There are no uses for this file outside the credential objects.
This will be explained in more detail later.

Django Admin and Object Setup
=============================

It's time to start configuring the app for your specific environment.

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

Scan Commands (Backend)
=======================

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

The scanner is governed by a setting in settings.py, PULL_THRESHOLD, which ensures that a repository
is not scanned more than every X minutes. If running the scanner frequently (such as every
5 minutes), setting PULL_THRESHOLD to a value that is greater than 30 minutes or so may be appropriate.

The scanner contains/will-contain a flock() call that will prevent concurrent runs from happening on the same
machine.

If parallelism is desired, process other organizations on a different machine.  Feature additions to
enable parallel scans on the same machine may be added in the future.

Webhooks
========

To enable webhooks to trigger the scanner automatically, make sure the scanner is set to run
on cron as normal, but at a higher frequency (perhaps once every 2 minutes) and then set the PULL_THRESHOLD
in settings.py to something like 120 minutes.  This means that without a webhook, a repository will only
be pulled very sporadically, but there is still a safeguard in case IT or GitHub breaks the routing of your 
webhooks or something like that.

In Django admin, on each organization, set the "webhooks_enabled" boolean to True.  

The URL to configure in GitHub or Jenkins is "http://yourserver:yourport/webhook".  The webhook must be set
to send JSON.

On each repository, an optional webhook security token is available to prevent abuse of a webhook.
If a token is set to 'acme1234', configure the webhook as "http://yourserver/webhook?token=1234"
If the token is not set on a repository, the value can be taken from the organization.

Note that webhooks have only been tested with GitHub and involve matching on the URLs on the repositories. Improvements,
particularly to support other hosting providers is a welcome addition.

When a commit happens, the external system will send a JSON POST to SourceOptics, and SourceOptics will flag
the repository to be scanned in the very next scanner pass.

Automated Repository Imports
============================

Configure GitHub in the organization's credential object and run the following:


python3 manage.py github_import -o organization_name

The organization must already exist.  There are settings in the organization to specify a github API endpoint
(for use with private GitHub) as well as fnmatch-format filter strings to only import certain patterns of project names.

Support for other hosting providers via another management command would be a welcome addition.

Statistics Web Interface
========================

With all the housekeeping out of the way, it's time to look at some stats.

The webserver can be previewed using the "python3 manage.py runserver 0:8000" command, but in production,
the web application should be started by something like gunicorn and invoked
on system startup.  Instructions and automation for this are pending, but this is a fairly simple
exercise for sysadmins.

With some repositories added to the system and now scanned, visit http://servername and verify you can
see some graphs.

Over time, expect to see lots of new features in this area.


Backups/Maintaince
==================

You should make database backups.  The 'work' directory inside the project is not important to save,
as new checkouts will recreate the git clones.

You should backup /etc/sourceoptics, not only for database configuration and settings, but also the
'cred.key' file, which is used to symetrically encrypt database contents.  The encryption key
is not held within the database.  As previously mentioned, if you rewrite this key, you will need
to set up new credentials in the admin system.

There are no other significant maintaince tasks to be aware of at this time.

Security Concerns
=================

Database access is controlled via standard means.  Currently the web UI is readable to any user,
and access to Django admin is allowed for any Django superuser, created by 'python3 manage.py createsuperuser'.

In the future, we should allow owners of an organization to manage just their own organization, but this
is presently not available.

Also, at the present time, all repo statistics, which  may in the near future include commit history, are public
to anyone with access to the website.




