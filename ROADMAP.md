Roadmap
=======

This is just a short list of things to do to the project. The following ideas are subject to change at any time.

- License headers
- Add a CLI command to delete a repo
- When deleting a repo in Django admin, the prompt about deleting all associated objects jams the Django admin interface (try workaround: https://code.djangoproject.com/ticket/10919)
- When calculating rollups, store the last rollups fully computed on the repo object to avoid duplicate recalc. on failure or ctrl-c
- Preserve date selection on all navigation
- Verify scanning transactions are seperate between scan and statistics, so repos show up faster
- Come up with a wider date window by default, so the graphs aren't usually blank
- Refactoring - keyword args, break into smaller functions
- Add a 'commit log' for every project that shows authors/commits, is filterable, and ignores branch names
- Make CLI options flags for scanner consistent for use with cron and systemd
- Change the add repo command into a 'import' command
- Retire the 'init' django management command except for parts not managed by django management commands already
- Add makefile targets
- test with sqlite
- Heroku deployment automation/targets for easy trials
- Allow the front page to be access controlled even in read only mode
- Admin view for users to avoid needing to use django admin
- Review/audit logging
- Review indexing/statistics speed, store historical performance info?
- Look into reinstating file and directory indexing to note changes by types of files
- More graphs
- More stats
- More reports
- Views for per file stats
- Fix naive datetime warnings (DateTimeField Statistic.start_date received a naive datetime (2019-05-17 22:32:32.957787) while time zone support is active)
- Show scanning status in the web interface somewhere, ideally a percentage
- When selecting wide time ranges, default to monthly averages not day data
- Consider loading graphs asynchronously (ajax the URL, etc) to increase responsiveness with multiple graphs
- SIGINT to the scan process requires two sigints - probably need to hook signals to join threads (?)
- Move function comments into docstrings
- The aggregration code uses "repo.last_scanned" to decide where to resume, and it should use a different statistic, last_rollup. Right now this field is added but really represents last daily rollups, so we need an additional field.
- The "flush" handling of the bulk inserts could be streamlined a bit to be easier to work on. Some sort of manager class?

