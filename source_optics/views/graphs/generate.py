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


# note: the present code does not require a user login and will return information
# on all repos, if we change this behavior in the UI, we also need to pass in request.user
# for filtering here.

from datetime import timedelta
from ... serializers import ReportParameters
from ... plugin_loader import PluginLoader
from ... models import Organization, Repository, Author

import dateutil.parser

OLD = """

class ReportParameters(object):

    def __init__(self, data):

        # input parameters
        self._end = data.get('start', None)
        self._days = data.get('days', 365)
        self._interval = data.get('interval', 'DY')
        self._author_ids = data.get('author_ids', None)
        self._repo_ids = data.get('repo_ids', None)
        self._organization = data.get('organization', None)
        self._plugin = data.get('plugins', None)
        self.arguments = data.get('arguments', None)

        self.get_defaults()

    def get_defaults(cls, data):

        self.end = dateutil.parser.parse(self._end)
        self.start = self.end - -datetime.timedelta(days=self._days)

        self.authors = Author.objects
        self.repos = Repo.objects

        if self._author_ids:
            self.authors = self.authors.filter(pk__in=self._author_ids)
        if self._repo_ids:
            self.repos = self.repos.filter(pk__in=self._repo_ids)

        self.organization = Organization.objects.get(pk=self._organization)

        self.plugins = PluginLoader().get_report_api_plugins()
        self.plugin = self.plugins[data['plugin']]


"""

class GraphGenerator(object):

    def __init__(self, data):

        self.data = data

        self.serializer = ReportParameters(data=data)


    """
    
    The GraphGenerator class intends to return data to fill in most pages in the
    application in a single response.  parameters are described in serializers.py under ReportParameters
    
    Input
    =====
    
    POST /report_api with JSON BODY:
    
    {
        end: 2004-10-16 08:10:15,
        days: 365,
        repo_filter: csc201-project4%,
        plugin: repo_summary
    }
    
    OR (another example):
    
    {
        end: 2004-10-16 08:10:15,
        days: 14,
        repo_id: 27,
        author_filter: "%ncsu.edu",
        plugin: line_graph
    }
    
    Note these use database wildcards, not fnmatch patterns or regexes.   
     
          
    Output
    ======
     
    This structure is POSTED to /report_api and response formats come back like this:
          
     meta: {
        format: 'line_graph'
     }
     
     repos: {
        name1: data_member1,
        name2: data_member2
     }

     
     Each data item per repository varies based on plugin type.  It is easiest to
     just run the plugin to see the format as they should be self explanatory. When building
     new plugin types, follow the standard of other plugins of the same type/format.
     
    """



    def graph(self):

        if not self.serializer.is_valid():
            raise Exception(self.serializer.errors)

        self.data = self.serializer.validated_data

        self.plugins = PluginLoader().get_report_api_plugins()
        self.plugin = self.plugins[self.data['plugin']]


        if self.data['organization_id']:
            self.organization = Organization.objects.get(pk=self.data['organization_id'])
        else:
            raise Exception("organization_id is required")

        if self.data['author_id']:
            self.authors = Author.objects.filter(pk=self.data['author_id'])
        elif self.data['author_pattern']:
            self.authors = Author.objects.filter(email__contains=self.data['author_pattern'])
        else:
            self.authors = Author.objects

        if self.data['repo_id']:
            self.repos = Repository.objects.filter(pk=self.data['repo_id'])
        elif self.data['repo_pattern']:
            self.repos = Repository.objects.filter(name__contains=self.data['repo_pattern'])
        else:
            self.repos = Repository.objects


        self.end = self.data['end']
        self.days = self.data['days']
        self.start = None
        if self.days:
            self.start = self.end - timedelta(days=self.days)

        self.interval = self.data['interval']


        return self.plugin.generate(
            start = self.start,
            end = self.end,
            days = self.days,
            interval = self.interval,
            repos = self.repos,
            authors = self.authors
        )
