import django_tables2 as tables
from ..models import Commit

class CommitTable(tables.Table):
    class Meta:
        model = Commit
        exclude = ('id',)