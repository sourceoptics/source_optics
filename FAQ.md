How Do I Add A Private Repo
===========================

First create a credentials object and assign it in Django admin.

You will need to add a SSH private key and optionally an unlock password.

Repo cloning for private repos requires an SSH key, as the password field is *NOT* used, though this field may
be used for some future API requests.

Git Checkout Troubleshooting
============================

If a repo does not have a SSH credential associated, a SSH checkout will fail.

If the SSH key requires a password to unlock, this password must be stored on the credential object.

Repos with http:// and https:// URLs may not be private repos, for security reasons only SSH keys are stored (encrypted) in the system.

GitHub's SSH key must be added to known hosts. Rather than doing this automatically, just run the scanner once before attaching it to cron and answer yes to add the key.
This way if GitHub is somehow MITM'ed, future checkouts will fail.

How Do I Organize My Large Installation?
========================================

Computer Science departments, for instance, would probably create an "Organization" object for every single course.

Deployment Suggestions
======================

Automated deployment is up to you.

In the near future the "scan" command will have a basic file lock to prevent duplicate runs, so that it can be easily triggered on cron.

The web app is currently horizontally scalable and work to better enable multiple distributed scanning processes should be added in the future.

Performance
===========

Small repos will always be fast to scan for the first time.  Repositories with many tens of thousands of commits and contributors may take a long time to scan the first time, though subsequent updates will be fast.

For instance, to scan some of the largest open source projects with thousands of contributors, the initial import of the git repository and
recording of all commits may take 10 minutes on a reasonably current iMac.  

Additional updates, if run frequently enough, will be very short, especially if they are run frequently.

Performance will likely be upgraded in future versions.

Access Control
==============

Right now, the access control system allows anyone with a superuser account to add objects or edit them.

In the future, there will be an admin view that allows people admin access to only specific organizations.

Right now, the read-only (graphs/stats) views are unprotected by default, and this can also be made configurable.

There is also no Single-Sign-On support at this time, though this is also planned.

The secrets file can be used to decrypt git passwords in the database.  If this concerns you, do not index private git repos.

There is no REST API at this time and nothing exposes the git passwords to userland, they are only consumed by expect scripts on
the indexing server.

Maintainance
============

Keep a backup of your database.  If you lose the secrets file in /etc/srcoptics you will need to delete and recreate any credential objects
for private repo access.

No Repos Data Showing Up?
=========================

After adding repos via the "addrepo" command or Django admin, no graph data or statistics will be available until these repositories are
picked up by the "python3 manage.py scan" background job.  If this job is running, data will be stale.

Also, if the main dashboards do not show any graph or statistics data, it may just be that the time range in the UI needs to be adjusted

Other problems?
===============

A mailing list will be available soon, for now please report them on GitHub.
