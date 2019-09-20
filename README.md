
![](https://raw.githubusercontent.com/sourceoptics/source_optics/master/source_optics/static/logo_bg.png?s=400)

![](https://img.shields.io/badge/dynotherms-connected-blue) ![](https://img.shields.io/badge/infracells-up-green) ![](https://img.shields.io/badge/megathrusters-go-green)

Source Optics
=============

Source Optics is an advanced source code repository dashboard, focused on understanding
evolving code activity in an organization and the teams that work on them.

Read all about use cases at  http://sourceoptics.io/

Installation, Setup, and Usage
==============================

Source Optics is a stand-alone web applicaton.  It is built on Python3 and Django, using PostgreSQL
for a database, making it exceptionally easy to deploy. You should be up and running in about 30
minutes, and setup is fairly standard as Django applications go.

See [INSTALL.md](https://github.com/sourceoptics/source_optics/blob/master/INSTALL.md) for detailed instructions.

Roadmap
=======

Our Roadmap is 100% public and posted on [GitHub Projects](https://github.com/sourceoptics/source_optics/projects)

License
=======

All source is provided under the Apache 2 license, (C) 2018-2019, All Project Contributors.

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
