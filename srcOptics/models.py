from django.contrib.postgres.fields import JSONField
from django.db import models
from django.contrib.auth.models import Group, User

class Organization(models.Model):
    # parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
    name = models.TextField(max_length=32, blank=False)
    admins = models.ManyToManyField(User, related_name='admins')
    members = models.ManyToManyField(User, related_name='members')

    def __str__(self):
        return self.name

class LoginCredential(models.Model):
    username = models.TextField(max_length=32, blank=True)
    password = models.TextField(max_length=128,  blank=True)

class Repository(models.Model):
    class Meta:
        verbose_name_plural = "repositories"
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True)
    enabled = models.BooleanField(default=False)
    last_scanned = models.DateTimeField(blank=True, null=True)
    cred = models.ForeignKey(LoginCredential, on_delete=models.CASCADE, null=True, blank = True)
    url = models.TextField(max_length=256, unique=True, blank=False)
    name = models.TextField(db_index=True, max_length=32, blank=True)

    def __str__(self):
        return self.name

class Author(models.Model):
    email = models.TextField(db_index=True, max_length=64, unique=True, blank=False, null=True)

    def __str__(self):
        return self.email

class Commit(models.Model):
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='repos')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=False, null=True, related_name='authors')
    sha = models.TextField(db_index=True, max_length=256, blank=False)
    files = models.ManyToManyField('File')
    commit_date = models.DateTimeField(blank=False, null=True)
    author_date = models.DateTimeField(blank=False, null=True)
    subject = models.TextField(db_index=True, max_length=256, blank=False)
    lines_added = models.IntegerField(default=0)
    lines_removed = models.IntegerField(default=0)

    def __str__(self):
        return self.subject

class FileChange(models.Model):
    name = models.TextField(db_index=True, max_length=256, blank=False, null=True)
    path = models.TextField(db_index=True, max_length=256, blank=False, null=True)
    ext = models.TextField(max_length=32, blank=False)
    binary = models.BooleanField(default=False)
    commit = models.ForeignKey(Commit, db_index=True, on_delete=models.CASCADE, related_name='commit')
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='filechange_repo', null=True)
    lines_added = models.IntegerField(default=0)
    lines_removed = models.IntegerField(default=0)

    def __str__(self):
        return self.path

class File(models.Model):
    repo = models.ForeignKey(Repository, db_index=True, on_delete=models.CASCADE, related_name='file_repo', null=True)
    name = models.TextField(db_index=True, max_length=256, blank=False, null=True)
    path = models.TextField(db_index=True, max_length=256, blank=False, null=True)
    ext = models.TextField(max_length=32, blank=False, null=True)
    binary = models.BooleanField(default=False)
    changes = models.ManyToManyField(FileChange, related_name='changes')
    lines_added = models.IntegerField(default=0)
    lines_removed = models.IntegerField(default=0)

    def __str__(self):
        return self.path

# if author = null && file = null, entry represents total stats for interval
# if author = null && file = X, entry represents X's file stats for the given interval
# if author = X && file = null, entry represent X's author stats for the given interval
class Statistic(models.Model):
    INTERVALS = (
        ('DY', 'day'),
        ('WK', 'week'),
        ('MN', 'month')
    )
    start_date = models.DateTimeField(blank=False, null=True)
    interval = models.TextField(max_length=5, choices=INTERVALS)
    repo = models.ForeignKey(Repository, db_index=True, on_delete=models.CASCADE, null=True, related_name='repo')
    author = models.ForeignKey(Author, db_index=True, on_delete=models.CASCADE, blank=True, null=True, related_name='author')
    file = models.ForeignKey(File, db_index=True, on_delete=models.CASCADE, blank=True, null=True, related_name='file')
    data = JSONField()

    def __str__(self):
        return self.data

    @classmethod
    def create_total_rollup(cls, start_date, interval, repo, data):
        instance = cls(start_date = start_date, interval = interval, repo = repo, data = data)
        return instance

    @classmethod
    def create_author_rollup(cls, start_date, interval, repo, author, data):
        instance = cls(start_date = start_date, interval = interval, repo = repo, author = author, data = data)
        return instance

    @classmethod
    def create_file_rollup(cls, start_date, interval, repo, file, data):
        instance = cls(start_date = start_date, interval = interval, repo = repo, file = file, data = data)
        return instance

    #data =
    # { linesAdded: 0,
    #   linesRemoved: 0,
    #   linesChanged: 0,
    #   commitTotal: 0,
    #   filesChanged 0,
    #   authorTotal 0
    # }
