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

# dataframes.py - code behind getting meaningful pandas dataframes (largely for graphing) from Statistic model querysets

import pandas as pd
from django.db.models import Sum

from ..models import Statistic


def get_interval(start, end):
    """
    Attempts to decide on a good granularity for a graph when it is not provided.
    This is mostly a vestige and can probably be removed.
    """
    delta = end-start
    if delta.days > 365:
        return 'WK'
    else:
        return 'DY'

def top_authors(repo, start, end, attribute='commit_total', limit=10):

    """
    Return the top N authors for a repo based on a specified attribute.
    FIXME: this isn't currently used because we show the full list.  This will change
    if we show a truncated list on the repo graph page.
    """

    interval = get_interval(start, end)

    # authors = []
    filter_set = Statistic.objects.filter(
        interval=interval,
        author__isnull=False,
        repo=repo,
        start_date__range=(start, end)
    ).values('author_id').annotate(total=Sum(attribute)).order_by('-total')[0:limit]

    author_ids = [ t['author_id'] for t in filter_set ]
    return author_ids


def _interval_queryset(repo, start=None, end=None, by_author=False, interval='DY', limit_top_authors=False):

    """
    Returns a queryset of statistics usable for a scatter plot.
    FIXME: this is only slightly different from the methods in models.py, because it doesn't yet use the top_authors data. Add the option
    with a limit=-1 (default) parameter.
    # FIXME: clean all this up.
    """

    totals = None
    if not by_author:
        if interval != 'LF':
            totals = Statistic.objects.select_related('repo', ).filter(
                interval=interval,
                repo=repo,
                author__isnull=True,
                start_date__range=(start, end)
            )
        else:
            if start is None or end is None:
                totals = Statistic.objects.select_related('repo').filter(
                    interval=interval,
                    repo=repo,
                    author__isnull=True
                )
            else:
                totals = Statistic.objects.select_related('repo').filter(
                    interval=interval,
                    repo=repo,
                )
    else:
        top = None
        if limit_top_authors:
            top = top_authors(repo, start, end)
        if interval != 'LF':
            if limit_top_authors:
                totals = Statistic.objects.select_related('repo', 'author').filter(
                    interval=interval,
                    repo=repo,
                    author__pk__in=top,
                    start_date__range=(start, end)
                )
            else:
                totals = Statistic.objects.select_related('repo', 'author').filter(
                    interval=interval,
                    repo=repo,
                    author__isnull=False,
                    start_date__range=(start, end)
                )
        else:
            totals = Statistic.objects.select_related('repo', 'author').filter(
                interval=interval,
                repo=repo,
                author__isnull=False
            )
            if start and end:
                totals = totals.filter(author__commits__commit_date__range=(start,end))
            if limit_top_authors:
                totals = totals.filter(author__pk__in=top)

    return totals.order_by('author','start_date')

def _interval_queryset_to_dataframe(repo, totals, fields, just_data=False):

    """
    Convert a queryset of statistic objects as returned by the above function
    to a Pandas dataframe which we can graph.  This ALMOST relies on the statistic
    objects being 100% correct in the database, but we also add a denormalized
    'days' stat, because Altair cannot do polynomial regressions (i.e. curve fitting graphs)
    against raw datetime objects.  'days' is the days since the project started.
    """

    data = dict()

    first_day = repo.earliest_commit_date()

    for f in fields:
        data[f] = []

    for t in totals:

        for f in fields:
            if f == 'date':
                # just renaming this one field for purposes of axes labelling
                data[f].append(t.start_date)
            elif f == 'day':
                if t.start_date is not None:
                    # if condition because lifetime stats have no dates
                    data[f].append((t.start_date - first_day).days)
                else:
                    data[f].append(0)
            elif f == 'earliest_commit_day':
                if t.earliest_commit_date is not None:
                    data[f].append((t.earliest_commit_date - first_day).days)
                else:
                    data[f] = -1
            elif f == 'latest_commit_day':
                if t.latest_commit_date is not None:
                    data[f].append((t.latest_commit_date - first_day).days)
                else:
                    data[f] = -1
            elif f == 'author':
                data[f].append(t.author.email)
            else:
                data[f].append(getattr(t, f))
    if not just_data:
        return pd.DataFrame(data, columns=fields)
    else:
        return (data, fields)

def _stat_series(repo, start=None, end=None, fields=None, by_author=False, interval=None, limit_top_authors=False):

    """
    The public function in this file (FIXME: convert the rest to _functions) that returns
    an appropriate dataframe of statistics for the input criteria.  There are more fields
    returned for lifetime statistics since many of the lifetime stats don't make sense
    when used with a daterange. (ex: longevity).
    """

    if not interval:
        interval = get_interval(start, end)

    if fields is None:
        fields = Statistic.GRAPHABLE_FIELDS[:]
        if by_author:
            fields.append('author')

    totals = _interval_queryset(repo, start=start, end=end, by_author=by_author, interval=interval, limit_top_authors=limit_top_authors)
    return _interval_queryset_to_dataframe(repo, totals, fields)

def team_time_series(repo, start=None, end=None, interval=None):
    return _stat_series(repo, start=start, end=end, interval=interval)

def author_time_series(repo, start=None, end=None, interval=None):
    return _stat_series(repo, start=start, end=end, interval=interval, by_author=True)

def top_author_time_series(repo, start=None, end=None, interval=None):
    return _stat_series(repo, start=start, end=end, interval=interval, by_author=True, limit_top_authors=True)

# TODO: make a method that returns the top_author_time_series but makes an 11th author which is the aggregrate of all authors not in
# the top author list.  We will then use *THAT* data for pie charts and stacked bars.
