import django_tables2 as tables
from ..models import Statistic
from django.contrib.humanize.templatetags.humanize import intcomma

class ColumnNumber(tables.Column):
    def render(self,value):
        return intcomma(value)

class StatTable(tables.Table):
    author_total = ColumnNumber(attrs={"th": {"class": "num"}})
    commit_total = ColumnNumber(attrs={"th": {"class": "num"}})
    files_changed = ColumnNumber(verbose_name='Files Changed', attrs={"th": {"class": "num"}})
    lines_changed = ColumnNumber(verbose_name='∆', attrs={"th": {"class": "lines"}})
    lines_added = ColumnNumber(verbose_name='+', attrs={"th": {"class": "lines"}})
    lines_removed = ColumnNumber(verbose_name='-', attrs={"th": {"class": "lines"}})
    start_date = tables.Column()
    repo = tables.Column(attrs={"td": {"class": "repo"}})
    
    class Meta:
        model = Statistic
        exclude = (
            'author',
            'id',
            'file',
            'interval',
            'start_date'
        )
        sequence = ('repo','...')
        template_name = 'table.html'