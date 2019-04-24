import django_tables2 as tables
from ..models import Statistic, Repository
from django.contrib.humanize.templatetags.humanize import intcomma
from django_tables2.utils import A
from django.db.models import F


class ColumnNumber(tables.Column):
    def render(self,value):
        return intcomma(value)

class StatTable(tables.Table):
    author_total = ColumnNumber(verbose_name='Author Total', attrs={"th": {"class": "num"}})
    commit_total = ColumnNumber(verbose_name='Commit Total', attrs={"th": {"class": "num"}})
    files_changed = ColumnNumber(verbose_name='Files Changed', attrs={"th": {"class": "num"}})
    repo_tags = tables.TemplateColumn(
        """
        <ul class='tags'>
            {% load query_tags %}
            {%for tag in record.repo_tags%}
            <li><a href="{% query_url request.GET.items 'filter' tag %}" {%ifequal request.GET.filter tag|stringformat:'s'%}class='active'{%endifequal%}>{{ tag }}</a></li>
            {%endfor%}
        </ul>

        """, verbose_name='Tags', attrs={"td": {"class": "no-padding"}})
    repo_last_pulled = tables.DateTimeColumn(verbose_name='Last Pulled', format='m\/d\/y P')
    repo_last_scanned = tables.DateTimeColumn(verbose_name='Last Scanned', format='m\/d\/y P')
    lines_added = ColumnNumber(verbose_name='Lines Added', attrs={"th": {"class": "lines"}})
    lines_removed = ColumnNumber(verbose_name='Lines Removed', attrs={"th": {"class": "lines"}})
    repo = tables.TemplateColumn('<a href="/repos/{{ record.repo }}/?{{ request.GET.urlencode }}">{{ record.repo }}</a>', accessor='repo.name', attrs={"td": {"class": "repo"}})

    class Meta:
        attrs = {'class': 'metrics'}
        model = Statistic
        exclude = (
            'author',
            'lines_changed',
            'repo_last_pulled',
            'id',
            'file',
            'interval',
            'start_date'
        )
        sequence = ('repo', 'repo_tags', 'repo_last_scanned', 'repo_last_pulled', 'commit_total', 'author_total', '...' )
        template_name = 'table.html'

    # def render_repo(self, record):
    #     return str(record.repo)
    # def order_repo(self, QuerySet, is_descending):
    #     QuerySet = QuerySet.annotate(
    #         repo=F('repo')
    #     ).order_by(('-' if is_descending else '') + 'repo')
    #     return (QuerySet, True)

class AuthorStatTable(tables.Table):
    author_total = ColumnNumber(verbose_name='Author Total', attrs={"th": {"class": "num"}})
    commit_total = ColumnNumber(verbose_name='Commit Total', attrs={"th": {"class": "num"}})
    files_changed = ColumnNumber(verbose_name='Files Changed', attrs={"th": {"class": "num"}})
    lines_added = ColumnNumber(verbose_name='Lines Added', attrs={"th": {"class": "lines"}})
    lines_removed = ColumnNumber(verbose_name='Lines Removed', attrs={"th": {"class": "lines"}})
    author = tables.TemplateColumn('<a href="/author/{{ record.author }}/?{{ request.GET.urlencode }}">{{ record.author }}</a>', 
        accessor='author.email', attrs={"td": {"class": "repo"}})
    
    class Meta:
        attrs = {'class': 'metrics'}
        model = Statistic
        exclude = (
            'lines_changed',
            'repo_last_pulled',
            'repo',
            'repo_last_scanned',
            'id',
            'file',
            'author_total',
            'interval',
            'start_date'
        )
        sequence = ('author', 'commit_total', 'author_total', '...' )
        template_name = 'table.html'
