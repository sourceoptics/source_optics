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


from django.db import models
from django.db.models import Sum, Max
from django.utils import timezone

# if author = null, entry represents total stats for interval
# if author = X, entry represent X's author stats for the given interval

class Statistic(models.Model):

    INTERVALS = (
        ('DY', 'Day'),
        ('WK', 'Week'),
        ('MN', 'Month'),
        ('LF', 'Lifetime')
    )

    start_date = models.DateTimeField(blank=False, null=True)
    interval = models.TextField(max_length=5, choices=INTERVALS)
    repo = models.ForeignKey('Repository', on_delete=models.CASCADE, null=True, related_name='repo')
    author = models.ForeignKey('Author', on_delete=models.CASCADE, blank=True, null=True, related_name='author')

    lines_added = models.IntegerField(blank = True, null = True)
    lines_removed = models.IntegerField(blank = True, null = True)
    lines_changed = models.IntegerField(blank = True, null = True)
    commit_total = models.IntegerField(blank = True, null = True)
    files_changed = models.IntegerField(blank = True, null = True)
    author_total = models.IntegerField(blank = True, null = True)
    days_active = models.IntegerField(blank=True, null=False, default=0)
    average_commit_size = models.IntegerField(blank=True, null=True, default=0)

    commits_per_day = models.FloatField(blank=True, null=True, default=0)
    files_changed_per_day = models.FloatField(blank=True, null=True, default=0)
    lines_changed_per_day = models.FloatField(blank=True, null=True, default=0)
    bias = models.IntegerField(blank=True, null=True, default=0)
    flux = models.FloatField(blank=True, null=True, default=0)
    commitment = models.FloatField(blank=True, null=True, default=0)

    earliest_commit_date = models.DateTimeField(blank=True, null=True)
    latest_commit_date = models.DateTimeField(blank=True, null=True)
    days_since_seen = models.IntegerField(blank=False, null=True, default=-1)
    days_before_joined = models.IntegerField(blank=False, null=True, default=-1)
    longevity = models.IntegerField(blank=True, null=False, default=0)
    last_scanned = models.DateTimeField(blank=True, null=True)

    moves = models.IntegerField(blank=True, null=False, default=0)
    edits = models.IntegerField(blank=True, null=False, default=0)
    creates = models.IntegerField(blank=True, null=False, default=0)

    def __str__(self):
        if self.author is None:
            return "Stat(Total): I=" + str(self.interval[0]) + " D=" + str(self.start_date)
        else:
            return "Stat(Author): " + str(self.author) + " I=" + str(self.interval[0]) + " D=" + str(self.start_date)

    class Meta:

        unique_together = [
            [ 'start_date', 'interval', 'repo', 'author' ]
        ]

        indexes = [
            models.Index(fields=['start_date', 'interval', 'repo', 'author'], name='author_rollup3'),
        ]

    @classmethod
    def aggregate_data(cls, queryset):
        return queryset.aggregate(
            lines_added=Sum("lines_added"),
            lines_removed=Sum("lines_removed"),
            lines_changed=Sum("lines_changed"),
            commit_total=Sum("commit_total"),
            days_active=Sum("days_active"),
            moves=Sum("moves"),
            edits=Sum("edits"),
            creates=Sum("creates")
        )

    @classmethod
    def annotate(cls, queryset):
        # FIXME: eventually make all this model driven so it doesn't need double entry
        return queryset.annotate(
            # this next one is kind of weird, but we need it to add the value in
            annotated_repo=Max("repo__name"),
            annotated_author_name=Max("author__display_name"),
            annotated_last_scanned=Max("last_scanned"),
            annotated_lines_added=Sum("lines_added"),
            annotated_lines_removed=Sum("lines_removed"),
            annotated_lines_changed=Sum("lines_changed"),
            annotated_commit_total=Sum("commit_total"),
            annotated_days_active=Sum("days_active"),
            annotated_moves=Sum("moves"),
            annotated_edits=Sum("edits"),
            annotated_creates=Sum("creates"),
            annotated_latest_commit_date=Max('latest_commit_date'),
            annotated_longevity=Sum('days_active')
        )

    @classmethod
    def compute_interval_statistic(cls, queryset, interval=interval, repo=None, author=None, start=None, end=None, for_update=False):

        from . statistic import Statistic
        from . author import Author
        from . file_change import FileChange

        # used by rollup.py to derive a rollup interval from another.

        if interval != 'LF':
            assert start is not None
            assert end is not None
        assert repo is not None

        data = Statistic.aggregate_data(queryset)
        author_count = Author.author_count(repo, start=start, end=end)
        files_changed = FileChange.change_count(repo=repo, start=start, end=end, author=author)

        if author and isinstance(author, int):
            # FIXME: find where this is happening and make sure the system returns objects.
            author = Author.objects.get(pk=author)

        stat = Statistic(
            start_date=start,
            interval=interval,
            repo=repo,
            author=author,
            lines_added=data['lines_added'],
            lines_removed=data['lines_removed'],
            lines_changed=data['lines_changed'],
            commit_total=data['commit_total'],
            days_active=data['days_active'],
            files_changed=files_changed,
            author_total=author_count,
            moves=data['moves'],
            creates=data['creates'],
            edits=data['edits']
        )

        stat.compute_derived_values()

        today = timezone.now()

        if for_update and interval == 'LF':

            all_earliest = repo.earliest_commit_date()
            all_latest = repo.latest_commit_date()
            stat.earliest_commit_date = repo.earliest_commit_date(author)
            stat.latest_commit_date = repo.latest_commit_date(author)
            stat.days_since_seen = (all_latest - stat.latest_commit_date).days
            stat.days_before_joined = (stat.earliest_commit_date - all_earliest).days
            stat.longevity = (stat.latest_commit_date - stat.earliest_commit_date).days + 1
            stat.commitment = (stat.days_active / (1 + stat.longevity))
            stat.last_scanned = today

            update_stats = None
            if author:
                update_stats = Statistic.objects.filter(repo=repo, author=author)
            else:
                update_stats = Statistic.objects.filter(repo=repo, author__isnull=True)
            # these stats are somewhat denormalized 'globals' but allows us to include them efficiently in time-series tooltips which is nice.
            update_stats.update(
                earliest_commit_date = stat.earliest_commit_date,
                latest_commit_date = stat.latest_commit_date,
                days_since_seen = stat.days_since_seen,
                days_before_joined = stat.days_before_joined,
                longevity = stat.longevity,
                commitment = stat.commitment,
                last_scanned = today,
            )

        elif not for_update and queryset.count():

            if author:
                first = queryset.first()
                stat.earliest_commit_date = first.earliest_commit_date
                stat.latest_commit_date = first.latest_commit_date
                stat.days_since_seen = first.days_since_seen
                stat.days_before_joined = first.days_before_joined
                stat.longevity = first.longevity
                stat.commitment = first.commitment
                stat.last_scanned = today
            else:
                # leave these at defaults
                pass




        return stat

    def compute_derived_values(self):
        self.average_commit_size = Statistic._div_safe(self, 'lines_changed', 'commit_total')
        self.commits_per_day = Statistic._div_safe(self, 'commit_total', 'days_active')
        self.lines_changed_per_day = Statistic._div_safe(self, 'lines_changed', 'days_active')
        self.files_changed_per_day = Statistic._div_safe(self, 'files_changed', 'days_active')
        self.flux = Statistic._div_safe(self, 'lines_changed', 'files_changed')
        if self.lines_added and self.lines_removed:
            self.bias = self.lines_added - self.lines_removed
        else:
            self.bias = 0

    @classmethod
    def _div_safe(cls, data, left, right):
        # FIXME: more of a question - these are float fields, do we want this, or should we make them int fields?
        # we're casting anyway at this point.
        if isinstance(data, dict):
            # FIXME: when done refactoring, I would think we'd only have objects, and this part
            # would no longer be needed.
            if data[right]:
                return int(float(data[left]) / float(data[right]))
            else:
                return 0
        else:
            left  = getattr(data, left, None)
            right = getattr(data, right, None)
            if left and right:
                return int(float(left) / float(right))
            else:
                return 0

    def copy_fields_for_update(self, other):
        # TODO: make this list of fields gathered automatically from the model so maintaince
        # of this function isn't required?  Get all Int + Date fields, basically
        self.lines_added = other.lines_added
        self.lines_removed = other.lines_removed
        self.lines_changed = other.lines_changed
        self.commit_total = other.commit_total
        self.files_changed = other.files_changed
        self.author_total = other.author_total
        self.earliest_commit_date = other.earliest_commit_date
        self.latest_commit_date = other.latest_commit_date
        self.days_since_seen = other.days_since_seen
        self.days_before_joined = other.days_before_joined
        self.days_active = other.days_active
        self.average_commit_size = other.average_commit_size
        self.commits_per_day = other.commits_per_day
        self.lines_changed_per_day = other.lines_changed_per_day
        self.files_changed_per_day = other.files_changed_per_day
        self.bias = other.bias
        self.flux = other.flux
        self.commitment = other.commitment
        self.longevity = other.longevity
        self.moves = other.moves
        self.creates = other.creates
        self.edits = other.edits


    @classmethod
    def queryset_for_range(cls, repos=None, authors=None, interval=None, author=None, start=None, end=None):

        assert repos or authors
        assert interval is not None

        stats = Statistic.objects.select_related('author', 'repo')

        if authors:
            stats = stats.filter(author__pk__in=authors)
        else:
            stats = stats.filter(author__isnull=True)

        if repos:
            stats = stats.filter(repo__pk__in=repos)

        if start and interval != 'LF':
            stats = stats.filter(start_date__range=(start,end), interval=interval)
        else:
            stats = stats.filter(interval='LF')

        return stats

    def to_dict(self):
        # FIXME: this really should take the interval as a parameter, such that it can not
        # supply statistics that don't make sense if the interval != lifetime ('LF').
        result = dict(
            days_active=self.days_active,
            commit_total=self.commit_total,
            average_commit_size=self.average_commit_size,
            lines_changed=self.lines_changed,
            lines_added=self.lines_added,
            lines_removed=self.lines_removed,
            longevity=self.longevity,
            earliest_commit_date=str(self.earliest_commit_date),
            latest_commit_date=str(self.latest_commit_date),
            days_before_joined=self.days_before_joined,
            days_since_seen=self.days_since_seen,
            author_total=self.author_total,
            files_changed=self.files_changed,
            files_changed_per_day=self.files_changed_per_day,
            lines_changed_per_day=self.lines_changed_per_day,
            commits_per_day=self.commits_per_day,
            bias=self.bias,
            flux=self.flux,
            commitment=self.commitment,
            creates=self.creates,
            edits=self.edits,
            moves=self.moves
        )
        if self.author:
            result['author']=self.author.email
        else:
            result['author']=None
        return result


    def to_author_dict(self, repo, author):

        # FIXME: this is somewhat similar to the views.py aggregrate needs but slightly different,
        # as we refactor, try to consolidate the duplication. This is only used for lifetime
        # reports, that don't use the interval summing code, but can't we just sum the lifetime
        # stat as an interval of one? I think we can.  This means the extra DB lookups are redundant.

        stat2 = self.to_dict()
        # there's a LRU cache around this, but is there a better way to do this?
        stat2['files_changed'] = author.files_changed(repo)
        return stat2