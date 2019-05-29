Roadmap
=======

This is just a short list of things to do to the project. The following ideas are subject to change at any time.

Code Cleanup
============
- License headers
- Add makefile targets
- Use python standard logging consistently
- Fix naive datetime warnings (DateTimeField Statistic.start_date received a naive datetime (2019-05-17 22:32:32.957787) while time zone support is active)
- The aggregration code uses "repo.last_scanned" to decide where to resume, and it should use a different statistic, last_rollup. Right now this field is added but really represents last daily rollups, so we need an additional field.
- SIGINT to the scan process requires two sigints - probably need to hook signals to join threads (?)
- Move function comments into docstrings
- Graphs with a large amount of data are too slow, database not optimized?

Deployment/Portability
======================
- test with sqlite
- Heroku deployment automation/targets for easy trials

CLI
===
- Make CLI object controls a bit more consistent
- Add a CLI command to delete a repo (what about other object types?)
- Refactoring - keyword args, break into smaller functions
- Make CLI options flags for scanner consistent for use with cron and systemd
- Change the add repo command into a 'import' command
- Retire the 'init' django management command except for parts not managed by django management commands already

Django Admin
============
- When deleting a repo in Django admin, the prompt about deleting all associated objects jams the Django admin interface (try workaround: https://code.djangoproject.com/ticket/10919)

Scanner/Stats
=============
- Scanner code doesn't like spaces in repo object names
- When calculating rollups, store the last rollups fully computed on the repo object to avoid duplicate recalc. on failure or ctrl-c
- Verify scanning transactions are seperate between scan and statistics, so repos show up faster

Larger Features
===============
- Add a 'commit log' for every project that shows authors/commits, is filterable, and ignores branch names
- More graphs
- More stats
- More reports
- Admin view for users to avoid needing to use django admin
- Views for per file stats
- Consider loading graphs asynchronously (ajax the URL, etc) to increase responsiveness with multiple graphs

Security
========
- Allow the front page to be access controlled even in read only mode
- Control what users can use what creds
- Support SSH keys for checkout of private content (see Vespene code for example)

Minor UX
========
- Preserve date selection on all navigation
- Come up with a wider date window by default, so the graphs aren't usually blank
- Look into reinstating file and directory indexing to note changes by types of files
- Graph and cell colors should  not be random, but should have some reasonable default and maybe be configurable (possibly from the tag).
- The date widget automatically changes the URL and is too hard to adjust by typing. Consider a simpler widget.  (Also can't easily go back several years)
- Show scanning status in the web interface somewhere, ideally a percentage
- When selecting wide time ranges, default to monthly averages not day data


