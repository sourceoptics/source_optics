from django.contrib.postgres.fields import JSONField
from django.db import models
from django.contrib.auth.models import Group, User

from cryptography import fernet
import binascii
from django.conf import settings
import tempfile
import os

class Organization(models.Model):
    # parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
    name = models.TextField(max_length=32, blank=False)
    admins = models.ManyToManyField(User, related_name='admins')
    members = models.ManyToManyField(User, related_name='members')

    def __str__(self):
        return self.name

class LoginCredential(models.Model):
    username = models.TextField(max_length=32, blank=False)
    password = models.TextField(max_length=128,  blank=False)

    def __str__(self):
        return self.username

    # encrypt the password when we save this
    #  (password needs to be unencrypted when saved)
    def save(self, *args, **kwargs):
        # from vespene
        fd = open(settings.SYMMETRIC_SECRET_KEY, "r")
        symmetric = fd.read()
        fd.close()
        ff = fernet.Fernet(symmetric)
        enc = ff.encrypt(self.password.encode('utf-8'))
        self.password = binascii.hexlify(enc).decode('utf-8')
        super().save(*args, **kwargs)

    # also from vespene
    def unencrypt_password(self):
        fd = open(settings.SYMMETRIC_SECRET_KEY, "r")
        symmetric = fd.read()
        fd.close()
        ff = fernet.Fernet(symmetric)
        enc = binascii.unhexlify(self.password)
        msg = ff.decrypt(enc)
        return msg.decode('utf-8')

    # create an expect file for git clone
    def expect_pass(self):
        pw = self.unencrypt_password()
        (fd, fname) = tempfile.mkstemp()
        fh = open(fname, "w")
        fh.write("#!/bin/bash\n")
        fh.write("echo %s" % pw)
        fh.close()
        os.close(fd)
        os.chmod(fname, 0o700)
        return fname

class Repository(models.Model):
    class Meta:
        verbose_name_plural = "repositories"
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True)
    enabled = models.BooleanField(default=True)
    last_scanned = models.DateTimeField(blank=True, null=True)
    last_pulled = models.DateTimeField(blank = True, null = True)
    cred = models.ForeignKey(LoginCredential, on_delete=models.CASCADE, null=True, blank = True)
    url = models.TextField(max_length=256, unique=True, blank=False)
    name = models.TextField(db_index=True, max_length=32, blank=False, unique= True, null=False)

    def __str__(self):
        return self.name

class Author(models.Model):
    email = models.TextField(db_index=True, max_length=64, unique=True, blank=False, null=True)
    repos = models.ManyToManyField(Repository, related_name='author_repos')

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
    lines_added = models.IntegerField(blank = True, null = True)
    lines_removed = models.IntegerField(blank = True, null = True)
    lines_changed = models.IntegerField(blank = True, null = True)
    commit_total = models.IntegerField(blank = True, null = True)
    files_changed = models.IntegerField(blank = True, null = True)
    author_total = models.IntegerField(blank = True, null = True)

    def __str__(self):
        if self.author is None:
            return "TOTAL " + str(self.interval[0]) + " " + str(self.start_date.date())
        else:
            return "AUTHOR: " + str(self.author) + " " + str(self.interval[0]) + " " + str(self.start_date.date())

    #    return str({'la': self.lines_added, 'lr': self.lines_removed, 'lc' : self.lines_changed,
    #            'ct': self.commit_total, 'fc': self.files_changed, 'at': self.author_total})

    @classmethod
    def create_total_rollup(cls, start_date, interval, repo, lines_added, lines_removed,
                            lines_changed, commit_total, files_changed, author_total):
        instance = cls(start_date = start_date, interval = interval, repo = repo, lines_added = lines_added,
        lines_removed = lines_removed, lines_changed = lines_changed, commit_total = commit_total, files_changed = files_changed,
        author_total = author_total)
        instance.save()
        return instance

    @classmethod
    def create_author_rollup(cls, start_date, interval, repo, author, lines_added, lines_removed,
                            lines_changed, commit_total, files_changed):
        instance = cls(start_date = start_date, interval = interval, repo = repo, author = author, lines_added = lines_added,
        lines_removed = lines_removed, lines_changed = lines_changed, commit_total = commit_total,
        files_changed = files_changed, author_total = 0)
        instance.save()
        return instance

    @classmethod
    def create_file_rollup(cls, start_date, interval, repo, file, data):
        instance = cls(start_date = start_date, interval = interval, repo = repo, file = file, data = data)
        return instance
