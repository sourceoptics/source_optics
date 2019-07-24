# Copyright 2018 SourceOptics Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from django.contrib import admin
from django.forms import CharField, ModelForm, PasswordInput

from .models import Organization, Statistic, Repository, Author, Commit, FileChange, File, Tag, Credential


def fast_delete(modeladmin, request, queryset):
    queryset.delete()

class RepoAdmin(admin.ModelAdmin):
    list_display = ('name','last_pulled', 'last_scanned', 'enabled')
    fields = ['organization', 'enabled', 'tags', 'name', 'url', 'webhook_token',
              'force_next_pull', 'force_nuclear_rescan',
              'scanner_directory_allow_list', 'scanner_directory_deny_list',
              'scanner_extension_allow_list', 'scanner_extension_deny_list' ]
    actions = [fast_delete]

class CommitAdmin(admin.ModelAdmin):
    list_display = ('sha', 'subject', 'repo', 'author', 'commit_date')
    actions = [fast_delete]

class StatAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'interval', 'repo', 'author', 'commit_total',
    'lines_added', 'lines_removed', 'lines_changed', 'files_changed', 'author_total')
    actions = [fast_delete]

class CredentialForm(ModelForm):
    password = CharField(widget=PasswordInput(), required=False)
    ssh_unlock_passphrase = CharField(widget=PasswordInput(), required=False)
    class Meta:
        model = Credential
        fields = '__all__'


class CredentialAdmin(admin.ModelAdmin):
    form = CredentialForm

admin.site.register(Organization)
admin.site.register(Statistic, StatAdmin)
admin.site.register(Repository, RepoAdmin)
admin.site.register(Author)
admin.site.register(Commit, CommitAdmin)
admin.site.register(FileChange)
admin.site.register(File)
admin.site.register(Tag)
admin.site.register(Credential, CredentialAdmin)
