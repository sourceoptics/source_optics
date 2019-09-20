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
# graphs.py - generate altair graphs as HTML snippets given panda dataframe inputs (see dataframes.py)

import functools
from .. models import Statistic
from django.db.models import Sum
from django.conf import settings
from . import dataframes

AUTHOR_TIME_SERIES_TOOLTIPS = ['day','author','commit_total', 'lines_changed', 'files_changed', 'longevity', 'days_since_seen' ]

TIME_SERIES_TOOLTIPS = ['day','commit_total', 'lines_changed', 'files_changed', 'author_total' ]

import json
import random
import string

import altair as alt
from django import template

GRAPH_CLAMPING_FACTOR = getattr(settings, 'GRAPH_CLAMPING_FACTOR', 5)

# template used by render_chart below
TEMPLATE_CHART = """
<div id="{output_div}"></div>
    <script type="text/javascript">
    var spec = {spec};
    var embed_opt = {embed_opt};
    function showError({output_div}, error){{
        {output_div}.innerHTML = ('<div class="error">'
                        + '<p>JavaScript Error: ' + error.message + '</p>'
                        + "<p>This usually means there's a typo in your chart specification. "
                        + "See the javascript console for the full traceback.</p>"
                        + '</div>');
        throw error;
    }}
    const {output_div} = document.getElementById('{output_div}');
    vegaEmbed("#{output_div}", spec, embed_opt)
      .catch(error => showError({output_div}, error));
    </script>
"""

def render_chart(chart):
    """
    wraps an altair chart with the required javascript/html to display that chart
    """
    spec = chart.to_dict()
    output_div = '_' + ''.join(random.choices(string.ascii_letters + string.digits, k=7))
    embed_opt = {"mode": "vega-lite", "actions": False}
    c = template.Context()
    return template.Template(TEMPLATE_CHART.format(output_div=output_div, spec=json.dumps(spec), embed_opt=json.dumps(embed_opt))).render(c)

@functools.lru_cache(maxsize=64)
def get_stat(repo, author, start, end, aspect):
   value = Statistic.objects.filter(
       author=author,
       repo=repo,
       interval='DY',
       start_date__range=(start,end)
   ).aggregate(
       lines_changed=Sum('lines_changed'),
       commit_total=Sum('commit_total')
   )[aspect]
   if value is None:
       return -10000
   return value

def time_plot(scope=None, df=None, repo=None, y=None, by_author=False, top=None, aspect=None):
    """
    Generates a time series area plot.
    :param df: a pandas dataframe
    :param y: the name of the y axis from the dataframe
    :param top: the legend, used for the top authors plot sorting, as a list of authors
    :param aspect: the aspect the chart was limited by
    :param author: true if the chart is going to be showing authors vs the whole team together
    :return: chart HTML
    """
    assert df is not None
    assert scope is not None
    start = scope.start
    end = scope.end
    repo = scope.repo

    if top:
        assert start is not None
        assert end is not None
        assert repo is not None
        # sort top authors by the statistic we filtered them by
        top = reversed(sorted(top, key=lambda x: get_stat(repo, x, start, end, aspect)))
        top = [ x.email for x in top ]
        top.append('OTHER')

    tooltips = TIME_SERIES_TOOLTIPS
    if by_author:
        tooltips = AUTHOR_TIME_SERIES_TOOLTIPS

    alt.data_transformers.disable_max_rows()
    domain = dataframes.get_clamped_domain(df, y)

    if by_author:
        chart = alt.Chart(df, height=600, width=600).mark_area().encode(
            x=alt.X('date:T', axis = alt.Axis(title = 'date', format = ("%b %Y")), scale=alt.Scale(zero=False, clamp=True)),
            y=alt.Y(y, scale=alt.Scale(zero=True, domain=domain, clamp=True)),
            color=alt.Color('author', sort=top),
            tooltip=tooltips
        ).interactive()
    elif not scope.multiple_repos_selected():
        chart = alt.Chart(df, height=600, width=600).mark_line().encode(
            x=alt.X('date:T', axis = alt.Axis(title = 'date', format = ("%b %Y")), scale=alt.Scale(zero=False, clamp=True)),
            y=alt.Y(y, scale=alt.Scale(zero=True, domain=domain, clamp=True)),
            tooltip=tooltips
        ).interactive()
    else:
        # multiple repos
        chart = alt.Chart(df, height=600, width=600).mark_line().encode(
            x=alt.X('date:T', axis = alt.Axis(title = 'date', format = ("%b %Y")), scale=alt.Scale(zero=False, clamp=True)),
            y=alt.Y(y, scale=alt.Scale(zero=True, domain=domain, clamp=True)),
            color=alt.Color('repo'),
            tooltip=tooltips
        ).interactive()

    return render_chart(chart)
