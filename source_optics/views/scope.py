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

class Scope(object):

    __slots__ = [
        'start', 'end', 'start_str', 'end_str', 'interval', 'org', 'orgs', 'orgs_count',
        'repos', 'repo', 'page_size', 'page', 'author', 'author_email', 'author_domain', 'context'
    ]

    def __init__(self, request, org=None, repo=None, add_repo_table=False):
        """
        Get objects from the URL parameters.
        """

        # FIXME: overdo for code cleanup

        assert request is not None

        start = request.GET.get('start', None)
        end = request.GET.get('end', None)
        interval = request.GET.get('intv', 'WK')
        self.page_size = request.GET.get('page_size', 100)
        self.page = request.GET.get('page', 1)
        self.author_email = request.GET.get('author_email', None)
        self.author_domain = request.GET.get('author_domain', None)
        self.interval = interval
        if not org:
            org = request.GET.get('org', None)
        if not repo:
            repo = request.GET.get('repo', None)

        author = request.GET.get('author', None)
        if author:
            try:
                int(author)
                self.author = Author.objects.get(pk=author)
            except:
                self.author = Author.objects.get(email=author)
        else:
            self.author = None

        # FIXME: a side effect, but important to have somewhere, should be Django middleware?
        models.cache_clear()

        self.interval = interval
        self.orgs = Organization.objects.order_by('name').all()

        if interval is None:
            interval='WK'

        if end == '_' or not end:
            end = timezone.now()
        elif end is not None:
            end = datetime.datetime.strptime(end, "%Y-%m-%d")
        self.end = end + datetime.timedelta(days=1) # start of tomorrow

        if start == '_' or not start:
            start = datetime.datetime.strptime("1970-01-01", "%Y-%m-%d")
        else:
            start = datetime.datetime.strptime(start, "%Y-%m-%d")
        self.start = start


        self.repo = None
        if org:
            try:
                int(org)
                self.org = Organization.objects.get(pk=int(org))
            except:
                self.org = Organization.objects.get(name=int(org))
            if repo:
                try:
                    int(repo)
                    self.repo = Repository.objects.get(pk=repo, organization=self.org)
                except:
                    print("repo", repo)
                    print("org", self.org)
                    self.repo = Repository.objects.get(name=repo, organization=self.org)
        else:
            self.org = None
            if repo:
                try:
                    int(repo)
                    self.repo = Repository.objects.get(pk=repo)
                except:
                    # there could be more than one, this might not lead to an error
                    self.repo = Repository.objects.get(name=repo)
                self.org = self.repo.organization

        if org:
            self.repos = Repository.objects.filter(organization=org).select_related('organization')
        else:
            self.repos = Repository.objects.all()


        self.orgs_count = self.orgs.count()

        context = dict(
            author=self.author,
            orgs=self.orgs.order_by('name').all(),
            org=self.org,
            orgs_count=self.orgs.count(),
            repos=self.repos.all(),
            start=self.start,
            end=self.end,
            repo=self.repo,
            intv=self.interval,
            title="Source Optics"
        )

        if start and end:
            self.start_str = start.strftime("%Y-%m-%d")
            self.end_str = end.strftime("%Y-%m-%d")
        else:
            self.start_str = None
            self.end_str = None

        context['start_str'] = self.start_str
        context['end_str'] = self.end_str

        if add_repo_table:
            context['repo_table'] = reports.repo_table(self)

        self.context = context


