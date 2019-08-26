Source Optics
=============

Source Optics is a source code repository dashboard, focused on understanding
evolving code activity and the teams that work on them.

It can help answer basic questions such as:

* what repositories are most active right now
* which projects are growing or decreasing in activity
* who is working on what projects
* what are the contribution dynamics around these projects

Features include:

* quick at-a-glance graphical output
* quickly comparing multiple repositories
* analyzing multiple branches all at once, as opposed to just "master"

It should be equally relevant to many types of users including:

* Computer Science educators
* Commercial software developers and managers
* Researchers interested in studying software development

Website
=======

See [sourceoptics.io](https://sourceoptics.io)

[Initial blog post](https://medium.com/@michaeldehaan/presenting-source-optics-better-git-analytics-for-teams-28ad3d238356)

Technical Details
=================

Source Optics is a stand-alone web applicaton implemented in Python3 and Django, using PostgreSQL
for a database.

It is essentially a multi-tenant system, and can index multiple courses or seperate business
departments from the same installation.

Background tasks are implemented as Django management commands, which could be run by
any task management system and/or cron.  Celery is not used, simplifying setup and
maintaince.

Repositories can be automatically imported via a management command, and all other aspects
of the system are configured within in the Django management interface (on "/admin").

The API is largely read-only but will support eventually support injection of user data via a few custom
POST endpoints, for instance allowing display in-GUI of build-system status, source code
static analysis, and so on. 

For those wishing to try out Source Optics, it should run happily from a laptop.

Installation
============

Installation and operation is as with any standard Django application and is described in INSTALL.md.

Roadmap
=======

See GitHub Projects

Usage
=====

(Also described in INSTALL.md)

Once installed and running, add in data via Django admin, ex: http://servername/admin

View graphs at http://servername/

More detailed documentation about Django admin settings will come later, but is largely
documented already with tooltips and in the install guide.

License
=======

All source is provided under the Apache 2 license, (C) All Project Contributors.

Questions/Troubleshooting
=========================

The mailing list will be available soon.

Until then, see FAQ.md

Authors/Credits
===============

Initial version:
 * Ady Francis
 * Pranesh Kamalakanthan
 * Austin Shafer
 * Nick Wrenn
 
Concept: 
 * Michael DeHaan
 * NCSU Senior Design Center

Current development:
 * Michael DeHaan

Mailing List
============

A combined user & development discussion list is available on Google Groups. Setup & management questions, ideas,
and code questions are all equally appropriate.  The mailing list is also the best place to keep up with the 
direction of the project.

To join, visit [https://groups.google.com/forum/#!forum/sourceoptics](https://groups.google.com/forum/#!forum/sourceoptics).  First posts are moderated to reduce spam, and most first posts should be approved in 24 hours.

Requests for features and ideas should be sent to the mailing list, not GitHub.


Code Contribution Preferences
=============================

A few small guidelines to keep things easy to manage.

0) While not required, it is strongly encouraged that all contributors should join the mailing list.

1) Contributions should be by github pull request on a seperate branch per topic. Please do not combine features. Rebase your pull requests to keep them up to date and avoid merges in the git history.  

2) We care a lot about managing the surface area of the application to keep it easy to maintain and operate, and this project should move pretty fast. To keep frustrations over repeated work low, discussion of feature ideas *prior* to submitting a pull request is strongly encouraged (i.e. what do you think about X, how should this be implemented?). For bugfixes, feel free to submit code directly. If you make a database change, you must check in a new Django migrations file.

3) Please do not send any submissions to tweak PEP8, pylint, or other code preferences.  Management will do that periodically, this breaks source code attribution.  Similarly, do not submit additions to add packaging or integration with third party build or test services.

4) Any addition of new database fields must also add a Django migration in the same pull request.

Thank you!



