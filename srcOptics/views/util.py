from django.http import *
from django.core import serializers
from datetime import datetime, timedelta
from django.utils import timezone

from django.db.models import Sum

from ..models import *
from srcOptics.stats.rollup import Rollup
from django.contrib.humanize.templatetags.humanize import intcomma


"""
Returns a JSON list of repositories by search query
"""
def search(request, q):
    org = request.GET.get('org')

    repos = query(q, org)
    data = serializers.serialize('json',repos)
    return HttpResponse(data, content_type='application/json')

"""
Returns a list of Repository objects from filter query
"""
def query(q, org):
    repos = None

    if not q:
        if not org or org == 'all':
            repos = Repository.objects.all()
        else:
            repos = Repository.objects.filter(organization__name=org)
    else:
        if not org or org == 'all':
            repos = Repository.objects.filter(name__icontains=q)
        else:
            repos = Repository.objects.filter(organization__name=org, name__icontains=q)
        #TODO: fix tag query search to filter by org as well
        tag_query = Tag.objects.filter(name__icontains=q)
        for tag in tag_query:
            repos |= tag.repos.all()
    return repos

"""
Generate a dictionary with all the statistics for a given repository, given author,
and given date range
"""
def aggregate_stats(repo, author, start, end):

    # Get statistics objects in the appropriate interval
    days = Statistic.objects.filter(interval='DY', repo=repo, author=author, file=None, start_date__range=(start, end))

    # Calculate sums from statistics objects into an object
    totals = days.aggregate(lines_added=Sum("lines_added"), lines_removed=Sum("lines_removed"),
                    lines_changed=Sum("lines_changed"), commit_total=Sum("commit_total"),
                    files_changed=Sum("files_changed"), author_total=Sum("author_total"))

    # append to stats list
    totals['repo_last_scanned'] = repo.last_scanned
    totals['repo_last_pulled'] = repo.last_pulled

    totals['repo_tags'] = repo.tags.all()

    return totals

"""
Returns a list of Statistic objects from start / end date in
a given list of repositories
"""
def get_all_repo_stats(**kwargs):
    # Loop through repos and add appropriate statistics to table
    stats = []
    for repo in kwargs['repos']:
        totals = aggregate_stats(repo, kwargs.get('author'), kwargs['start'], kwargs['end'])
        # Add repository name to totals object to display
        totals['repo'] = repo
        stats.append(totals)
    return stats

"""
Returns a list of Statistic objects for a list of authors in a
given time interval
"""
def get_all_author_stats(**kwargs):
    stats = []
    for author in kwargs['authors']:
        totals = aggregate_stats(kwargs['repo'], author, kwargs['start'], kwargs['end'])
        # Add repository name to totals object to display
        totals['author'] = author
        stats.append(totals)
    return stats


"""
Returns a list of author contributions for ALL repositories in the
given time interval
"""
def get_total_author_stats(**kwargs):
    author = kwargs['author']
    stats = []
    for repo in author.repos.all():
        totals = aggregate_stats(repo, author, kwargs['start'], kwargs['end'])
        # Add repository name to totals object to display
        totals['author'] = author
        totals['repo'] = repo
        stats.append(totals)
    return stats


def get_query_strings(request):
    queries = {}

    start = request.GET.get('start')
    end = request.GET.get('end')

    # Sets default date range to a week if no query string is specified
    if not start or not end:
        queries['end'] = datetime.now()
        queries['start'] = queries['end'] - timedelta(days=7)
    else:
        queries['start'] = datetime.strptime(start, '%Y-%m-%d')
        queries['end'] = datetime.strptime(end, '%Y-%m-%d')

    attribute = request.GET.get('attr')
    if not attribute:
        queries['attribute'] = Statistic.ATTRIBUTES[0][0]
    else:
        queries['attribute'] = request.GET.get('attr')

    interval = request.GET.get('intr')
    if not interval:
        queries['interval'] = Statistic.INTERVALS[0][0]
    else:
        queries['interval'] = request.GET.get('intr')


    return queries

# author summary statistics
def get_lifetime_stats_author(author):
    commits = Commit.objects.filter(author=author).order_by('commit_date')
    earliest = commits[0].commit_date
    today = datetime.now(tz=timezone.utc)
    age = abs(today - earliest).days

    lifetime = Statistic.objects.filter(interval='MN', author=author)

    ret = lifetime.aggregate(lines_added=Sum("lines_added"), lines_removed=Sum("lines_removed"))

    ret['commits'] = intcomma(commits.count())
    ret['lines_added'] = intcomma(ret['lines_added'])
    ret['lines_removed'] = intcomma(ret['lines_removed'])
    ret['age'] = intcomma(age)
    ret['repo_count'] = author.repos.count()
    ret['avg_commits_day'] = intcomma(round(commits.count() / age, 4))

    return ret


#Calculate the lifetime statistics of a repository
def get_lifetime_stats(repo):
    #Summary Statistics
    earliest_commit = repo.earliest_commit
    today = datetime.now(tz=timezone.utc)

    start_range = Rollup.get_first_day(earliest_commit, ('MN', "Month"))

    lifetime = Statistic.objects.filter(interval='MN', repo=repo,
                                        author=None, file=None,
                                        start_date__range=(start_range, today))


    summary_stats = lifetime.aggregate(commits=Sum("commit_total"), authors=Sum("author_total"),
                                       lines_added=Sum("lines_added"), lines_removed=Sum("lines_removed"),
                                       lines_changed=Sum("lines_changed"))

    #number of files
    file_count = File.objects.filter(repo=repo).count()
    summary_stats['file_count'] = file_count

    #Age of repository
    age = abs(today - earliest_commit).days
    summary_stats['age'] = age

    #Average commits per day
    avg_commits_day = "%0.2f" % (summary_stats['commits']/age)
    summary_stats['avg_commits_day'] = avg_commits_day

    summary_stats['commits'] = intcomma(summary_stats['commits'])
    summary_stats['authors'] = intcomma(summary_stats['authors'])
    summary_stats['lines_added'] = intcomma(summary_stats['lines_added'])
    summary_stats['lines_removed'] = intcomma(summary_stats['lines_removed'])
    summary_stats['file_count'] = intcomma(summary_stats['file_count'])
    summary_stats['avg_commits_day'] = intcomma(summary_stats['avg_commits_day'])

    return summary_stats


"""
Returns an array of the top 6 contributing authors
"""
def get_top_authors(**kwargs):
    # Get every author with displayed repo; limit 5
    authors = []
    #First get all daily interval author stats within the range
    filter_set = Statistic.objects.filter(
        interval='DY',
        author__isnull=False,
        repo=kwargs['repo'],
        start_date__range=(kwargs['start'], kwargs['end'])
    )

    #Then aggregate the filter set based on the attribute, get top 5
    top_set = filter_set.annotate(total_attr=Sum(kwargs['attribute'])).order_by('-total_attr')

    #append top 5 authors to author set to display
    i = 0
    for t in top_set:
        if t.author not in authors and i < 6:
            authors.append(t.author)
            i += 1

    return authors

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

    date_index = date_index.replace(hour=23, minute=59, second=59, microsecond=99)
    return date_index
