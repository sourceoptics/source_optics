Roadmap
=======

This is just a short list of things to do to the project. The following ideas are subject to change at any time.

- License headers
- Preserve date selection on all navigation
- Verify scanning transactions are seperate between scan and statistics, so repos show up faster
- Come up with a wider date window by default, so the graphs aren't usually blank
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




