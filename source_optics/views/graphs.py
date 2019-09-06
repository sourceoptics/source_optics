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

AUTHOR_TIME_SERIES_TOOLTIPS = ['day','author','commit_total', 'lines_changed', 'files_changed', 'days_active', 'longevity', 'days_since_seen' ]

TIME_SERIES_TOOLTIPS = ['day','commit_total', 'lines_changed', 'files_changed', 'author_total' ]

import json
import random
import string

import altair as alt
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


def time_area_plot(df=None, y=None, color=None, author=False):
    """
    Generates a time series area plot.
    :param df: a pandas dataframe
    :param y: the name of the y axis from the dataframe
    :param color: a bit of a misnomer, this is what attribute to use for the legend
    :param author: true if the chart is going to be showing authors vs the whole team together
    :return: chart HTML
    """

    tooltips = TIME_SERIES_TOOLTIPS
    if author:
        tooltips = AUTHOR_TIME_SERIES_TOOLTIPS

    alt.data_transformers.disable_max_rows()

    if color:
        chart = alt.Chart(df, height=600, width=600).mark_area().encode(
            x=alt.X('date:T', axis = alt.Axis(title = 'date', format = ("%b %Y")), scale=alt.Scale(zero=False, clamp=True)),
            y=alt.Y(y, scale=alt.Scale(zero=False, clamp=True)),
            color=color,
            tooltip=tooltips
        ).interactive()
    else:
        chart = alt.Chart(df, height=600, width=600).mark_area().encode(
            x=alt.X('date:T', axis = alt.Axis(title = 'date', format = ("%b %Y")), scale=alt.Scale(zero=False, clamp=True)),
            y=alt.Y(y, scale=alt.Scale(zero=False, clamp=True)),
            tooltip=tooltips
        ).interactive()

    return render_chart(chart)
