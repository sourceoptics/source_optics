
![](https://raw.githubusercontent.com/sourceoptics/source_optics/master/source_optics/static/logo_bg.png?s=400)

![](https://img.shields.io/badge/dynotherms-connected-blue) ![](https://img.shields.io/badge/infracells-up-green) ![](https://img.shields.io/badge/megathrusters-go-green)

Source Optics
=============

Source Optics is an advanced source code repository dashboard, focused on understanding
evolving code activity in an organization and the teams that work on them.

It should be equally relevant to many types of users including:

* Commercial software managers, developers, and executives
* Ops/"DevOps" teams tracking a wide variety of microservice repositories
* Open source community managers
* Researchers interested in studying software development
* Computer science educators with a large number of class projects

It can help answer basic questions such as:

* what repositories are most active within a time range
* what are the contribution dynamics around these projects
* which projects are growing or decreasing in activity
* who is working on what projects
* how much work effort is being applied, by whom, to different projects

Features include:

* multiple charts showing project dynamics, with built-in curve fitting
* tables of contributor activity
* analyzing multiple branches all at once, as opposed to just "master"

Compared to other analysis tools, SourceOptics is well differentiated by:

* showing all branches at once
* supporting arbitrary time range windows for all statistics and graphs
* offering more statistics and graphs
* being scalable to projects with thousands of authors
* having an amazing roadmap of new features

Website
=======

See [sourceoptics.io](https://sourceoptics.io)

Features/Basics
===============

Repositories are configured or can be imported over the GitHub API.

Once added, repositories can be periodically scanned, or triggered for scanning from a webhook.

Scanned repositories can be reviewed, using a wide range of graphs and tables.

Technical Details
=================

Source Optics is a stand-alone web applicaton.  It is built on Python3 and Django, using PostgreSQL
for a database, making it exceptionally easy to deploy.

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

Installation and operation is as with any standard Django application and is described in [INSTALL.md](https://github.com/sourceoptics/source_optics/blob/master/INSTALL.md).

Roadmap
=======

See GitHub Projects

Usage
=====

(Also described in [INSTALL.md](https://github.com/sourceoptics/source_optics/blob/master/INSTALL.md))

Once installed and running, add in data with the Django admin UI, ex: http://127.0.0.1:8000/servername/admin.
Set up a credential, create an organization, add some repos.  Or use the CLI import command to import repos from GitHub.

Can the repositories periodically with the "python3 manage.py scan" command.

View graphs at http://127.0.0.1/

More detailed documentation about Django admin settings will come later, but is largely
documented already with tooltips and in the install guide.

License
=======

All source is provided under the Apache 2 license, (C) All Project Contributors.

Newsletter
==========

A weekly newsletter is available for signup at the bottom of http://sourceoptics.io/ - it's a great way to keep up with new features in development, ideas, to participate in surveys, and more. 

Code Contribution Preferences
=============================

A few small guidelines to keep things easy to manage:

0) Contributors should subscribe to the newsletter to keep up with project direction. If you are on twitter, also follow @SourceOptics.

1) Contributions should be by github pull request on a seperate branch per topic. Please do not combine features. Rebase your pull requests to keep them up to date and avoid merges in the git history.  

2) We care a lot about managing the surface area of the application to keep it easy to maintain and operate, and this project should move pretty fast. To keep frustrations over repeated work low, discussion of feature ideas *prior* to submitting a pull request is  encouraged. For bugfixes, feel free to submit code directly. If you make a database change, you must check in a new Django migrations file. Email michael AT michaeldehaan.net to discuss anything you would like to discuss.  

3) Please do not send any submissions to tweak PEP8, pylint, or other code preferences. This breaks source code attribution, and we'll do it periodically anyway. Similarly, do not submit additions to add packaging, deployment, or integration with third party build or test services, as these are site specific preferences and we will not be maintaining multiple offshoots.

Thank you!
