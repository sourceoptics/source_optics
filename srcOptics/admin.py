from django.contrib import admin
from django import forms
from django.forms import ModelForm, PasswordInput
# Register your models here.
from .models import *
from srcOptics.scanner.git import Scanner

def scan_selected(modeladmin, request, queryset):
    for rep in queryset:
        print("Scanning repository: " + rep.url)
        Scanner.scan_repo(rep.url, rep.name, rep.cred)

class RepoAdmin(admin.ModelAdmin):
    list_display = ('name','last_pulled', 'last_scanned', 'enabled')
    fields = ['organization', 'enabled', 'tags', 'cred','name', 'url']
    actions = [scan_selected]

class CommitAdmin(admin.ModelAdmin):
    list_display = ('sha', 'subject', 'repo', 'author', 'commit_date')

class StatAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'interval', 'repo', 'author', 'commit_total',
    'lines_added', 'lines_removed', 'lines_changed', 'files_changed', 'author_total')

class LoginCredentialForm(ModelForm):
    password = forms.CharField(widget=PasswordInput())
    class Meta:
        model = LoginCredential
        fields = '__all__'


class LoginCredentialAdmin(admin.ModelAdmin):
    form = LoginCredentialForm

admin.site.register(Organization)
admin.site.register(Statistic, StatAdmin)
admin.site.register(Repository, RepoAdmin)
admin.site.register(Author)
admin.site.register(Commit, CommitAdmin)
admin.site.register(FileChange)
admin.site.register(File)
admin.site.register(Tag)
admin.site.register(LoginCredential, LoginCredentialAdmin)
