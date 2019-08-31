
import altair as alt
import pandas as pd
import numpy as np


# https://github.com/Jesse-jApps/django-altair/blob/master/django_altair/templatetags/django_altair.py

from django import template
import random, string, json

register = template.Library()

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
    spec = chart.to_dict()
    output_div = '_' + ''.join(random.choices(string.ascii_letters + string.digits, k=7))
    embed_opt = {"mode": "vega-lite", "actions": False}
    c = template.Context()
    return template.Template(TEMPLATE_CHART.format(output_div=output_div, spec=json.dumps(spec), embed_opt=json.dumps(embed_opt))).render(c)

def _basic_graph(repo=None, start=None, end=None, df=None, x=None, y=None, tooltips=None):

    if tooltips is None:
        tooltips=['date', 'commit_total', 'lines_changed', 'author_total']

    alt.data_transformers.disable_max_rows()
    chart = alt.Chart(df, height=600, width=600).mark_point().encode(
        x=alt.X(x, scale=alt.Scale(zero=False, clamp=True)),
        y=alt.Y(y, scale=alt.Scale(zero=False, clamp=True)),
        tooltip=tooltips,
    ).interactive()

    # Plot the best fit polynomials
    # degree_list = [1, 3, 5]

    # Build a dataframe with the fitted data
    #poly_data = pd.DataFrame({'xfit': np.linspace(df['lines_changed'].min(), df['lines_changed'].max(), 500)})
    #print("PD=%s" % poly_data)

    #polynomial_fit = alt.Chart(poly_data).transform_fold(
    #    ['1', '3', '5'],
    #    as_=['degree', 'yfit']
    #).mark_line().encode(
    #    x='xfit:Q',
    #    y='yfit:Q',
    #    color='degree:N'
    #)

    #chart = chart + polynomial_fit

    return render_chart(chart)

def volume(repo=None, start=None, end=None, df=None):
    return _basic_graph(repo=repo, start=start, end=end, df=df, x='date', y='lines_changed')

def frequency(repo=None, start=None, end=None, df=None):
    return _basic_graph(repo=repo, start=start, end=end, df=df, x='date', y='commit_total')

def participation(repo=None, start=None, end=None, df=None):
    return _basic_graph(repo=repo, start=start, end=end, df=df, x='date', y='author_total')

def granularity(repo=None, start=None, end=None, df=None):
    return _basic_graph(repo=repo, start=start, end=end, df=df, x='date', y='average_commit_size')

def key_retention(repo=None, start=None, end=None, df=None):
    return _basic_graph(repo=repo, start=start, end=end, df=df, x='latest_commit_date', y='lines_changed',
                        tooltips=['author', 'earliest_commit_date', 'latest_commit_date', 'commit_total', 'lines_changed'])

def early_retention(repo=None, start=None, end=None, df=None):
    return _basic_graph(repo=repo, start=start, end=end, df=df, x='earliest_commit_date', y='days_since_seen',
                        tooltips=['author', 'earliest_commit_date', 'latest_commit_date', 'commit_total', 'lines_changed'])


def largest_contributors(repo=None, start=None, end=None, df=None):
    alt.data_transformers.disable_max_rows()
    chart = alt.Chart(df, height=600, width=600).mark_point().encode(
        x=alt.X('date', scale=alt.Scale(zero=False, clamp=True)),
        y=alt.Y("lines_changed", scale=alt.Scale(zero=False, clamp=True)), #  domain=(0,2000), clamp=True)),
        color='author:N',
        # size='commit_count:N',
        tooltip = ['date', 'commit_total', 'lines_changed', 'author' ],
    ).interactive()
    return render_chart(chart)

OLD = """


def health_matrix(repo=None, start=None, end=None, df=None):
    rows = ['days_before_joined', 'days_since_seen', 'lines_changed', 'commits', 'average_commit_size' ]
    cols = ['days_before_joined', 'days_since_seen', 'lines_changed', 'commits', 'average_commit_size' ]
    tooltips = ('author', 'commits', 'lines_changed', 'average_commit_size', 'days_before_joined', 'days_since_seen')

    chart = alt.Chart(df).mark_circle().encode(
        alt.X(alt.repeat("column"), type='quantitative'),
        alt.Y(alt.repeat("row"), type='quantitative'),
        #color='author:N'
        tooltip = tooltips
    ).properties(
        width=150,
        height=150
    ).repeat(
        row=rows,
        column=cols
    ).interactive()

    return render_chart(chart)

"""