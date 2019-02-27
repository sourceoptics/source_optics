from django.utils.dateparse import parse_datetime
from django.db.models import Sum, Count
from django.conf import settings
from django.utils import timezone
from srcOptics.models import *
from srcOptics.create import Creator
import datetime
import json


intervals =  Statistic.INTERVALS

class Rollup:

    @classmethod
    def aggregate_day_rollup(cls,repo):
        #make sure that we're scanning the repository for the current day as well
        today = datetime.datetime.now(tz=timezone.utc).date()
        temp_date = repo.last_scanned
        print("TODAY: " + str(today))
        while temp_date.date() != today:
            #Commit.objects.annotate(Count("files"))
            commits = Commit.objects.filter(commit_date__contains=temp_date.date())

            file_total = 0
            for c in commits:
                file_total = c.files.count()
                print(file_total)




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
            #print(stat)
            #for commit in commits:
            #    print("COMMIT: ",  commit.commit_date)
            temp_date += datetime.timedelta(days=1)
            #print("TEMP  " + str(temp_date))


    @classmethod
    def compile_rollup (cls, repo, interval):
        if repo.last_scanned is None:
            repo.last_scanned = Commit.objects.filter(repo=repo).earliest("commit_date").commit_date
        cls.aggregate_day_rollup(repo)

    @classmethod
    def rollup_repo(cls):
        repos = Repository.objects.all()
        print(intervals)
        for repo in repos:
            #for i in intervals:
                #this is the key for the interval (DY, WK, MN)
            interval = intervals[0]
            cls.compile_rollup(repo, interval)
