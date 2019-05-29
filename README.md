Source Optics
=============

Source Optics is a repository analysis tool, with a primary focus on:

* graphical output
* quickly comparing multiple repositories
* scanning multiple branches, as opposed to just master.

It should be equally relevant to many types of users including:

* Computer Science educators
* Professional software developers and managers
* Open source community managers
* Data scientists interested in studying software development

Website
=======

See [sourceoptics.io](https://sourceoptics.io)

[Initial blog post](https://medium.com/@michaeldehaan/presenting-source-optics-better-git-analytics-for-teams-28ad3d238356)

Technical Details
=================

Source Optics is a stand-alone web applicaton implemented in Python3/Django that 
uses a PostgreSQL database.

It is essentially a multi-tenant system, and can run multiple courses or seperate views from
the same installation.  In a university setting, this means that you can keep projects
from one course or past semesters seperate from the others.

Any background tasks are implemented as Django management commands, which could be run by
any task management system and/or cron.  Celery is not used.

Graphs are generated from Plotly, so no javascript experience is required to work on
the project.

Currently the admin interface uses the built-in Django management interface, for instance,
to add new repos. This can also be scripted and will evolve over time.

For those wishing to try out Source Optics, it should run happily from a laptop.

Installation
============

For install as well as basic operations instructions, see INSTALL.md

Roadmap
=======

See GitHub Projects

Usage
=====

Once installed and running, add in data via Django admin, ex: http://servername/admin

View graphs at http://servername/

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
 
 Concept/Management: Michael DeHaan

Mailing List
============

A user & development discussion list is available on Google Groups. Setup & maintaince questions, ideas,
and code questions are all equally appropriate.  

To join, visit [https://groups.google.com/forum/#!forum/sourceoptics](https://groups.google.com/forum/#!forum/sourceoptics).  First posts are moderated to reduce spam, and most first posts should be approved in 24 hours.

Requests for features and ideas should be sent to the mailing list, not GitHub.

Code Contribution Preferences
=============================

A few small guidelines to keep things easy to manage.

1) Contributions should be by github pull request on a seperate branch per topic. Do not combine features. Rebase your pull requests to keep them up to date and avoid merges in the git history.  

2) TWe care a lot about managing the surface area of the application to keep it easy to maintain and operate, and this project should move pretty fast. To keep frustrations over repeated work low, discussion of feature ideas *prior* to submitting a pull request is strongly encouraged (i.e. what do you think about X, how should this be implemented?). For bugfixes, feel free to submit code directly. If you make a database change, you must check in a new Django migrations file.

3) Please do not send any submissions to tweak PEP8, pylint, or other code preferences.  Management will do that periodically, this breaks source code attribution.  Similarly, do not submit additions to add packaging or integration with third party build or test services.

Thank you!



