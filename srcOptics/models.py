from django.db import models

# commit points to owning repo
class Commit(models.Model):
    repo = models.ForeignKey('Repository', on_delete=models.SET_NULL, null=True)
    sha = models.CharField(max_length=256, default='')
    lines_added = models.IntegerField(default=0)
    lines_removed = models.IntegerField(default=0)

class Repository(models.Model):
    parent = models.ForeignKey('Organization', on_delete=models.SET_NULL, null=True)
    url = models.CharField(max_length=256, default='')
    name = models.CharField(max_length=32, default='')
    
    def __str__(self):
        return self.name

class Organization(models.Model):
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)    
    name = models.CharField(max_length=32, default='')

    def __str__(self):
        return self.name

class Admin(models.Model):
    organizations = models.ForeignKey('Organization', on_delete=models.SET_NULL, null=True)
    account = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True)

class Account(models.Model):
    organizations = models.ForeignKey('Organization', on_delete=models.SET_NULL, null=True, blank=True)
    repos = models.ForeignKey('Repository', on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=16, default='')
    email = models.CharField(max_length=32, default='')

    def __str__(self):
        return self.username
