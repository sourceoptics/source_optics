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
    enabled = models.BooleanField(default=False)
    lastScanned = models.DateTimeField(blank=True, null=True)
    cred = models.ForeignKey(LoginCredential, on_delete=models.CASCADE, null=True)
    url = models.TextField(max_length=256, unique=True, blank=False)
    name = models.TextField(db_index=True, max_length=32, blank=False)

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
    startDay = models.DateTimeField(blank=False, null=True)
    interval = models.TextField(max_length=5, choices=[('DY', 'day'), ('WK', 'week'), ('MN', 'month')])
    repo = models.ForeignKey(Repository, db_index=True, on_delete=models.CASCADE, null=True, related_name='repo')
    author = models.ForeignKey(Author, db_index=True, on_delete=models.CASCADE, blank=True, null=True, related_name='author')
    file = models.ForeignKey(File, db_index=True, on_delete=models.CASCADE, blank=True, null=True, related_name='file')
    data = JSONField()

    #data =
    # { linesAdded: 0,
    #   linesRemoved: 0,
    #   linesChanged: 0,
    #   commitTotal: 0,
    #   filesChanged 0,
    #   authorTotal 0
    # }
