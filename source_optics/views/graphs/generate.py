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

class GraphGenerator(object):

    """
    The GraphGenerator class provides flexible data sufficient to render most pages in the
    application in a single response.

    The input is a parameter structure, that looks like this:
     {
           'end'  : ISO 8601 time string or omit
           'history' : number of days from 'end' to look back for stats
           'interval': 'DY',
           'author_filter': [ 'michael@michaeldehaan.net', 'foo@example.org' ], # or omit
           'repo_filter' : [ 'asdf1', 'asdf2' ], # or omit
           'organization' : '2019-fall-csc201-001',  # required!
           'aspects' : [ 'totals', 'author_info', 'repo_info', 'commit_graph', 'lines_added_graph', 'lines_removed_graph' ]
     }

     If any parameter is not supplied, it has the following effect:

     end - assumes today
     interval - assumes 'WK', valid also are 'DY' and 'MN'
     history - assumes 365 (1 year)
     author_filter - assumes no filter, includes data for all authors rather than selected authors
     repo_filter - assumes no filter, includes data for all repos in the organization rather than selected repos
     organization - this is required, include an organization name or get an error!
     aspects - assumes just ['totals'] which is the result from the REPORT_totals function

     The most interesting paramter by far is 'aspects', as each of these names corresponds with a function
     name below and will include results from calling that function.

     A author_filter of [] does not mean all authors, but it means give *NO AUTHORS*, in other words, it just
     returns the repo totals ("*ALL*").

     The response looks like this:

     {
           parameters: { ... }
           authors: {
               # each author matched and their database IDs
               'email@example.com': { pk: 1 }
           }
           aspects: {
               # a dictionary of each repo...
               repo_name: {
                   # database ID of the repo
                   pk: 1
                   # each one of these are aspects ...
                   lines_added: <RESULT FROM ASPECT_lines_added> ,
                   lines_removed: <RESULT FROM ASPECT lines_removed>,
                   commits: <RESULT FROM ASPECT commits>
               }, ...
           }
     }

     Asking for too many repos or aspects could possibly result in a very long response time.

     For aspects that represent a line graph, the response looks like this:

            lines_added: {
                'hint': 'line',
                meta: {
                    description: "Lines Added"
                }
                data: {
                    'axes' : {
                        x: 'Date',
                        y: 'Lines Added'
                    },
                    'labels' : {
                        x: [ <list of date strings> ],
                    },
                    'data_by_author' : {
\                       'user1@example.com' : [ 1, 2, 3, 4, 5, 6, ... ]
                        'user2@example.com' : [ 1, 2, 3, 4, 5, 6, ... ]
                    },
                    'annotate_series' : {
                        3: 'Start of Semester'
                        15: 'Superbowl'
                    }
                    'data_overall' : [ 1, 2, 3, 4, 5, 6 ]
                }
            }

    Annotations of specific points of a data can be considered in the future.

    For aspects that represent a report (and thus are not time series related), the format is like this:

            basic_report: {
                hint: 'table'
                meta: {
                    description: "Summary Statistics"
                }
                data: {
                    overall: {
                        lines_added: 50
                        lines_removed: 100
                        lines_changed: 150
                        commits: 86
                    }
                    by_author: {
                        'user1@example.com' : {
                             lines_added: 50
                             lines_removed: 100
                             lines_changed: 150
                            commits: 99
                      }
                 }
            }

    For aspects that represent pie chart information:

            pie_contribution: {
                hint' : 'pie'
                meta: {
                    commits: {
                        description: "Commits Per Team Member"
                    }
                    lines_added: {
                        description: "Lines Added Per Team Member
                    }
                }
                data: {
                    commits': {
                        'user1@example.com': 219,
                        'user2@example.com': 456,
                    }
                    lines_added': {
                        ...
                    }
                }
            }

    Other format types may be added later.

    If the repo has a very large number of authors, pagination may be required and should be implemented client
    side for now and server side later.



    """


    def __init__(self, data):

        # input parameters
        self._start = data.get('start', None)
        self._end = data.get('end', None)
        self._interval = data.get('interval', 'DY')
        self._authors = data.get('authors', None)
        self._repos = data.get('repos', None)
        self._organization = data.get('organization', 'default')
        self._aspects = data.get('aspects', None)

        self.get_defaults()

    def get_defaults(cls, data):

        self.organization = Organization.objects.filter(name=self._organization)

        self.repos = Repos.objects.filter(self.organization)
        if self._repos:
            self.repos.filter(pk__in=self._repos)
        self.repos = self.repos.all()

        if self._aspects is not None:
            self.aspects = self._aspects
        else:
            self.aspects = [ 'repo_summary' ]


    def graph(self, data):
        pass

