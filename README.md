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

See [[sourceoptics.io][http://sourceoptics.io]]


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

See ROADMAP.md

Usage
=====

Once installed and running, add in data via Django admin, ex: http://servername/admin

View graphs at http://servername/

Discussion
==========

User Q&A, Ideas, and Contributions are all welcome. 

Stop by the mailing list at <TBD>.

License
=======

Apache 2

Authors/Credits
===============

 Ady Francis
 Pranesh Kamalakanthan
 Austin Shafer
 Nick Wrenn




