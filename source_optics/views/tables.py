# contributor note: the django UI will be eventually replaced by a new dynamic frontend speaking to the REST API, do not add features

import django_tables2 as tables
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import F
from django_tables2.utils import A

from ..models import Repository, Statistic


class ColumnNumber(tables.Column):
    def render(self,value):
        return intcomma(value)

NUM_CLASS = dict(td={ "class" : "num"})
REPO_CLASS = dict(td={ "class" : "repo" })

def repo_team_link(what):
    return reverse('repo-team', args=[what.name])

def repo_contributors_link(what):
    return reverse('repo-contributors', args=[what.name])

class StatTable(tables.Table):

    author_total = ColumnNumber(verbose_name='Author Total', attrs=NUM_CLASS)
    commit_total = ColumnNumber(verbose_name='Commit Total', attrs=NUM_CLASS)
    files_changed = ColumnNumber(verbose_name='Files Changed', attrs=NUM_CLASS)
    
    # FIXME: introduce FontAwesome icons, add new reversed URLs to views

    team = tables.TemplateColumn('<i class="fas fa-users"></i>', linkify=('repo_team', {'repo_name': tables.A('repo.name') }))
    contributors = tables.TemplateColumn('<i class="fas fa-user"></i>', linkify=('repo_contributors', {'repo_name': tables.A('repo.name') }))
    repo_last_pulled = tables.DateTimeColumn(verbose_name='Last Pulled', format='m\/d\/y P')
    repo_last_scanned = tables.DateTimeColumn(verbose_name='Last Scanned', format='m\/d\/y P')
    lines_added = ColumnNumber(verbose_name='Lines Added', attrs={"th": {"class": "lines"}})
    lines_removed = ColumnNumber(verbose_name='Lines Removed', attrs={"th": {"class": "lines"}})
    repo = tables.Column(attrs=REPO_CLASS)

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
        sequence = ('repo', 'team', 'contributors', 'repo_last_scanned', 'repo_last_pulled', 'commit_total', 'author_total', '...' )
        template_name = 'table.html'

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
