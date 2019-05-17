How Do I Add A Private Repo
===========================

First create a credentials object and assign it in Django admin

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

The very most popular repos on github MAY take several hours depending on computing hardware available.  Optimizations to this process, 
particularly in regards to tracking file content, are pending.

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
