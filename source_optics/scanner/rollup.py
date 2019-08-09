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

import calendar
from django.db.models import Sum, Max
from django.utils import timezone
from source_optics.models import Statistic, Commit, FileChange, Author
from dateutil import rrule
import datetime
CURRENT_TZ = timezone.get_current_timezone()

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
    def aware(cls, date):
        # we previously had timezones turned on but they just cause trouble...
        # try:
        #    return timezone.make_aware(date, timezone.utc)
        #except:
        return date

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
            stats = Statistic.objects.filter(repo=repo, interval=interval, start_date=cls.aware(start_day))
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
        file_changes = None
        if not author:
            file_changes = FileChange.objects.select_related('commit').filter(
                commit__commit_date__year=start_day.year,
                commit__commit_date__month=start_day.month,
                commit__commit_date__day=start_day.day,
            )
        else:
            file_changes = FileChange.objects.select_related('commit', 'author').filter(
                commit__commit_date__year=start_day.year,
                commit__commit_date__month=start_day.month,
                commit__commit_date__day=start_day.day,
                commit__author=author
            )

        if file_changes.count() == 0:
            # FIXME: this occurs because we don't track git move paths perfectly and lose edits
            # that happen at the same time.  Fixing the rename code will fix this.
            print("***************** GLITCH ******************* ")
            return

        # FIXME: probably not the most efficient way to do this
        commits = file_changes.values_list('commit', flat=True).distinct().all()
        files = file_changes.values_list('file', flat=True).distinct().all()
        authors = Commit.objects.filter(pk__in=commits).values_list('author', flat=True).distinct().all()

        # FIXME: this may still be incorrect?

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
            start_date=cls.aware(start_day),
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

        assert repo is not None
        assert interval in [ 'WK', 'MN']
        assert start_day is not None

        start_day = start_day.replace(tzinfo=None)
        end_date = cls.get_end_day(start_day, interval)

        days = None
        if author is None:
            days = Statistic.objects.filter(
                author__isnull=True,
                interval=DAY,
                repo=repo,
                start_date__gte=start_day,
                start_date__lte=end_date
            )
        else:
            days = Statistic.objects.filter(
                author=author.pk,
                interval=DAY,
                repo=repo,
                start_date__gte=start_day,
                start_date__lte=end_date
            )
            if days.count() == 0:
                print("WARNING: NO HITS: SHOULDN'T BE HERE!: ", author, DAY, repo, cls.aware(start_day), cls.aware(end_date))
                # FIXME: temporary workaround bc of the file move code, this should probably be fatal
                # this can happen because the file move support is not quite smart about paths yet and seemingly
                # does not write FileChange records in those cases, which results in Statistic objects for days being
                # missing if all edits involved a move.  But we need to verify this.  The opsmop repo has a few examples.
                return

        # aggregates total stats for the interval
        data = days.aggregate(
            lines_added=Sum("lines_added"),
            lines_removed=Sum("lines_removed"),
            lines_changed=Sum("lines_changed"),
            commit_total=Sum("commit_total"),
            files_changed=Sum("files_changed"),
            author_total=Max("author_total")
        )

        stat = Statistic(
            start_date=cls.aware(start_day),
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
    def bulk_create(cls, total_instances):
        # by not ignoring conflicts, we can test whether our scanner "overwork" code is correct
        # use -F to try a full test from scratch
        Statistic.objects.bulk_create(total_instances, 100, ignore_conflicts=False)
        del total_instances[:]

    @classmethod
    def finalize_scan(cls, repo):
        repo.last_scanned = cls.today
        repo.save()

    @classmethod
    def rollup_team_stats(cls, repo):

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

        commit_weeks = commits.datetimes('commit_date', 'week', order='ASC')

        for start_day in commit_weeks:
            if repo.last_scanned and start_day < repo.last_scanned:
                break
            # FIXME: if after the last_scanned date

            print("(RTS2) compiling team stats: week=%s" % start_day)
            cls.compute_interval_rollup(repo=repo, start_day=start_day, interval=WEEK, total_instances=total_instances)
        cls.bulk_create(total_instances)

        commit_months = commits.datetimes('commit_date', 'month', order='ASC')

        for start_day in commit_months:
            # FIXME: if after the last_scanned date
            if repo.last_scanned and start_day < repo.last_scanned:
                break

            print("(RTS3) compiling team stats: month=%s" % start_day)
            cls.compute_interval_rollup(repo=repo, start_day=start_day, interval=MONTH, total_instances=total_instances)
        cls.bulk_create(total_instances)

    @classmethod
    def rollup_author_stats(cls, repo):

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



        for author in authors:

            commits = Commit.objects.filter(repo=repo, author=author)

            cls.bulk_create(total_instances)

            commit_weeks = commits.datetimes('commit_date', 'week', order='ASC')

            for start_day in commit_weeks:
                if repo.last_scanned and start_day < repo.last_scanned:
                    break
                # FIXME: if after the last_scanned date (is this still a FIXME?)

                print("(RAS2) compiling contributor stats: %s/%s (week=%s)" % (author_count, author_total, start_day))
                cls.compute_interval_rollup(repo=repo, author=author, interval=WEEK, start_day=start_day, total_instances=total_instances)

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


