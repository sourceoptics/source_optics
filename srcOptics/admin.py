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
    list_display = ('name', 'last_pulled', 'last_scanned', 'enabled')
    fields = ['organization', 'enabled', 'cred','name', 'url']
    actions = [scan_selected]

class LoginCredentialForm(ModelForm):
    password = forms.CharField(widget=PasswordInput())
    class Meta:
        model = LoginCredential
        fields = '__all__'


class LoginCredentialAdmin(admin.ModelAdmin):
    form = LoginCredentialForm

admin.site.register(Organization)
admin.site.register(Statistic)
admin.site.register(Repository, RepoAdmin)
admin.site.register(Author)
admin.site.register(Commit)
admin.site.register(FileChange)
admin.site.register(File)
admin.site.register(LoginCredential, LoginCredentialAdmin)
