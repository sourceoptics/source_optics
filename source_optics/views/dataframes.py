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
import django.utils.timezone as timezone
import dateutil.rrule as rrule
import datetime
from ..models import Statistic, Author
import pandas

TZ = timezone.get_current_timezone()


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

    return [ x for x in Author.objects.filter(pk__in= [ t['author_id'] for t in filter_set ]).all() ]

def _interval_queryset(repo, start=None, end=None, by_author=False, interval='DY', limit_top_authors=False):

    """
    Returns a queryset of statistics usable for a scatter plot.
    FIXME: this is only slightly different from the methods in models.py, because it doesn't yet use the top_authors data. Add the option
    with a limit=-1 (default) parameter.
    # FIXME: clean all this up.
    """
    limited_to = None

    totals = None
    if not by_author:
        if interval != 'LF':
            print("n1")
            totals = Statistic.objects.select_related('repo', ).filter(
                interval=interval,
                repo=repo,
                author__isnull=True,
                start_date__range=(start, end)
            )
        else:
            print("n2")
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
                    author__isnull=True
                )
    else:
        top = None
        if limit_top_authors:
            limited_to = top_authors(repo, start, end)
        if interval != 'LF':
            assert start is not None
            assert end is not None
            print(start,end)
            print(top)
            if limit_top_authors:
                print("n3")
                totals = Statistic.objects.select_related('repo', 'author').filter(
                    interval=interval,
                    repo=repo,
                    author__in=limited_to,
                    start_date__range=(start, end)
                )
            else:
                print("n4")
                totals = Statistic.objects.select_related('repo', 'author').filter(
                    interval=interval,
                    repo=repo,
                    author__isnull=False,
                    start_date__range=(start, end)
                )
        else:
            print("n5")
            totals = Statistic.objects.select_related('repo', 'author').filter(
                interval=interval,
                repo=repo,
                author__isnull=False
            )
            if start and end:
                totals = totals.filter(author__commits__commit_date__range=(start,end))
            if limit_top_authors:
                totals = totals.filter(author__pk__in=limited_to)

    return (totals.order_by('author','start_date'), limited_to)

def _field_prep(field, stat, first_day):
    if field == 'date':
        return stat.start_date
    elif field == 'author':
        return stat.author.email
    else:
        return getattr(stat, field)

def _interval_queryset_to_dataframe(repo, totals, fields, start, end, interval, limited_to):


    data = dict()

    first_day = repo.earliest_commit_date()

    for f in fields:
        data[f] = []

    # load the dataframe with the queryset results we have
    for t in totals:
        for f in fields:
            data[f].append(_field_prep(f, t, first_day))

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

    print("INF=%s" % fields)

    (totals, limited_to_authors) = _interval_queryset(repo, start=start, end=end, by_author=by_author, interval=interval, limit_top_authors=limit_top_authors)
    (pre_df, fields) = _interval_queryset_to_dataframe(repo, totals, fields, start, end, interval, limited_to_authors)
    return pandas.DataFrame(pre_df, columns=fields)

def team_time_series(repo, start=None, end=None, interval=None):
    return _stat_series(repo, start=start, end=end, interval=interval, by_author=False)

def author_time_series(repo, start=None, end=None, interval=None):
    return _stat_series(repo, start=start, end=end, interval=interval, by_author=True)

def top_author_time_series(repo, start=None, end=None, interval=None):
    return _stat_series(repo, start=start, end=end, interval=interval, by_author=True, limit_top_authors=True)

