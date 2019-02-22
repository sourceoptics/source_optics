import django_tables2 as tables
from ..models import Statistic

class StatTable(tables.Table):
    lines_added = tables.Column(verbose_name='+ Lines', attrs={"th": {"class": "num"}})
    lines_removed = tables.Column(verbose_name='- Lines', attrs={"th": {"class": "num"}})
    
    class Meta:
        # model = Statistic
        exclude = ('id',)