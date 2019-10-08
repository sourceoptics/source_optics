# Copyright 2018-2019 SourceOptics Project Contributors
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

# scope.py - turns URLs and query strings into objects and typed, validated parameters

import datetime
from django.utils import timezone
from source_optics.models import (Organization, Repository, Author)
import source_optics.models as models
from . import reports

CURRENT_TZ = timezone.get_current_timezone()

# FIXME: lots of refactoring in fuzzy "what is the scope" logic is still required

def is_int(x):
    try:
        int(x)
        return True
    except:
        return False

class Scope(object):

    __slots__ = [
        'start', 'end', 'display_end', 'start_str', 'end_str', 'interval', 'org', 'orgs', 'orgs_count',
        'repos', 'repo', 'repos', 'repos_str', 'page_size', 'page', 'author', 'context', 'add_repo_table',
        'add_orgs_table', 'available_repos', 'request', 'full_time_range', 'path', 'file', 'extension'
    ]

    def _compute_start_and_end(self):
        """
        Most pages can specify a start and end date
        """

        start = self.request.GET.get('start', None)
        end = self.request.GET.get('end', None)
        now = timezone.now()
        epoch = datetime.datetime.strptime("1970-01-01", "%Y-%m-%d").replace(tzinfo=CURRENT_TZ)

        self.full_time_range=False

        if end == '_' or not end:
            end = timezone.now()
        elif end is not None:
            end = datetime.datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=CURRENT_TZ)

        self.end = end + datetime.timedelta(days=1)  # start of tomorrow

        if start == '_' or not start:
            start = datetime.datetime.strptime("1970-01-01", "%Y-%m-%d")
        else:
            start = datetime.datetime.strptime(start, "%Y-%m-%d")
        self.start = start

        self.start = self.start.replace(tzinfo=CURRENT_TZ)
        self.end = self.end.replace(tzinfo=CURRENT_TZ)

        if (self.start <= epoch) and (self.end >= now):
            self.full_time_range = True

    def _compute_path(self):
        self.path = self.request.GET.get('path', None)
        self.file = self.request.GET.get('file', None)
        self.extension = self.request.GET.get('extension', None)

    def _compute_pagination(self):
        """
        Certain pages like the commit feed are paginated
        """

        self.page_size = self.request.GET.get('page_size', 100)
        self.page = self.request.GET.get('page', 1)

    def _compute_org(self):
        """
        The organization may be specified in the query string as a name or an int
        """

        if not self.org:
            self.org = self.request.GET.get('org', None)
        if self.org:
            if is_int(self.org):
                self.org = Organization.objects.get(pk=int(self.org))
            else:
                self.org = Organization.objects.get(name=self.org)

    def _compute_author(self):
        """
        If the page takes an author, it may be an email or an int...
        FIXME: Note that now that we have 'display_name' on author, we really should search that also.
        """

        author = self.author
        if not author:
            author = self.request.GET.get('author', None)

        if author:
            if is_int(author):
                self.author = Author.objects.get(pk=author)
            else:
                # if we have an email like 12345+noreply@github.com
                # the query string "+" comes back as a space for the "+" and this fixes it. As spaces
                # are illegal in email this should be ok.
                author = author.replace(" ","+")
                self.author = Author.objects.get(email=author)
        else:
            self.author = None

    def _compute_interval(self):
        self.interval = self.request.GET.get('intv', 'WK')

    def _compute_repo(self):
        """
        The repo is an int or a string, but is filtered by the selected organization, as repo names
        should only be unique within an organization.
        """
        # FIXME: this is a mess

        self.repos_str = None

        repos = self.request.GET.get('repos', None)

        if not self.repo:
            self.repo = self.request.GET.get('repo', None)

        if self.repo:
            if self.org:
                if is_int(self.repo):
                    self.repo = Repository.objects.get(pk=self.repo, organization=self.org)
                else:
                    self.repo = Repository.objects.get(name=self.repo, organization=self.org)
            else:
                if is_int(self.repo):
                    self.repo = Repository.objects.get(pk=self.repo)
                else:
                    # there could be more than on (ex: from a different org), this might not lead to an error
                    self.repo = Repository.objects.get(name=self.repo)
                self.org = self.repo.organization

        if  repos:
            # if the user has passed in a list of repositories...
            self.repos_str = None
            if isinstance(repos, str) and repos != "None":
                # FIXME: how does it get to be string None?
                repos = repos.split()
                repos_by_id = is_int(repos[0])

                if repos_by_id:
                    repos = repos = [ int(x) for x in repos ]

                if repos_by_id:
                    if self.org:
                        self.repos = Repository.objects.filter(pk__in=repos, organization=self.org).select_related('organization')
                    else:
                        self.repos = Repository.objects.filter(pk__in=repos).select_related('organization')
                else:
                    if self.org:
                        self.repos = Repository.objects.filter(name__in=repos, organization=self.org).select_related('organization')
                    else:
                        self.repos = Repository.objects.filter(name__in=repos).select_related('organization')

                self.repo = self.repos.first()
        else:
            self.repos = None


        if self.repos_str is None:
            if self.request.GET.get('repos',None) is not None:
                self.repos_str = "+".join([ str(x.pk) for x in self.repos.all() ])
            elif self.repo:
                self.repos_str = str(self.repo.pk)

        # available repos is the list of all repos, for lists or dropdowns, not the selected repos list
        if self.org:
            self.available_repos = Repository.objects.filter(organization=self.org).select_related('organization')
        else:
            self.available_repos = Repository.objects.select_related('organization')


    def _compute_orgs(self):
        """
        Any page should have access to the full organization list to populate an organization switch control
        """
        self.orgs = Organization.objects.order_by('name').all()
        self.orgs_count = self.orgs.count()

    def _add_tables(self):
        """
        Repo table is the list of all repos, org table is the list of all orgs.  These are used for
        page indexes and should really NOT be built here inside of Scope (FIXME).
        """

        if self.add_repo_table:
            self.context['repo_table'] = reports.repo_table(self)

        if self.add_orgs_table:
            self.context['orgs_table'] = reports.orgs_table(self)

    def _compute_template_context(self):
        """
        Here's where we build the list of variables that will be available in Django templates.
        """
        self.context = dict(
            author=self.author,
            orgs=self.orgs.order_by('name').all(),
            org=self.org,
            orgs_count=self.orgs.count(),
            available_repos=self.available_repos.all(),
            start=self.start,
            end=self.end,
            repo=self.repo,
            repos_str=self.repos_str,
            intv=self.interval,
            title="Source Optics",
            multiple_repos_selected=self.multiple_repos_selected(),
            full_time_range=self.full_time_range,
            file=self.file,
            path=self.path,
            extension=self.extension
        )
        if self.repos:
            self.context['repos'] = self.repos.all()
        else:
            self.context['repos'] = None
        self._add_start_and_end_strings()
        self._add_tables()

    def _add_start_and_end_strings(self):
        """
        Add formatted versions of the start and end times to the context for use in templates
        """


        if self.start and self.end:
            self.start_str = self.start.strftime("%Y-%m-%d")
            fixed_end = self.end - datetime.timedelta(days=1)
            self.context['display_end'] = fixed_end
            self.end_str = fixed_end.strftime("%Y-%m-%d")
        else:
            self.start_str = None
            self.end_str = None

        self.context['start_str'] = self.start_str
        self.context['end_str'] = self.end_str

    def multiple_repos_selected(self):
        if self.repos_str is None:
            return False
        if not ('+' in self.repos_str):
            return False
        return True


    def standardize_repos_and_authors(self):
        """"
        Doesn't modify a scope, but returns some plural forms that let callers not know' \
        if the scope specified plural or singular objects
        """
        repos = None
        authors = None

        if self.author:

            if isinstance(self.author, str):
                email = self.author.replace(" ","+")
                authors = Author.objects.filter(email=email)
            else:
                authors = Author.objects.filter(pk=self.author.pk).values_list('pk', flat=True)
        elif self.repo:
            authors = self.repo.author_ids(self.start, self.end)
        else:
            authors = None

        if not self.repo and self.author:
            repos = Author.repos(repos, self.start, self.end).values_list('pk', flat=True)
        elif self.repo:
            repos = Repository.objects.filter(pk=self.repo.pk).values_list('pk', flat=True)
        else:
            assert self.org is not None
            repos = [ x.pk for x in Repository.objects.filter(organization=self.org).all() ]

        return (repos, authors)

    def __init__(self, request, org=None, repo=None, author=None, add_repo_table=False, add_orgs_table=False):

        """
        A scope object parses the request query string and makes available scope.context to django
        templates. It is also allowed to raise any errors needed based on invalid query strings.
        """

        # FIXME: get org and repo from the query strings and remove them from the URL structure?
        self.org = org
        self.repo = repo
        self.author = author

        self.add_repo_table = add_repo_table
        self.add_orgs_table = add_orgs_table

        assert request is not None

        self.request = request
        self._compute_path()
        self._compute_pagination()
        self._compute_interval()
        self._compute_org()
        self._compute_author()
        self._compute_orgs()
        self._compute_repo()

        self._compute_start_and_end()
        self._compute_template_context()

        # FIXME: a side effect, but important to have somewhere, should be Django middleware?
        models.cache_clear()

