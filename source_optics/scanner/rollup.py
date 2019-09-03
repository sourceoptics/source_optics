# Copyright 2018-2019 SourceOptics Project Contributors
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

# FIXME: this whole class is well overdue for splitting up into smaller
# functions and/or multiple files.

import calendar
import datetime

from django.utils import timezone

from source_optics.models import Author, Commit, FileChange, Statistic
import source_optics.models as models

CURRENT_TZ = timezone.get_current_timezone()

intervals =  Statistic.INTERVALS

# interval constants
DAY = 'DY'
WEEK = 'WK'
MONTH = 'MN'
LIFETIME = 'LF'

#
# This class aggregates commit data already scanned in based on intervals
# Intervals include: day (DY), week (WK), and month (MN).
#
class Rollup:

    """
    The rollup class is responsible for building the statistics table.  First it computes
    daily totals by looking at commits and file change records recorded by the Commit class.
    From there, we can work on Weekly rollups and Monthly rollups of that data.  These are still
    time ranged. Lifetime rollups also exist, but are NOT time ranged (obviously?). And all of
    these types of rollups exist for each author and if the author is None, that represents an
    entire repository.  It's a lot of calculation, which is why this is all a backend CLI
    command and not done within the life of a request. Performance upgrades can always be
    made and are always welcome - the thing that will make the system do the most work is
    repositories with thousands of authors, scaling with commits doesn't really increase
    the amount of queries performed, though a very long source code history does
    take a little longer than a shorter one.
    """

    today = timezone.now()

    @classmethod
    def aware(cls, date):
        # FIXME: we can eliminate this function, it doesn't do anything anymore
        return date

    @classmethod
    def get_end_day(cls, date, interval):
        """
        Gets the last day of the week or month depending on interval,
        Sets the time to 11:59 PM or 23:59 for the day
        """
        if interval == WEEK:
            result = date + datetime.timedelta(days=6)
            return result.replace(hour=23, minute=59, second=59, microsecond=99)
        elif interval == MONTH:
            (weekday, days_in_month) = calendar.monthrange(date.year, date.month)
            return date.replace(day=days_in_month, hour=23, minute=59, second=59, microsecond=99)
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

        # FIXME: all this code should be cleaned up.

        # FIXME: add a method here like "should_update_statistic"
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
        elif interval == LIFETIME:
            update = True

        if update:
            # a rather expensive update of the current month if statistic already exists
            # that normally doesn't happen on most records.
            if interval != LIFETIME:
                stats = Statistic.objects.filter(repo=repo, interval=interval, start_date=cls.aware(start_day))
            else:
                stats = Statistic.objects.filter(repo=repo, interval=interval)
            if author:
                stats = stats.filter(author=author)
            else:
                stats = stats.filter(author__isnull=True)
            stats = stats.all()
            if len(stats) == 0:
                update = False
            else:
                # just assuming this can't match more than one, not doing 'get' as exceptions are be slower
                old_stat = stats.first()
                old_stat.copy_fields_for_update(stat)
                old_stat.save()

        if not update:
            total_instances.append(stat)

    @classmethod
    def compute_daily_rollup(cls, repo=None, author=None, start_day=None, total_instances=None):

        """
        Generate rollup stats for everything the team did on a given day
        """

        end_date = cls.get_end_day(start_day, DAY)

        file_change_count = FileChange.change_count(repo, author=author, start=start_day, end=end_date)

        if file_change_count == 0:
            # this looks like a merge commit, FIXME: it would be a good idea to validate that this is 100% true.
            print("-- skipping potential merge commit --")
            return

        if not author:
            authors_count = Author.author_count(repo, start=start_day, end=end_date)
        else:
            authors_count = 1

        # Aggregate values from query set for rollup

        data = FileChange.aggregate_stats(repo, author=author, start=start_day, end=end_date)

        # FIXME: if start_day is today, we need to UPDATE the current stat? - verify if the bulk_update code deals with this?
        # FIXME: model code method below is rather inefficient, does this matter?

        # Create total rollup row for the day
        stat = Statistic(
            start_date=start_day,
            interval=DAY,
            repo=repo,
            author=author,
            lines_added=data['lines_added'],
            lines_removed=data['lines_removed'],
            lines_changed=data['lines_changed'],
            commit_total= data['commit_total'],
            files_changed=data['files_changed'],
            author_total=authors_count,
            average_commit_size=data['average_commit_size'],
            days_active=1,
        )

        cls.smart_bulk_update(repo=repo, start_day=start_day, author=author, interval=DAY, stat=stat, total_instances=total_instances)

    @classmethod
    def _queryset_for_interval_rollup(cls, repo=None, author=None, interval=None, start_day=None, end_date=None):
        """
        returns the queryset needed to select Statistic rows for a weekly, monthly, or lifetime rollup, which may or may not be
        author specific.
        """

        if author is None:
            if interval != LIFETIME:
                return Statistic.objects.filter(
                    author__isnull=True,
                    interval=DAY,
                    repo=repo,
                    # FIXME: use range everywhere
                    start_date__gte=start_day,
                    start_date__lte=end_date
                )
            else:
                return Statistic.objects.filter(
                    author__isnull=True,
                    interval=DAY,
                    repo=repo,
                )
        else:
            if interval != LIFETIME:
                return Statistic.objects.filter(
                    author=author,
                    interval=DAY,
                    repo=repo,
                    # FIXME: use range everywhere
                    start_date__gte=start_day,
                    start_date__lte=end_date
                )
            else:
                return Statistic.objects.filter(
                    author=author,
                    interval=DAY,
                    repo=repo,
                )

    @classmethod
    def start_and_end_dates_for_interval(cls, repo=None, author=None, start=None, interval=None):
        """
        Given a start date, what is the end date for the interval?
        """
        assert (interval == 'LF' or start is not None)
        assert interval is not None
        absolute_first_commit_date = repo.earliest_commit_date()
        absolute_last_commit_date = repo.latest_commit_date()
        assert absolute_first_commit_date is not None
        assert absolute_last_commit_date is not None
        if interval != LIFETIME:
            start_day = start.replace(tzinfo=None)
            end_date = cls.get_end_day(start, interval)
        else:
            # lifetime...
            if author:
                start_day = repo.earliest_commit_date(author=author)
                end_date = repo.latest_commit_date(author=author)
            else:
                start_day = repo.earliest_commit_date()
                end_date = repo.latest_commit_date()
            if start_day is None or end_date is None:
                # this MAY happen if the author has no commits, but that shouldn't be likely
                # we'll handle the issue just to be paranoid about it though.
                return (None, None)
        return (start, end_date)

    @classmethod
    def compute_interval_rollup(cls, repo=None, author=None, interval=None, start_day=None, total_instances=None):
        """
        Use the daily team stats to generate weekly or monthly rollup stats.
        start_day is the beginning of that period
        """

        # FIXME: all this code should be cleaned up.

        # IF in weekly mode, and start_day is this week, we need to delete the current stat
        # IF in monthly mode, and start_day is this month, we need to delete the current stat

        assert repo is not None
        assert interval in [ 'WK', 'MN', 'LF']

        (start_day, end_date) = cls.start_and_end_dates_for_interval(repo=repo, author=author, start=start_day, interval=interval)
        if start_day is None and interval != 'LF':
            print("**** GLITCH: Author has no commits? ", author)
            return

        days = cls._queryset_for_interval_rollup(repo=repo, author=author, interval=interval, start_day=start_day, end_date=end_date)

        if days.count() == 0:
            # probably just a merge commit today, be cool about it and skip this one.
            return

        stat = Statistic.compute_interval_statistic(days, repo=repo, interval=interval, author=author, start=start_day, end=end_date)

        cls.smart_bulk_update(repo=repo, start_day=start_day, author=author, interval=interval, stat=stat, total_instances=total_instances)


    @classmethod

    def get_authors_for_repo(cls, repo):
        """
        Return the authors involved in the repo
        """
        return Author.authors(repo)


    @classmethod
    def get_earliest_commit_date(cls, repo, author):
        # FIXME: this should really be memozed, it is called way too much.  We should do that
        # in the model class and then eliminate this function.
        return repo.earliest_commit_date(author)

    @classmethod
    def bulk_create(cls, total_instances):
        """
        Creates a bunch of statistic objects that have been queued up for insertion.
        """
        # by not ignoring conflicts, we can test whether our scanner "overwork" code is correct
        # use -F to try a full test from scratch
        Statistic.objects.bulk_create(total_instances, 100, ignore_conflicts=False)
        del total_instances[:]

    @classmethod
    def finalize_scan(cls, repo):
        """
        Flags a scan as completed.
        """
        repo.last_scanned = cls.today
        repo.save()

    @classmethod
    def rollup_team_stats(cls, repo):
        """
        Computes the day, week, month, and lifetime stats for a repo, but on a team basis, not a per author basis.
        """

        commits = Commit.objects.filter(repo=repo)

        commit_days = commits.datetimes('commit_date', 'day', order='ASC')

        total_instances = []
        for start_day in commit_days:

            if repo.last_scanned and start_day < repo.last_scanned:
                break
            # FIXME: if after the last_scanned date
            print("(RTS1) compiling team stats: day=%s" % start_day)
            cls.compute_daily_rollup(repo=repo, start_day=start_day, total_instances=total_instances)

        cls.bulk_create(total_instances)
        models.cache_clear()

        commit_weeks = commits.datetimes('commit_date', 'week', order='ASC')

        for start_day in commit_weeks:
            if repo.last_scanned and start_day < repo.last_scanned:
                break
            # FIXME: if after the last_scanned date

            print("(RTS2) compiling team stats: week=%s" % start_day)
            cls.compute_interval_rollup(repo=repo, start_day=start_day, interval=WEEK, total_instances=total_instances)

        cls.bulk_create(total_instances)
        models.cache_clear()

        commit_months = commits.datetimes('commit_date', 'month', order='ASC')

        for start_day in commit_months:
            # FIXME: if after the last_scanned date
            if repo.last_scanned and start_day < repo.last_scanned:
                break

            print("(RTS3) compiling team stats: month=%s" % start_day)
            cls.compute_interval_rollup(repo=repo, start_day=start_day, interval=MONTH, total_instances=total_instances)

        print("(RTS4) compiling team stats: lifetime")
        cls.compute_interval_rollup(repo=repo, start_day=None, interval=LIFETIME, total_instances=total_instances)

        cls.bulk_create(total_instances)
        models.cache_clear()

    @classmethod
    def rollup_author_stats(cls, repo):
        """
        Computes the day, week, month, and lifetime stats for a repo, for all authors in that repo.  Contrast
        with rollup_team_stats.
        """

        # FIXME: very long function, refactor/simplify.

        total_instances = []

        authors = cls.get_authors_for_repo(repo)
        author_count = 0
        author_total = len(authors)

        for author in authors:

            commits = Commit.objects.filter(repo=repo, author=author)
            author_count = author_count + 1

            print("(RAS1) compiling contributor stats: %s/%s" % (author_count, author_total))

            commit_days = commits.datetimes('commit_date', 'day', order='ASC')

            # print("author commit days: ", author, commit_days)

            for start_day in commit_days:
                if repo.last_scanned and start_day < repo.last_scanned:
                    break
                # FIXME: if after the last_scanned date (is this still a FIXME?)
                cls.compute_daily_rollup(repo=repo, author=author, start_day=start_day, total_instances=total_instances)

            if len(total_instances) > 2000:
                cls.bulk_create(total_instances)

        cls.bulk_create(total_instances)
        models.cache_clear()


        author_count = 0

        for author in authors:

            author_count = author_count + 1

            commits = Commit.objects.filter(repo=repo, author=author)

            cls.bulk_create(total_instances)

            commit_weeks = commits.datetimes('commit_date', 'week', order='ASC')

            for start_day in commit_weeks:
                if repo.last_scanned and start_day < repo.last_scanned:
                    break
                # FIXME: if after the last_scanned date (is this still a FIXME?)

                print("(RAS2) compiling contributor stats: %s/%s (week=%s)" % (author_count, author_total, start_day))
                cls.compute_interval_rollup(repo=repo, author=author, interval=WEEK, start_day=start_day, total_instances=total_instances)

        cls.bulk_create(total_instances)
        models.cache_clear()

        author_count = 0

        for author in authors:
            author_count = author_count + 1
            commits = Commit.objects.filter(repo=repo, author=author)

            commit_months = commits.datetimes('commit_date', 'month', order='ASC')

            for start_day in commit_months:
                # FIXME: if after the last_scanned date (is this still a FIXME?)
                if repo.last_scanned and start_day < repo.last_scanned:
                    break
                print("(RAS3) compiling contributor stats: %s/%s (month=%s)" % (author_count, author_total, start_day))
                cls.compute_interval_rollup(repo=repo, author=author, interval=MONTH, start_day=start_day, total_instances=total_instances)

            if len(total_instances) > 2000:
                cls.bulk_create(total_instances)

        cls.bulk_create(total_instances)
        models.cache_clear()

        author_count = 0

        for author in authors:

            author_count = author_count + 1

            print("(RAS4) compiling contributor stats: %s/%s (lifetime)" % (author_count, author_total))
            cls.compute_interval_rollup(repo=repo, author=author, interval=LIFETIME, start_day=None, total_instances=total_instances)

        cls.bulk_create(total_instances)
        models.cache_clear()


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
