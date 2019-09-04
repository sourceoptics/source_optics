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

def add_fit(df, x, y, chart):
    if len(df.index) <= 0:
        return chart
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
    return chart + polynomial_fit

def scatter_plot(df=None, x=None, y=None, color=None, author=False, fit=False):
    """
    This renders an altair graph around pretty much any combination of two parameters found on a Statistic object.
    """

    tooltips=['date', 'commit_total', 'lines_changed', 'author_total']
    if author:
        tooltips.extend(['author'])
    # FIXME: we should pass in the interval, and add longevity/etc when interval==LF.

    if fit and x=='date':
        x='day'


    alt.data_transformers.disable_max_rows()

    if color:
        chart = alt.Chart(df, height=600, width=600).mark_point().encode(
            x=alt.X(x, scale=alt.Scale(zero=False, clamp=True)), #, scale=alt.Scale(zero=False, clamp=True)),
            y=alt.Y(y, scale=alt.Scale(zero=False, clamp=True)), #, scale=alt.Scale(zero=False, clamp=True)),
            color=color
        ).interactive()
    else:
        chart = alt.Chart(df, height=600, width=600).mark_point().encode(
            x=alt.X(x, scale=alt.Scale(zero=False, clamp=True)),  # , scale=alt.Scale(zero=False, clamp=True)),
            y=alt.Y(y, scale=alt.Scale(zero=False, clamp=True)),  # , scale=alt.Scale(zero=False, clamp=True)),
        ).interactive()

    if fit:
        chart = add_fit(df, x, y, chart)

    return render_chart(chart)
