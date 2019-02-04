from django.db import models
from django.contrib.auth.models import Group, User

# ?? rather than have 'Account', you can use the built in Django user and
# group models - definitely do this, because Django logins already work with
# these
class Organization(models.Model):
    # parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
    owner = models.ManyToManyField(User, related_name='owner')
    name = models.TextField(max_length=32, blank=False)
    admins = models.ManyToManyField(User, related_name='admins')
    members = models.ManyToManyField(User, related_name='members')

    def __str__(self):
        return self.name

class Repository(models.Model):
    parent = models.ForeignKey(Organization, on_delete=models.SET_NULL, blank=False, null=True, related_name='orgs')
    url = models.TextField(max_length=256, blank=False)
    name = models.TextField(max_length=32, blank=False)
    
    def __str__(self):
        return self.name

class LoginCredential(models.Model):
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE)
    username = models.TextField(max_length=32, blank=False)
    password = models.TextField(max_length=128,  blank=False)
    
    
class Author(models.Model):
    email = models.TextField(max_length=64, blank=False, null=True)
    username = models.TextField(max_length=64, blank=False, null=True)
    
    def __str__(self):
        return self.email

class Commit(models.Model):
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='repos')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=False, null=True, related_name='authors')
    sha = models.TextField(max_length=256, blank=False)
    lines_added = models.IntegerField(default=0)
    lines_removed = models.IntegerField(default=0)

    def __str__(self):
        return self.sha
