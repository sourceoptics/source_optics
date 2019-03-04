from django.utils.dateparse import parse_datetime
from django.db.models import Sum, Count, IntegerField
from django.db.models.functions import Cast
from django.conf import settings
from django.utils import timezone
from srcOptics.models import *
from srcOptics.create import Creator
import datetime
import json


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
        if interval[0] is 'WK':
            date_index -= datetime.timedelta(days=date_index.isoweekday() % 7)
        elif interval[0] is 'MN':
            date_index = date_index.replace(day = 1)
        date_index = date_index.replace(hour=0, minute=0, second=0, microsecond=0)
        return date_index

    #Gets the last day of the week or month depending on INTERVALS
    #Sets the time to 11:59 PM or 23:59 for the day
    def get_end_day(date_index, interval):
        if interval[0] is 'WK':
            date_index = date_index + datetime.timedelta(days=6)
        elif interval[0] is 'MN':
            date_delta = date_index.replace(day = 28) + datetime.timedelta(days = 4)
            date_index = date_delta - datetime.timedelta(days=date_delta.day)

        date_index = date_index.replace(hour=11, minute=59, second=59, microsecond=99)
        return date_index


    # Aggregates the total rollup for the daily interval
    @classmethod
    def aggregate_day_rollup(cls,repo):

        date_index = repo.last_scanned
        print("Aggregating daily stats from " + str(date_index.date()) + " to " + str(cls.today))

        # Daily rollups aren't dependent on the time
        # This allows us to scan the current day
        while date_index.date() != cls.today.date():

            #Filters commits by date_index's day value as well as the repo
            commits = Commit.objects.filter(commit_date__contains=date_index.date(), repo=repo)

            # If there are no commits for the day, continue
            if len(commits) == 0:
                date_index += datetime.timedelta(days=1)
                continue

            #Count the number of files in a commit
            file_total = cls.count_files(commits)

            #Get all the authors for the commits for that day
            authors_for_day = commits.values_list('author')
            author_count = len(set(authors_for_day))

            #Aggregate values from query set for rollup
            data = commits.aggregate(lines_added=Sum("lines_added"), lines_removed = Sum("lines_removed"))
            data['commit_total'] = len(commits)
            data['files_changed'] = file_total
            data['author_total'] = author_count
            #Calculated by adding lines added and removed
            data['lines_changed'] = int(data['lines_added']) + int(data['lines_removed'])

            # Create total rollup row for the day
            stat = Statistic.create_total_rollup(date_index, intervals[0][0], repo, data['lines_added'], data['lines_removed'],
            data['lines_changed'], data['commit_total'], data['files_changed'], data['author_total'])
        #    print(stat)
            #Increment date_index to the next day
            date_index += datetime.timedelta(days=1)
        return date_index

    @classmethod
    def aggregate_author_rollup_day(cls, repo, author):

        date_index = repo.last_scanned

        # Daily rollups aren't dependent on the time
        # This allows us to scan the current day
        while date_index.date() != cls.today.date():

            #Filters commits by author,  date_index's day value, and repo
            commits = Commit.objects.filter(author=author, commit_date__contains=date_index.date(), repo=repo)

            # If there are no commits for the day, continue
            if len(commits) == 0:
                date_index += datetime.timedelta(days=1)
                continue

            #Count the number of files in a commit
            file_total = cls.count_files(commits)

            #Aggregate values from query set for author rollup
            data = commits.aggregate(lines_added = Sum("lines_added"), lines_removed = Sum("lines_removed"))
            data['commit_total'] = len(commits)
            data['files_changed'] = file_total

            #Calculated by adding lines added and removed
            data['lines_changed'] = int(data['lines_added']) + int(data['lines_removed'])

            # Create author rollup row for the day
            stat = Statistic.create_author_rollup(date_index, intervals[0][0], repo, author, data['lines_added'], data['lines_removed'],
            data['lines_changed'], data['commit_total'], data['files_changed'])
            #print(stat)

            #Increment date_index to the next day
            date_index += datetime.timedelta(days=1)

    @classmethod
    def aggregate_author_rollup(cls, repo, author, interval):
        a = 1

    #Compile rollup for interval by aggregating daily stats
    @classmethod
    def aggregate_interval_rollup(cls, repo, interval):

        #Gets the first day depending on the interval
        date_index = cls.get_first_day(repo.last_scanned, interval)


        while date_index < cls.today:
            end_date = cls.get_end_day(date_index, interval)
            print("RANGE: " + str(date_index) + " TO " + str(end_date))

            #Gets the total stats for each day in the given interval
            #If author and file = none, we are getting total stats
            days = Statistic.objects.filter(interval = 'DY', author = None, repo = repo, file = None, start_date__range=(date_index, end_date))

            #Aggregates total stats for the interval
            data = days.aggregate(lines_added=Sum("lines_added"), lines_removed = Sum("lines_removed"),
                                lines_changed = Sum("lines_changed"), commit_total = Sum("commit_total"),
                                files_changed = Sum("files_changed"), author_total = Sum("author_total"))

            #Creates row for given interval
            stat = Statistic.create_total_rollup(date_index, interval[0], repo, data['lines_added'], data['lines_removed'],
            data['lines_changed'], data['commit_total'], data['files_changed'], data['author_total'])

            print(stat)

            #Increment to next week or month
            end_date = end_date + datetime.timedelta(days=1)
            date_index = end_date.replace(hour=0, minute=0, second=0, microsecond=0)


    #Compile total rollups for all intervals
    @classmethod
    def compile_total_rollup (cls, repo, interval):
        #Compile day using repo data
        if interval[0] is 'DY':
            last_scanned = cls.aggregate_day_rollup(repo)
        #compile other intervals using day stats which have been aggregated
        else:
            last_scanned = cls.aggregate_interval_rollup(repo, interval)


    #We only want to iterate through the authors once.
    #Currently, this seems like the easiest way to do so
    @classmethod
    def compile_author_rollups (cls, repo):
        #Need to compile authors separately. Iterator is used for memory efficiency
        authors = Author.objects.filter(repos__in=[repo]).iterator()
        for author in authors:
            cls.aggregate_author_rollup_day(repo, author)
            #week
            cls.aggregate_author_rollup(repo, author, intervals[1])
            #month
            cls.aggregate_author_rollup(repo, author, intervals[2])



    #Compute rollups for all repos scanned in
    @classmethod
    def rollup_repo(cls):
        repos = Repository.objects.all()
        for repo in repos:

            #This means that the repo has not been scanned
            if repo.last_scanned is None:
                #So we set the last scanned field to the earliest commit field
                repo.last_scanned = Commit.objects.filter(repo=repo).earliest("commit_date").commit_date

            for interval in intervals:
                cls.compile_total_rollup(repo, interval)

            cls.compile_author_rollups(repo)

            #Set last scanned date to today
            repo.last_scanned = cls.today
            repo.save()
