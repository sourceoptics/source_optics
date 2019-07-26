# Copyright 2018 SourceOptics Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import datetime
import calendar
from django.db.models import Sum
from django.utils import timezone
from source_optics.models import Statistic, Commit, FileChange, Author
from dateutil import rrule
import datetime

intervals =  Statistic.INTERVALS

# interval constants
DAY = 'DY'
WEEK = 'WK'
MONTH = 'MN'

#
# This class aggregates commit data already scanned in based on intervals
# Intervals include: day (DY), week (WK), and month (MN).
#
class Rollup:

    # FIXME: this should be called 'now', not 'today' and really should be a function
    today = datetime.datetime.now(tz=timezone.utc)

    @classmethod
    def get_end_day(cls, date, interval):
        """
        Gets the last day of the week or month depending on interval,
        Sets the time to 11:59 PM or 23:59 for the day
        """
        if interval == WEEK:
            return date + datetime.timedelta(days=6)
        elif interval == MONTH:
            (weekday, days_in_month) = calendar.monthrange(date.year, date.month)
            return date.replace(day=days_in_month)
        elif interval == DAY:
            return date.replace(hour=23, minute=59, second=59, microsecond=99)
        else:
            raise Exception("invalid interval")

    @classmethod
    def smart_bulk_update(cls, repo=None, start_day=None, author=None, interval=None, stat=None, total_instances=None):

        """
        We batch statistics updates to keep things efficient but the current interval needs to be replaced, not updated.
        This code detects whether the rollup is in the current interval.
        """

        update = False
        if interval == DAY:
            if cls.today == start_day:
                update = True
        elif interval == WEEK:
            today_week = cls.today.isocalendar()[1]
            start_week = start_day.isocalendar()[1]
            if cls.today.year == start_day.year and today_week == start_week:
                update = True
        elif interval == MONTH:
            if cls.today.year == start_day.year and cls.today.year == start_day.year:
                update = True

        if update:
            # a rather expensive update of the current month if statistic already exists
            # that normally doesn't happen on most records.
            stats = Statistic.objects.filter(repo=repo, interval=interval, start_date=start_day)
            if author:
                stats = stats.filter(author=author)
            else:
                stats = stats.filter(author__isnull=True)
            stats = stats.all()
            if len(stats) == 0:
                update = False
            else:
                # just assuming this can't match more than one, not doing 'get' as exceptions are be slower
                old_stat = stats[0]
                old_stat.update(
                    lines_added=stat.lines_added,
                    lines_removed=stat.lines_removed,
                    lines_changed=stat.lines_changed,
                    commit_total=stat.commit_total,
                    files_changed=stat.files_changed,
                    author_total=stat.author_total
                )
                old_stat.save()

        if not update:
            total_instances.append(stat)

    @classmethod
    def compute_daily_rollup(cls, repo=None, author=None, start_day=None, total_instances=None):

        """
        Generate rollup stats for everything the team did on a given day
        """

        file_changes = FileChange.objects.select_related('commit', 'author').filter(
            commit__commit_date__year=start_day.year,
            commit__commit_date__month=start_day.month,
            commit__commit_date__day=start_day.day,
        )
        if file_changes.count() == 0:
            return

        if author:
            file_changes.filter(commit__author=author)

        # FIXME: probably not the most efficient way to do this
        commits = file_changes.values_list('commit', flat=True).distinct().all()
        files = file_changes.values_list('file', flat=True).distinct().all()
        authors = Commit.objects.filter(pk__in=commits).values_list('author', flat=True).distinct().all()
        authors_count = len(authors)

        # Aggregate values from query set for rollup
        data = file_changes.aggregate(lines_added=Sum("lines_added"), lines_removed = Sum("lines_removed"))
        commits_total = len(commits)
        files_changed = len(files)
        lines_added = data['lines_added']
        lines_removed = data['lines_removed']
        lines_changed = lines_added + lines_removed

        # FIXME: if start_day is today, we need to delete the current stat

        # Create total rollup row for the day
        stat = Statistic(
            start_date=start_day,
            interval=DAY,
            repo=repo,
            author=author,
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_changed=lines_changed,
            commit_total=commits_total,
            files_changed=files_changed,
            author_total=authors_count
        )

        cls.smart_bulk_update(repo=repo, start_day=start_day, author=author, interval=DAY, stat=stat, total_instances=total_instances)

    @classmethod
    def compute_interval_rollup(cls, repo=None, author=None, interval=None, start_day=None, total_instances=None):
        """
        Use the daily team stats to generate weekly or monthly rollup stats.
        start_day is the beginning of that period
        """

        # IF in weekly mode, and start_day is this week, we need to delete the current stat
        # IF in monthly mode, and start_day is this month, we need to delete the current stat

        end_date = cls.get_end_day(start_day, interval)
        days = Statistic.objects.filter(
            interval=DAY,
            repo=repo,
            start_date__range=(start_day, end_date)
        )
        if author:
            days.filter(author__isnull=True)
        else:
            days.filter(author=author)

        # aggregates total stats for the interval
        data = days.aggregate(
            lines_added=Sum("lines_added"),
            lines_removed=Sum("lines_removed"),
            lines_changed=Sum("lines_changed"),
            commit_total=Sum("commit_total"),
            files_changed=Sum("files_changed"),
            author_total=Sum("author_total")
        )

        stat = Statistic(
            start_date=start_day,
            interval=interval,
            repo=repo,
            author=author,
            lines_added=data['lines_added'],
            lines_removed=data['lines_removed'],
            lines_changed=data['lines_changed'],
            commit_total=data['commit_total'],
            files_changed=data['files_changed'],
            author_total=data['author_total']
        )

        cls.smart_bulk_update(repo=repo, start_day=start_day, author=author, interval=interval, stat=stat, total_instances=total_instances)


    @classmethod
    def get_authors_for_repo(cls, repo):
        assert repo is not None
        # FIXME: better query here would be nice, this probably isn't too efficient with 5000 authors
        author_ids = Commit.objects.filter(repo=repo).values_list("author", flat=True).distinct().all()
        authors = Author.objects.filter(pk__in=[author_ids]).all()
        return authors

    @classmethod
    def get_earliest_commit_date(cls, repo, author):
        return repo.earliest_commit_date(author)

    @classmethod
    def get_commit_days(cls, repo, author, interval):
        """
        Get every day we need to compute a rollup for within the time range.
        Daily rollups are optimized to ignore days without commits.
        Currently weekly/monthly ones are *not*, which might be nice, but make sure the graph code is cool w/ it.
        If a project is 20 years old, this could return a maximum of 7300 dates, which isn't horrific.
        It will return less if there is existing scan data.
        """

        assert repo is not None
        assert interval in [ DAY, MONTH, WEEK ]

        commits = None
        stats = None
        if author:
            commits = Commit.objects.filter(author=author, repo=repo)
            stats = Statistic.objects.filter(author=author, repo=repo, interval=interval)
        else:
            commits = Commit.objects.filter(repo=repo)
            stats = Statistic.objects.filter(author__isnull=True, repo=repo, interval=interval)

        scan_start = None
        if repo.last_scanned:
            scan_start = repo.last_scanned.date()
        else:
            scan_start = cls.get_earliest_commit_date(repo, author)
            if scan_start is None:
                print("no commits!")
                return

        def clear(d):
            return datetime.datetime(d.year, d.month, d.day)

        if interval == DAY:
            # we need to scan all days that DO have a commit and DONT have a daily rollup
            # and we also need to rescan today
            commit_dates = set([ x.date() for x in commits.values_list('commit_date', flat=True).all() ])
            stat_dates = set([ x.date() for x in stats.values_list('start_date', flat=True).all() ])

            rollup_dates = set([ x for x in commit_dates if x not in stat_dates ])
            rollup_dates.add(cls.today.date())
            rollup_dates = sorted([x for x in rollup_dates])
            for x in rollup_dates:
                yield clear(x)

        elif interval == WEEK:
            # just return the first of every week inside the time range
            # this may return periods where there are no commits, which is ok for now
            for dt in rrule.rrule(rrule.WEEKLY, dtstart=scan_start, until=cls.today):
                yield clear(dt)
        elif interval == MONTH:
            # just return the first of every month inside the time range
            # this may return periods where there are no commits, which is ok for now
            for dt in rrule.rrule(rrule.MONTHLY, dtstart=scan_start, until=cls.today):
                yield clear(dt)
        else:
            raise Exception('unknown interval')

    @classmethod
    def bulk_create(cls, total_instances):
        # by not ignoring conflicts, we can test whether our scanner "overwork" code is correct
        # use -F to try a full test from scratch
        Statistic.objects.bulk_create(total_instances, 5000, ignore_conflicts=False)
        del total_instances[:]

    @classmethod
    def finalize_scan(cls, repo):
        repo.last_scanned = cls.today.date()
        repo.save()

    @classmethod
    def rollup_team_stats(cls, repo):

        total_instances = []
        for start_day in cls.get_commit_days(repo=repo, author=None, interval=DAY):
            print("RD: %s" % start_day)
            cls.compute_daily_rollup(repo=repo, start_day=start_day, total_instances=total_instances)

        cls.bulk_create(total_instances)


        for start_day in cls.get_commit_days(repo=repo, author=None, interval=WEEK):
            print("RW: %s" % start_day)
            cls.compute_interval_rollup(repo=repo, start_day=start_day, interval=WEEK, total_instances=total_instances)
        cls.bulk_create(total_instances)

        for start_day in cls.get_commit_days(repo=repo, author=None, interval=MONTH):
            print("RM: %s" % start_day)
            cls.compute_interval_rollup(repo=repo, start_day=start_day, interval=MONTH, total_instances=total_instances)
        cls.bulk_create(total_instances)

    @classmethod
    def rollup_author_stats(cls, repo):

        total_instances = []
        for author in cls.get_authors_for_repo(repo):
            print("A: %s" % author)

            for start_day in cls.get_commit_days(repo=repo, author=author, interval=DAY):
                print("RD: %s/%s" % (author, start_day))
                cls.compute_daily_rollup(repo=repo, author=author, start_day=start_day, total_instances=total_instances)
            cls.bulk_create(total_instances)

            for start_day in cls.get_commit_days(repo=repo, author=author, interval=WEEK):
                print("RW: %s/%s" % (author, start_day))
                cls.compute_interval_rollup(repo=repo, author=author, interval=WEEK, start_day=start_day, total_instances=total_instances)
            cls.bulk_create(total_instances)

            for start_day in cls.get_commit_days(repo=repo, author=author, interval=MONTH):
                print("RM: %s/%s" % (author, start_day))
                cls.compute_interval_rollup(repo=repo, author=author, interval=MONTH, start_day=start_day, total_instances=total_instances)
            cls.bulk_create(total_instances)

    @classmethod
    def rollup_repo(cls, repo):
        """
        Compute rollups for specified repo passed in by daemon
        """

        assert repo is not None

        commits = Commit.objects.filter(repo=repo)
        if commits.count() == 0:
            cls.finalize_scan(repo)
            return

        cls.rollup_team_stats(repo)
        cls.rollup_author_stats(repo)
        cls.finalize_scan(repo)


