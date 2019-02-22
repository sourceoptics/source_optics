from django.contrib import admin
# Register your models here.
from .models import *
from srcOptics.scanner.git import Scanner

def scan_selected(modeladmin, request, queryset):
    for rep in queryset:
        print("Scanning repository: " + rep.url)
        Scanner.scan_repo(rep.url, rep.cred)

class RepoAdmin(admin.ModelAdmin):
    actions = [scan_selected]

admin.site.register(Organization)
admin.site.register(Repository, RepoAdmin)
admin.site.register(Author)
admin.site.register(Commit)
admin.site.register(FileChange)
admin.site.register(File)
admin.site.register(LoginCredential)
