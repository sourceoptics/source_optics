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
    username = models.TextField(max_length=32, blank=False)
    password = models.TextField(max_length=128,  blank=False)
    
class Repository(models.Model):
    class Meta:
        verbose_name_plural = "repositories"
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True)
    cred = models.ForeignKey(LoginCredential, on_delete=models.CASCADE, null=True)
    url = models.TextField(max_length=256, unique=True, blank=False)
    name = models.TextField(max_length=32, blank=False)
    
    def __str__(self):
        return self.name
    
class Author(models.Model):
    email = models.TextField(max_length=64, unique=True, blank=False, null=True)
    
    def __str__(self):
        return self.email

class Commit(models.Model):
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='repos')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=False, null=True, related_name='authors')
    sha = models.TextField(max_length=256, blank=False)
    commit_date = models.DateTimeField(blank=False, null=True)
    author_date = models.DateTimeField(blank=False, null=True)
    lines_added = models.IntegerField(default=0)
    lines_removed = models.IntegerField(default=0)

    def __str__(self):
        return self.sha
