import django_tables2 as tables
from ..models import Statistic

class StatTable(tables.Table):
    author_total = tables.Column(accessor='get_data.author_total', verbose_name='Author Total', attrs={"th": {"class": "num"}})
    commit_total = tables.Column(accessor='get_data.commit_total', verbose_name='Commit Total', attrs={"th": {"class": "num"}})
    files_changed = tables.Column(accessor='get_data.files_changed', verbose_name='Files Changed', attrs={"th": {"class": "num"}})
    lines_changed = tables.Column(accessor='get_data.lines_changed', verbose_name='∆', attrs={"th": {"class": "lines"}})
    lines_added = tables.Column(accessor='get_data.lines_added', verbose_name='+', attrs={"th": {"class": "lines"}})
    lines_removed = tables.Column(accessor='get_data.lines_removed', verbose_name='-', attrs={"th": {"class": "lines"}})
    repo = tables.Column(verbose_name='Repositories', attrs={"td": {"class": "repo"}})
    
    class Meta:
        model = Statistic
        exclude = ('id', 'startDay', 'interval', 'data', 'file')
        template_name = 'table.html'