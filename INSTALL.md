Source Optics Install/Operations Guide
======================================

Excellent! We're glad you are interested in running Source Optics.

Source Optics is a Django web application. It also has some simple 
backend management CLI commands that are intended to be run from cron or another scheduler.

If you have deployed one Django app, this one should not be very different.

Source Optics does not have any cloud requirements or network dependencies other than (presently)
needing PostgreSQL. 

It can scan repos from any HTTP/HTTPS git server (public repos only) or SSH based repositories (public
or private).  You do not need to be using GitHub, though some features like API imports of repositories
and webhooks have been written primarily for GitHub and GitHub Enterprise, and other versions 

This application has been developed on a Mac with support for Mac and Linux/Unix machines. Some small areas
of the application probably do not work on Windows. Patches to fix any problem related to Windows support are always welcome.

We first assume your system has Python 3 installed, and 'pip' points at pip3 (otherwise just run pip3), and you have
a PostgreSQL instance running.  'git' and 'expect' must also be in your path.  If this is 
not the case, take care of this before proceeding. If you are running from homebrew, also install 'timeout', which
gets installed as 'gtimeout'.

If you are developing on a Mac, we recommend using "Postgres.app" for your database setup, along with the "pgadmin" web UI.

Initial Steps
=============

```
# from the checkout directory

## set up the application
mkdir -p /etc/source_optics/conf.d/
pip install -r requirements.txt
```

Database Setup
==============

Once PostgreSQL is installed, make a new database:

```
createdb source_optics
````

Next, we'll create a role for whatever username you would like to run source_optics as:

```
createuser --createdb <username>
```

(You may need to run these commands sudoed to 'postgres' depending on your plaform setup)

From the 'psql' prompt you will then need to create a new role to allow database access:

```
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

Understanding Encryption Features
=================================

The generate_secret command generates a symetric key in /etc/source_optics/cred.key.  If you lose this
file you will need to run the command again and re-edit any credential objects in Django Admin to allow
them to be re-encrypted with a new key.  There are no uses for this file outside the credential objects.
This will be explained in more detail later.

Django Admin and Object Setup
=============================

It's time to start configuring the app for your specific environment.

Visit http://servername:8000/admin and create an Organization.  Normally organizations represent
something like departments (at a workplace) or courses at a university.  You do not technically
need to create more than one organization, but you can.

You should also add some Credential objects, which are used when checking out private repositories.
Crednetials will hold on to your SSH private keys, which are automated behind the scenes with the
system using SSH-agent.  It's fine to create keys specifically for this purpose, and then add them
to your repositories in GitHub, GitLab, and so on, and is preferred to using private keys that would
have access to other software systems. This all being said, these keys are encrypted in the database
using the keyfiles above.

With these two configuration items in place, you may now add repositories at this time using the web interface. For each
repository, provide a name, select an Organization that it should belong to, and optionally pick a credential object to use if
the repository is not public. You may also add repositories via the import command, which is detailed
below.

Do not interact with Statistics, Author, File, and File Change objects in Django Admin GUI directly, as these
are too low level.  Instead, use the API and UI to explore this data.  The visibility of these objects in Django
admin will likely be removed in a future release.

Before proceeding further to the web interface, lets first scan the repository or repository you have added
so there will be some graphs and statistics to view.  We'll show how to do that below.

Scan Commands (Backend)
=======================

Once you have repos in the system, you will need to periodically pull in new commits and calculate statistics
on the repo in order to see updated information in the web interface.

This is done with a shell command:

```
python manage.py scan
```

This should normally be invoked with ssh-agent in order to allow working with SSH keys and passphrases, which
are used for some git checkouts, so like this:

```
ssh-agent python manage.py scan
```

Note that in order for the scan to *NOT* stall, the SSH fingerprint of the remote server (for SSH checkouts) *must*
be added to known hosts for the user running the scanner command.  You can easily do this by just attempting to do a manual git clone for one of the many repos, and then saying "yes" at the known host prompt.

To scan just a single organization (or organizations matching a substring), you can run as follows:

```
ssh-agent python manage.py scan -o csc201
```

And you can also scan a specific repository:

```
ssh-agent python manage.py scan -o repo_name
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

If you have problems with the scanner going interactive, make sure that you are using ssh:// URLs for repositories in
the Django admin configuration for the repo, that the process is wrapped with ssh-agent, and if any credentials have locked keys (SSH keys with passphrases) those are stored on the credential objects.

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

Configure GitHub in the organization's Credential object (in Django Admin).

You will need to supply an organizaton name and, if using GitHub Enterprise, the github API endpoint URL.

Once configured, run the following:

```
python3 manage.py github_import -o organization_name
```

The organization must already exist.  There are settings in the organization to specify a github API endpoint
(for use with private GitHub) as well as fnmatch-format filter strings to only import certain patterns of project names.

This can work with both regular GitHub and GitHub Enterprise installations.

Support for other hosting providers via another management command would be a welcome addition.

Statistics Web Interface
========================

With all the housekeeping out of the way, it's time to look at some stats.

The webserver can be previewed using the "python3 manage.py runserver 0:8000" command, but in production,
the web application should be started by something like gunicorn and invoked
on system startup.  Instructions and automation for this are pending, but this is a fairly simple
exercise for sysadmins.

Inclusion of a basic systemd example file using gnuicorn would be a welcome addition, but as this is distribution
specific, we'll leave automation setup of the program up to the installer.

With some repositories added to the system and now scanned, visit http://servername and verify you see some
statistics show up.  If graphs appear blank, or statistics show "0", try adjusting the time range as everything
in SourceOptics works off a time-series implementation.

Over time, expect to see lots of new features in this area.

Upgrades
========

SourceOptics doesn't have explicitly versioned releases at this time, and you should be able to run directly
out of source checkouts.

When you do a "git pull", apply database migrations from "python manage.py migrate". Any new
config settings will appear in settings.py automatically, and if you want to make any changes, do not
edit settings.py, but add overrides in /etc/sourceoptics/conf.d/*.py.  You can make any files
you want there that end in "*.py" and they will all be loaded.

Backups/Maintenance
===================

You should make database backups.  The 'work' directory inside the project is not important to save,
as new checkouts will recreate the git clones.

You should absolutely backup /etc/source_optics, not only for database configuration and settings, but also the
'cred.key' file, which is used to symetrically encrypt database contents.  The encryption key
is not held within the database.  As previously mentioned, if you rewrite this key, you will need
to set up new credentials in the admin system.

There are no other significant maintaince tasks to be aware of at this time.

Security Concerns
=================

Database access is controlled via standard means.  Currently the web UI is read-only to any user,
and access to Django admin is allowed for any Django superuser, created by 'python3 manage.py createsuperuser'.

In the future, we should allow owners of an organization to manage just their own organization, but this
is presently not available, and we expect most users to be comfortable with sharing organizational stats
throughout their organization.

That all being said, limited features to restrict access would be welcome additions, and may be added in future
releases.

Also, at the present time, all repo statistics, which  may in the near future include commit history, are public
to anyone with access to the website.

Future Manual
=============

The above setup information is comprehensive, though an online user guide should be created in the near future, that will
walk through settings in more detail.

In particular, some settings, such as source code filtering, or configurable working directories, are not yet fully explained
in this guide, but do have tooltips/explanations in the admin view. We don't suspect these settings will cause any problems, but let us know if you do have questions.

Questions
=========

If you have any setup problems or have any questions, please post on the mailing list or email michael@michaeldehaan.net. 




