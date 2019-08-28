# OBSOLETE - this will be folded back into the main UI

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

from django.db.models import Sum, Max
from ... models import Statistic, Commit, Author
from datetime import datetime

import json

# About this plugin
# =================
# flex graph takes the following in JSON parameters:
#  - 'show_aspect' - a list of terms
#  - 'by_aspect' - a way to partition the stats, either by 'month' or 'author'
# -
#
# it is suitable for producing 2D, 3D, and even 4D/5D graphs, because it basically returns
# list of tuples for a given repo.

# note: this plugin isn't as database efficient as many of the others
# If this becomes important we could make the scanner compile these in a table and load the new table here.


class Plugin(object):



    def _gen_buckets(self, each, max):


        current = 0
        results = []

        while (current < max):
            top = current + each
            x = [current,top]
            # print("bucket:",x)
            results.append(x)
            current = current + each

        results.append([max,None])
        return results


    def _repo_data(self, repo, each_bucket, bucket_max, metric):

        # FIXME: metric is currently ignored

        results = []

        count = 0

        months = Commit.objects.filter(repo=repo).datetimes('commit_date', 'month', order='ASC').all()
        buckets = self._gen_buckets(each_bucket, bucket_max)


        # FIXME: this is VERY inefficient at the moment and is designed as a Proof of Concept
        # using some hashes for the bucket function would help tons and would be very easy to do, so up next.

        for month in months:
            # print(month)

            # monthly_count = Commit.objects.filter(repo=repo, commit_date__month=month.month, commit_date__year=month.year).count()

            for each_bucket in buckets:
                # print("......... %s %s" % (each_bucket[0], each_bucket[1]))

                current, top = each_bucket



                commits = Commit.objects.filter(repo=repo,
                                               commit_date__month=month.month,
                                               commit_date__year=month.year)
                authors = commits.values_list('author', flat=True).distinct().all()
                authors = Author.objects.filter(pk__in=authors)

                count = 0

                for author in authors.all():
                    # print(each_bucket)


                    author_ct = Statistic.objects.filter(
                        author=author,
                        repo=repo,
                        interval='MN',
                        start_date__month=month.month,
                        start_date__year=month.year
                    ).aggregate(
                        lines_changed=Sum("lines_changed"),
                    )
                    #print(author_ct)
                    if author_ct is None:
                        continue
                    author_ct = author_ct['lines_changed']

                    if author_ct is None:
                        author_ct = 0

                    if top is not None:
                        if ((author_ct >= current) and (author_ct < top)):
                            print("A=%s, AC=%s, CURRENT=%s, TOP=%s" % (author.email, author_ct, current, top))
                            count = count + 1
                    if top is None:
                        if (author_ct > current):
                            print("A!=%s, AC=%s, CURRENT=%s, TOP=%s" % (author.email, author_ct, current, top))
                            count = count + 1
                    else:
                        continue


                if (count > 500):
                    # don't let anomalies smash the graph scale, crop it
                    count = 500


                entry = [ month, count, current]
                if count != 0:
                    print(entry)
                else:
                    print(".")
                if count != 0:
                    results.append(entry)

                #if top is None or ((count == 0) and (top > monthly_count)):
                #    break


        return results



    def generate(self, start=None, end=None, days=0, interval='DY', repos=None, authors=None, arguments=None):

        # author filter is ignored, guess that is ok for now

        each_bucket = int(arguments.get('each_bucket', 10))
        bucket_max = int(arguments.get('bucket_max', 1000))
        metric = arguments.get('metric', 'commits')

        data = dict()
        data['meta'] = dict(
            format = 'data_points_by_repo'
        )
        reports = data['reports'] = dict()

        for repo in repos:

            reports[repo.name] = self._repo_data(repo, each_bucket, bucket_max, metric)

        return data
