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
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from source_optics.models import Statistic, Commit, Author

intervals =  Statistic.INTERVALS

#
# This class aggregates commit data already scanned in based on intervals
# Intervals include: day (DY), week (WK), and month (MN).
#
class Rollup:

    #Gets the current date in UTC date time
    today = datetime.datetime.now(tz=timezone.utc)

    #Counts the number of files for a given queryset of commits
    def count_files(commits):
        file_total = 0
        for c in commits.iterator():
            files = c.files
            file_total += files.count()
        return file_total

    #Gets the first day of the week or the month depending on intervals
    #Sets the time to 12:00 AM or 00:00 for that day
    def get_first_day(date_index, interval):
        if interval[0] == 'WK':
            date_index -= datetime.timedelta(days=date_index.isoweekday() % 7)
        elif interval[0] == 'MN':
            date_index = date_index.replace(day = 1)
        date_index = date_index.replace(hour=0, minute=0, second=0, microsecond=0)
        return date_index

    #Gets the last day of the week or month depending on INTERVALS
    #Sets the time to 11:59 PM or 23:59 for the day
    def get_end_day(date_index, interval):
        if interval[0] == 'WK':
            date_index = date_index + datetime.timedelta(days=6)
        elif interval[0] == 'MN':
            date_delta = date_index.replace(day = 28) + datetime.timedelta(days = 4)
            date_index = date_delta - datetime.timedelta(days=date_delta.day)

        date_index = date_index.replace(hour=23, minute=59, second=59, microsecond=99)
        return date_index

    # Aggregates the total rollup for the daily interval
    @classmethod
    def aggregate_day_rollup(cls,repo):

        total_instances = []
        date_index = repo.last_scanned

        # Daily rollups aren't dependent on the time
        # This allows us to scan the current day
        while date_index.date() != cls.today.date():

            # enable speeding by rollups already computed in event of ctrl-c or fault
            if (repo.last_rollup is None) or (repo.last_rollup <= date_index):
                date_index = cls.aggregate_day_rollup_internal(repo, total_instances, date_index)
                repo.last_rollup = date_index
                repo.save()
            else:
                date_index += datetime.timedelta(days=1)

        Statistic.objects.bulk_create(total_instances, 5000, ignore_conflicts=True)

        return date_index

    # FIXME: eliminate this function
    @classmethod
    def create_total_rollup(cls, start_date=None, interval=None, repo=None, lines_added=None, lines_removed=None,
                            lines_changed=None, commit_total=None, files_changed=None, author_total=None,
                            total_instances=None):
        total_instances.append(Statistic(start_date=start_date, interval=interval, repo=repo, lines_added=lines_added,
                                     lines_removed=lines_removed, lines_changed=lines_changed,
                                     commit_total=commit_total, files_changed=files_changed,
                                     author_total=author_total))

    # FIXME: eliminate this function / this should all use keyword arguments
    @classmethod
    def create_author_rollup(cls, start_date, interval, repo, author, lines_added, lines_removed,
                            lines_changed, commit_total, files_changed, author_instances):
        author_instances.append(Statistic(start_date = start_date, interval = interval, repo = repo, author=author, lines_added = lines_added,
        lines_removed = lines_removed, lines_changed = lines_changed, commit_total = commit_total, files_changed = files_changed))

    @classmethod
    def aggregate_day_rollup_internal(cls, repo, total_instances, date_index):

        # FIXME: we should be able to check if this already exists and not recalculate it.


        #Filters commits by date_index's day value as well as the repo
        commits = Commit.objects.filter(commit_date__contains=date_index.date(), repo=repo).prefetch_related('files')

        # If there are no commits for the day, continue
        if len(commits) == 0 :
            date_index += datetime.timedelta(days=1)
            return date_index
        print("Aggregate Day: %s, %s" % (repo, date_index))

        #Count the number of files in a commit
        file_total = cls.count_files(commits)

        #Get all the authors for the commits for that day
        authors_for_day = commits.values_list('author')
        author_count = len(set(authors_for_day))

        #Aggregate values from query set for rollup
        data = commits.aggregate(lines_added=Sum("lines_added"), lines_removed = Sum("lines_removed"))
        # FIXME: an object using slots here might be faster
        data['commit_total'] = len(commits)
        data['files_changed'] = file_total
        data['author_total'] = author_count
        #Calculated by adding lines added and removed
        data['lines_changed'] = int(data['lines_added']) + int(data['lines_removed'])

        # Create total rollup row for the day
        cls.create_total_rollup(start_date=date_index, interval=intervals[0][0], repo=repo,
            lines_added=data['lines_added'], 
            lines_removed=data['lines_removed'],
            lines_changed=data['lines_changed'], 
            commit_total=data['commit_total'], 
            files_changed=data['files_changed'],
            author_total=data['author_total'], 
            total_instances=total_instances)
        #Increment date_index to the next day
        date_index += datetime.timedelta(days=1)
        return date_index

    # Compile each statistic for each author over every day in the date range
    @classmethod
    def aggregate_author_rollup_day(cls, repo, author):

        #earliest_commit = Commit.objects.filter(repo=repo).earliest("commit_date").commit_date

        date_index = repo.last_scanned
        author_instances = []

        all_dates = [ x.date() for x in Commit.objects.filter(author=author, repo=repo).values_list('commit_date', flat=True).all() ]

        def has_date(which, many):
            for x in many:
                if x == which:
                    return True
            return False

        # Daily rollups aren't dependent on the time
        # This allows us to scan the current day
        while date_index.date() != cls.today.date():

            if not has_date(date_index.date(), all_dates):
                date_index += datetime.timedelta(days=1)
                continue
            else:
                print(" -> %s" % date_index)

            # FIXME: move to debug logging
            # print("Author Rollup by Day: %s, %s, %s" % (repo, date_index, author))

            #Filters commits by author,  date_index's day value, and repo
            commits = Commit.objects.filter(author=author, commit_date__contains=date_index.date(), repo=repo).prefetch_related('files')



            #Count the number of files in a commit
            file_total = cls.count_files(commits)

            #Aggregate values from query set for author rollup
            data = commits.aggregate(lines_added = Sum("lines_added"), lines_removed = Sum("lines_removed"))
            data['commit_total'] = len(commits)
            data['files_changed'] = file_total

            #Calculated by adding lines added and removed
            data['lines_changed'] = int(data['lines_added']) + int(data['lines_removed'])

            # Create author rollup row for the day
            cls.create_author_rollup(date_index, intervals[0][0], repo, author, data['lines_added'], data['lines_removed'],
            data['lines_changed'], data['commit_total'], data['files_changed'], author_instances)

            #Increment date_index to the next day
            date_index += datetime.timedelta(days=1)

        Statistic.objects.bulk_create(author_instances, 5000, ignore_conflicts=True)

    # Compile each statistic for the author based on the interval over the date range
    @classmethod
    def aggregate_author_rollup(cls, repo, interval):

        date_index = cls.get_first_day(repo.last_scanned, interval)
        author_instances = []

        while date_index < cls.today:

            # FIXME: move to debug logging
            print("Author Rollup Aggregration: repo=%s, interval=%s" % (repo, interval))
            end_date = cls.get_end_day(date_index, interval)


            #Gets all the daily author statistic objects
            #.values parameter groups author objects by author id
            #.annotate sums the relevant statisic and adds a new field to the queryset
            days = Statistic.objects.filter(
                interval='DY',
                author__isnull=False,
                file=None,
                repo=repo,
                start_date__range=(date_index, end_date)
            ).values('author_id').annotate(lines_added_total=Sum("lines_added"), lines_removed_total = Sum("lines_removed"),
                                lines_changed_total = Sum("lines_changed"), commit_total_total = Sum("commit_total"),
                                files_changed_total = Sum("files_changed"), author_total_total = Sum("author_total"))


            #iterate through the query set and create author objects
            author = None
            for d in days:
                author = Author.objects.get(pk=d['author_id'])
                # FIXME: these should use keyword arguments
                cls.create_author_rollup(date_index, interval[0], repo, author, d['lines_added_total'], d['lines_removed_total'],
                d['lines_changed_total'], d['commit_total_total'], d['files_changed_total'], author_instances)

            #Increment to next week or month
            end_date = end_date + datetime.timedelta(days=1)
            date_index = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

        Statistic.objects.bulk_create(author_instances, 5000, ignore_conflicts=True)


    #Compile rollup for interval by aggregating daily stats
    @classmethod
    def aggregate_interval_rollup(cls, repo, interval):

        # FIXME: move to debug logging
        print("Interval Rollup: %s, %s" % (repo, interval))

        #Gets the first day depending on the interval
        date_index = cls.get_first_day(repo.last_scanned, interval)
        total_instances = []

        while date_index < cls.today:
            end_date = cls.get_end_day(date_index, interval)

            days = Statistic.objects.filter(interval = 'DY', author = None, repo = repo, file = None, start_date__range=(date_index, end_date))

            #Aggregates total stats for the interval
            data = days.aggregate(lines_added=Sum("lines_added"), lines_removed = Sum("lines_removed"),
                                lines_changed = Sum("lines_changed"), commit_total = Sum("commit_total"),
                                files_changed = Sum("files_changed"), author_total = Sum("author_total"))

            #Creates row for given interval
            cls.create_total_rollup(start_date=date_index, interval=interval[0], repo=repo,
                lines_added=data['lines_added'], 
                lines_removed=data['lines_removed'],
                lines_changed=data['lines_changed'], 
                commit_total=data['commit_total'], 
                files_changed=data['files_changed'], 
                author_total=data['author_total'], 
                total_instances=total_instances)

            #Increment to next week or month
            end_date = end_date + datetime.timedelta(days=1)
            date_index = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

        Statistic.objects.bulk_create(total_instances, 5000, ignore_conflicts=True)

    #Compile total rollups for all intervals
    @classmethod
    def compile_total_rollup (cls, repo, interval):
        #Compile day using repo data
        if interval[0] == 'DY': # FIXME: use constants everywhere
            last_scanned = cls.aggregate_day_rollup(repo)
        #compile other intervals using day stats which have been aggregated
        else:
            last_scanned = cls.aggregate_interval_rollup(repo, interval)
        return last_scanned

    #We only want to iterate through the authors once.
    #Currently, this seems like the easiest way to do so
    @classmethod 
    def compile_author_rollups (cls, repo):
        #Need to compile authors separately. Iterator is used for memory efficiency
        authors = Author.objects.filter(repos__in=[repo]).iterator()
        total_authors = Author.objects.filter(repos__in=[repo]).count()

        count = 0
        for author in authors:
            count = count + 1
            print("Author %s: %s -> # %s/%s" % (repo, author, count, total_authors))
            cls.aggregate_author_rollup_day(repo, author)
            # FIXME: use specific constants for day and week here.
        cls.aggregate_author_rollup(repo, intervals[1])
        cls.aggregate_author_rollup(repo, intervals[2])

    #Compute rollups for specified repo passed in by daemon
    #TODO: Index commit_date and repo together
    @classmethod
    # FIXME: shouldn't be atomic here probably, so killing halfway through allows resumption
    @transaction.atomic
    def rollup_repo(cls, repo):

        #This means that the repo has not been scanned
        if repo.last_scanned is None:
            #So we set the last scanned field to the earliest commit field
            # FIXME: if there are no commits, don't crash - possible scenario for new repos
            earliest_commit = Commit.objects.filter(repo=repo).earliest("commit_date").commit_date
            repo.last_scanned = earliest_commit
            repo.earliest_commit = earliest_commit

        for interval in intervals:
            # FIXME: the return from this function is never used, should it be?
            # FIXME: also it says 'last_scanned' but rollups should record different times
            cls.compile_total_rollup(repo, interval)

        cls.compile_author_rollups(repo)

        #Set last scanned date to today
        repo.last_scanned = cls.today
        repo.save()
