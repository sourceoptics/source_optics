from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Organization)
admin.site.register(Repository)
admin.site.register(Account)
admin.site.register(Author)
admin.site.register(Commit)
admin.site.register(LoginCredential)
