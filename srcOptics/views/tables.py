import django_tables2 as tables
from ..models import Statistic

class StatTable(tables.Table):
    author_total = tables.Column(attrs={"th": {"class": "num"}})
    commit_total = tables.Column(attrs={"th": {"class": "num"}})
    files_changed = tables.Column(verbose_name='Files Changed', attrs={"th": {"class": "num"}})
    lines_changed = tables.Column(verbose_name='∆', attrs={"th": {"class": "lines"}})
    lines_added = tables.Column(verbose_name='+', attrs={"th": {"class": "lines"}})
    lines_removed = tables.Column(verbose_name='-', attrs={"th": {"class": "lines"}})
    repo = tables.TemplateColumn('<a href="#{{record.repo}}">{{record.repo}}</a>',  attrs={"td": {"class": "repo"}})
    
    class Meta:
        model = Statistic
        exclude = ('author', 'id', 'start_date', 'interval', 'file')
        template_name = 'table.html'