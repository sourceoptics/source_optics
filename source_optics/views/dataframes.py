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

from django.db.models import Sum
import django.utils.timezone as timezone
from ..models import Statistic, Author
import pandas

# fields valid for axes or tooltips in time series graphs
TIME_SERIES_FIELDS = [
    'day',
    'date',
    'lines_changed',
    'commit_total',
    'author_total',
    'average_commit_size',
    'files_changed',
    'days_since_seen',
    'days_before_joined',
    'longevity',
    'days_active',
    'creates',
    'edits',
    'moves',
    'repo'
]

TZ = timezone.get_current_timezone()

def get_interval(scope, start, end):
    """
    Attempts to decide on a good granularity for a graph when it is not provided.
    This is mostly a vestige and can probably be removed.
    """
    if scope.interval:
        return scope.interval
    delta = end-start
    if delta.days > 365:
        return 'WK'
    else:
        return 'DY'

def top_authors(scope, aspect='commit_total', limit=9):

    """
    Return the top N authors for a repo based on a specified attribute.
    """

    repo = scope.repo
    start = scope.start
    end = scope.end

    interval = get_interval(scope, start, end)

    filter_set = Statistic.objects.filter(
        interval=interval,
        author__isnull=False,
        repo=repo,
        start_date__range=(start, end)
    ).values('author_id').annotate(total=Sum(aspect)).order_by('-total')[0:limit]

    result = [ x for x in Author.objects.filter(pk__in= [ t['author_id'] for t in filter_set ]).all() ]
    return result

def _interval_queryset(scope, by_author=False, aspect=None, limit_top_authors=False):


    """
    Returns a queryset of statistics usable for a scatter plot.
    FIXME: this is only slightly different from the methods in models.py, because it doesn't yet use the top_authors data. Add the option
    with a limit=-1 (default) parameter.
    # FIXME: clean all this up.
    """

    repo = scope.repo
    start = scope.start
    end = scope.end
    interval = scope.interval

    limited_to = None
    inverse = None

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
                    author__isnull=True
                )
    else:
        if limit_top_authors:
            limited_to = top_authors(scope, aspect=aspect)
        if interval != 'LF':
            assert start is not None
            assert end is not None

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
                # we can still trim the lifetime stats by excluding authors
                totals = totals.filter(author__commits__commit_date__range=(start,end))
        if limit_top_authors:
            filtered = totals.filter(author__in=limited_to).select_related('author')
            inverse = totals.exclude(author__in=limited_to).select_related('author')
            return (filtered, limited_to, inverse)

    return (totals.order_by('author','start_date').select_related('author'), None, None)


def _interval_queryset_to_dataframe(repo, totals=None, fields=None, inverse=None):
    """
    :param repo: repository object
    :param totals: a statistics queryset
    :param fields: fields to include in the dataframe
    :param start: beginning of the date range
    :param end: end of the date range
    :param interval: DY, WK, MN
    :param limited_to: a set of authors that are in the primary dataset
    :param inverse: if provided, an aggregrate of authors not in the primary dataset
    :return: (datastructure for dataframe, list of fields used)
    """

    data = dict()

    for f in fields:
        data[f] = []

    # load the dataframe with the queryset results we have
    for t in totals:
        for f in fields:
            if f == 'repo':
                data[f].append(repo.name)
            elif f in [ 'date', 'day' ]:
                data[f].append(str(t.start_date))
            elif f == 'author':
                data[f].append(t.author.email)
            else:
                data[f].append(getattr(t,f))

    if inverse:

        # FIXME: this should use a method in the Statistic class
        inverse = inverse.values('start_date').annotate(
            lines_changed=Sum('lines_changed'),
            lines_added=Sum('lines_added'),
            lines_removed=Sum('lines_removed'),
            commit_total=Sum('commit_total'),
            author_total=Sum('author_total'),
            files_changed=Sum('files_changed'),
            creates=Sum('creates'),
            edits=Sum('edits'),
            moves=Sum('moves')
        )

        for x in inverse.all():
            for f in fields:
                if f == 'repo':
                    data[f].append(repo.name)
                elif f == 'date' or f == 'day':
                    data[f].append(str(x['start_date']))
                elif f in [ 'days_active', 'days_since_seen', 'longevity', 'days_active', 'average_commit_size', 'days_before_joined' ]:
                    # these aren't available in the aggregate, but we need a placeholder
                    data[f].append(-1)
                elif f == 'author':
                    data[f].append('OTHER')
                else:
                    data[f].append(x[f])

    return (data, fields)

def _stat_series(scope, by_author=False, interval=None, limit_top_authors=False, aspect=None):

    """
    returns an appropriate dataframe of statistics for the input criteria.
    """

    start = scope.start
    end = scope.end


    if not interval:
        interval = get_interval(scope, start, end)

    fields = TIME_SERIES_FIELDS[:]
    if by_author:
        fields.append('author')

    # holds the data before we save a dataframe

    df_data = dict()
    limited_to_authors = None

    if scope.multiple_repos_selected():

        # getting dataframes for multiple repos - this form does NOT (yet?) support filtering by a single author
        # and currently works by executing one set of queries per repo

        for repo in scope.repos:

            scope.repo = repo
            (totals, limited_to_authors, inverse) = _interval_queryset(scope, by_author=by_author, aspect=aspect, limit_top_authors=limit_top_authors)

            (pre_df, fields) = _interval_queryset_to_dataframe(repo, totals=totals, fields=fields, inverse=inverse)
            for f in fields:
                if not f in df_data:
                    df_data[f] = []
                df_data[f].extend(pre_df[f])

    else:
        # getting data for a single repo - this form supports optional filtering by author

        (totals, limited_to_authors, inverse) = _interval_queryset(scope, by_author=by_author, aspect=aspect,
                                                                   limit_top_authors=limit_top_authors)

        (df_data, fields) = _interval_queryset_to_dataframe(scope.repo, totals=totals, fields=fields, inverse=inverse)



    df = pandas.DataFrame(df_data, columns=fields)
    return (df, limited_to_authors)

def team_time_series(scope):
    (df, _) = _stat_series(scope, by_author=False)
    return (df, None)

def author_time_series(scope):
    (df, _) = _stat_series(scope, by_author=True)
    return (df, None)


def top_author_time_series(scope, aspect=None):
    (df, top) = _stat_series(scope, by_author=True, aspect=aspect, limit_top_authors=True)
    return (df, top)

