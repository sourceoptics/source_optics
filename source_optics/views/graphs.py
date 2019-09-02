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

import json
import random
import string

import altair as alt
import numpy as np
import pandas as pd
from django import template

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

def _basic_graph(repo=None, start=None, end=None, df=None, x=None, y=None, tooltips=None, fit=False):
    """
    This renders an altair graph around pretty much any combination of two parameters found on a Statistic object.
    """

    if tooltips is None:
        tooltips=['day', 'date', 'commit_total', 'lines_changed', 'author_total']

    if fit and x=='date':
        x='day'


    alt.data_transformers.disable_max_rows()
    chart = alt.Chart(df, height=600, width=600).mark_point().encode(
        x=alt.X(x, scale=alt.Scale(zero=False, clamp=True)), #, scale=alt.Scale(zero=False, clamp=True)),
        y=alt.Y(y, scale=alt.Scale(zero=False, clamp=True)), #, scale=alt.Scale(zero=False, clamp=True)),
        tooltip=tooltips,
    ).interactive()


    if fit and len(df.index) > 0:
        # only show the curve if it is turned on and there is data to apply the curve to.

        # Build a dataframe with the fitted data
        poly_data = pd.DataFrame({'xfit': np.linspace(df[x].min(), df[x].max(), 500)})
        for degree in [1,3,5]:
            poly_data[str(degree)] = np.poly1d(np.polyfit(df[x], df[y], degree))(poly_data['xfit'])

        polynomial_fit = alt.Chart(poly_data).transform_fold(
            ['1', '3', '5'],
            as_=['degree', 'yfit']
        ).mark_line().encode(
            x='xfit:Q',
            y='yfit:Q',
            color='degree:N'
        )

        chart = chart + polynomial_fit

    return render_chart(chart)

def volume(repo=None, start=None, end=None, df=None):
    """ graphs the number of days since the project started VS the lines changed each day """
    return _basic_graph(repo=repo, start=start, end=end, df=df, x='day', y='lines_changed', fit=True)

def frequency(repo=None, start=None, end=None, df=None):
    """ graphs the number of days since the project started since the number of commits each day """
    return _basic_graph(repo=repo, start=start, end=end, df=df, x='day', y='commit_total', fit=True)

def participation(repo=None, start=None, end=None, df=None):
    """ graphs the number of days since the project started since the number of authors that committed each day """
    return _basic_graph(repo=repo, start=start, end=end, df=df, x='day', y='author_total', fit=True)

def granularity(repo=None, start=None, end=None, df=None):
    """ shows the average commit size for a particular day """
    return _basic_graph(repo=repo, start=start, end=end, df=df, x='day', y='average_commit_size', fit=True)

# FIXME: standardize all the tooltips so they are the same for lifetime graphs, and a different set for non-lifetime graphs

def key_retention(repo=None, start=None, end=None, df=None):
    """
    graphs the number of days since we have seen a commit from a user against their line contribution to the project.
    this can be used to identify contributors that may have lost interest or changed jobs/assignments.
    """
    # FIXME: earliest_commit_date should be 0-based (earliest_commit_day) from project start so we can apply fit
    return _basic_graph(repo=repo, start=start, end=end, df=df, x='days_since_seen', y='lines_changed',
                        tooltips=['author', 'earliest_commit_date', 'latest_commit_date', 'longevity', 'commit_total', 'lines_changed'], fit=True)

def early_retention(repo=None, start=None, end=None, df=None):
    """
    graphs the number of days since project inception before the user offered a commit vs the span of days encompassing user history with
    the project.  This can be used to tell, over time, whether the project is keeping contributors around better or worse, essentially
    tracking the rate of change of turnover.
    """
    # FIXME: earliest_commit_date should be 0-based (earliest_commit_day) from project start so we can apply fit
    # FIXME: terminology between 'first' and 'earliest' and 'last' and 'latest' is redundant/confusing and should be standardized
    return _basic_graph(repo=repo, start=start, end=end, df=df, x='days_before_joined', y='longevity',
                        tooltips=['author', 'earliest_commit_date', 'latest_commit_date', 'longevity', 'commit_total', 'lines_changed'], fit=True)

def staying_power(repo=None, start=None, end=None, df=None):
    """
    graphs longevity (as above) against the number of days a user has contributed to a project.  This graph is not time based, but attempts
    to determine whether there is a relationship between how long a user has been around versus how active they are.  Do contributors with a lot
    of history commit more than ones who have been around less frequently?  True understanding really warrants a 3D graph vs days_since_joined.
    """
    return _basic_graph(repo=repo, start=start, end=end, df=df, x='longevity', y='days_active',
                        #x='longevity', y='lines_changed',
                        tooltips=['author', 'earliest_commit_date', 'latest_commit_date', 'longevity', 'commit_total', 'lines_changed'], fit=True)


def largest_contributors(repo=None, start=None, end=None, df=None):
    """
    this is a scatter plot of the activity of the top authors within the time range.  Selecting a different time range may highlight a different set
    of authors that were at the top within that particular range, rather than the overall top authors for the lifetime of the project.
    """
    alt.data_transformers.disable_max_rows()
    chart = alt.Chart(df, height=600, width=600).mark_point().encode(
        x=alt.X('day', scale=alt.Scale(zero=False, clamp=True)),
        y=alt.Y("lines_changed", scale=alt.Scale(zero=False, clamp=True)), #  domain=(0,2000), clamp=True)),
        color='author:N',
        tooltip = ['day', 'date', 'commit_total', 'lines_changed', 'author' ],
    ).interactive()
    return render_chart(chart)
