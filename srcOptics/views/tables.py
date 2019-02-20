import django_tables2 as tables
from ..models import Commit

class CommitTable(tables.Table):
    lines_added = tables.Column(verbose_name='+ Lines', attrs={"th": {"class": "num"}})
    lines_removed = tables.Column(verbose_name='- Lines', attrs={"th": {"class": "num"}})
    sha = tables.TemplateColumn('<a href="#">{{record.sha}}</a>')
    class Meta:
        model = Commit
        exclude = ('id',)