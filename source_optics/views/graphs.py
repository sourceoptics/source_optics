
import altair as alt

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

@register.simple_tag(name='render_chart')
def render_chart(chart):
    spec = chart.to_dict()
    output_div = '_' + ''.join(random.choices(string.ascii_letters + string.digits, k=7))
    embed_opt = {"mode": "vega-lite", "actions": False}
    c = template.Context()
    return template.Template(TEMPLATE_CHART.format(output_div=output_div, spec=json.dumps(spec), embed_opt=json.dumps(embed_opt))).render(c)


def author_series(repo=None, start=None, end=None, df=None):
    alt.data_transformers.disable_max_rows()
    chart = alt.Chart(df).mark_point().encode(
        x=alt.X('date', scale=alt.Scale(zero=False)),
        y=alt.Y("lines_changed", scale=alt.Scale(zero=False, domain=(0,2000), clamp=True)),
        color='author:N',
        # size='commit_count:N',
        tooltip = ['date', 'author', 'commits', 'lines_changed' ],
    ).interactive()
    return render_chart(chart)

