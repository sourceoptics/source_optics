from django.utils.dateparse import parse_datetime
from django.db.models import Sum, Count
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

    @classmethod
    def aggregate_day_rollup(cls,repo):
        #make sure that we're scanning the repository for the current day as well
        today = datetime.datetime.now(tz=timezone.utc).date()
        temp_date = repo.last_scanned

        print("Aggregating daily stats from " + str(temp_date.date()) + " to " + str(today))
        while temp_date.date() != today:
            #Commit.objects.annotate(Count("files"))
            commits = Commit.objects.filter(commit_date__contains=temp_date.date(), repo=repo)
            
            if len(commits) == 0:
                temp_date += datetime.timedelta(days=1)
                continue

            #file statistics as well as aggregate file count for total rollups
            file_total = 0
            for c in commits.iterator():
                files = c.files
                file_total = files.count()


            temp = commits.aggregate(Sum("lines_added"), Sum("lines_removed"), Sum("author"))
            temp['commit_total'] = len(commits)
            temp['files_changed'] = file_total

            if temp['lines_added__sum'] is None:
                temp['lines_added__sum'] = 0
            if temp['lines_removed__sum'] is None:
                temp['lines_removed__sum'] = 0

            temp['lines_changed'] = int(temp['lines_added__sum']) + int(temp['lines_removed__sum'])

            data = json.dumps(temp)
            stat = Statistic.create_total_rollup(temp_date, intervals[0], repo, data)
            print(stat)

            temp_date += datetime.timedelta(days=1)
        return temp_date

    @classmethod
    def aggregate_author_rollup_day(cls, repo, author, temp_date):
        today = datetime.datetime.now(tz=timezone.utc).date()
        temp_date = repo.last_scanned
        while temp_date.date() != today:

            commits = Commit.objects.filter(author=author, commit_date__contains=temp_date.date(), repo=repo)

            if len(commits) == 0:
                temp_date += datetime.timedelta(days=1)
                continue

            file_total = 0
            for c in commits.iterator():
                files = c.files
                file_total = files.count()
            temp = commits.aggregate(Sum("lines_added"), Sum("lines_removed"))
            temp['commit_total'] = len(commits)
            temp['files_changed'] = file_total

            if temp['lines_added__sum'] is None:
                temp['lines_added__sum'] = 0
            if temp['lines_removed__sum'] is None:
                temp['lines_removed__sum'] = 0
            
            temp['lines_changed'] = int(temp['lines_added__sum']) + int(temp['lines_removed__sum'])

            data = json.dumps(temp)
            stat = Statistic.create_author_rollup(temp_date, intervals[0], repo, author, data)
            print(stat)
            temp_date += datetime.timedelta(days=1)

    @classmethod
    def compile_rollup (cls, repo, interval):
        if repo.last_scanned is None:
            repo.last_scanned = Commit.objects.filter(repo=repo).earliest("commit_date").commit_date
        if interval[0] is 'DY':
            temp_date = cls.aggregate_day_rollup(repo)
            authors = Author.objects.filter(repos__in=[repo]).iterator()
            for author in authors:
                cls.aggregate_author_rollup_day(repo, author, temp_date)
            repo.last_scanned = temp_date
            repo.save()

    @classmethod
    def rollup_repo(cls):
        repos = Repository.objects.all()
        for repo in repos:
            for interval in intervals:
                cls.compile_rollup(repo, interval)
