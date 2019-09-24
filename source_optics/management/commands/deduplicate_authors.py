# Copyright 2019 SourceOptics Project Contributors
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

import fnmatch

from django.core.management.base import BaseCommand, CommandError
import toml
from source_optics.models import Commit, Organization, Repository, Author

from ... models import Organization, Repository

# usage:
# python3 manage.py deduplicate_authors -o org_name --file authors.yml --plan
# python3 manage.py deduplicate_authors -o org_name --file authors.yml --execute

class Command(BaseCommand):
    help = 'looks for authors using multiple email addresses'

    # FIXME: all of this implementation is a rough cut, including the fuzzy matching to decide what address should be the primary.
    # it's all open to change.

    def add_arguments(self, parser):
        parser.add_argument('-o', '--organization', dest='org', type=str, help='scan repositories from this organization', default=None)
        parser.add_argument('-r', '--repo', dest='repo', type=str, help='scan just this repository', default=None)
        parser.add_argument('-f', '--file', dest='file', type=str, help='input or output file', default=None)
        parser.add_argument('-p', '--plan', dest='plan', action='store_true', help='save the proposal to a file', default=False)
        parser.add_argument('-x', '--execute', dest='execute', action='store_true', help='load a proposal file into the aliases table', default=False)

    def pick_best(self, results):

        def do_select(item, results):
            return (item, [x for x in results if x != item])

        # first, try to capture organizational affiliation
        ORDER = [ "gmail.com", "hotmail.com", "fastmail.com", ".gov", ".edu", ".org"]
        for o in ORDER:
            for x in results:
                if o in x:
                    return do_select(x, results)

        # next try to capture company association, though a user may change companies
        for x in results:
            if x.endswith(".com") and not x.endswith("noreply.github.com"):
                return do_select(x, results)

        # try to find anything else
        options = [x for x in results if not x.startswith("root") and not x.endswith("noreply.github.com")]
        if len(options):
            do_select(options[0], results)

        # if that fails, get anything that isn't a "root" commit
        options = [x for x in results if not x.startswith("root")]
        if len(options):
            do_select(options[0], results)

        # there are no good options, don't write any aliases, because other users may commit as root.
        return (None, None)



    def handle(self, *args, **kwargs):

        org = kwargs.get('org', None)
        repo = kwargs.get('repo', None)
        file = kwargs.get('file', None)
        plan = kwargs.get('plan', None)
        execute = kwargs.get('execute', None)

        if not org or not repo:
            print("either -o or -r are required, or both")
        if not plan and not execute:
            raise CommandError("plan (-p) or execute (-x) are required")
        if not file:
            raise CommandError("file is required")


        if org:
            org = Organization.objects.get(name=org)
        if repo:
            repo = Repository.objects.get(name=repo)

        objs = Commit.objects

        if org:
            objs = objs.filter(
                repo__organization__name=org
            )
        if repo:
            objs = objs.filter(
                repo__name=repo
            )


        if plan:

            seen = dict()

            authors = objs.values_list('author', flat=True).distinct()
            count = authors.count()
            print("authors=%s" % authors)
            index = 0
            clones = 0

            report = dict()
            for i_author in authors.all():
                index = index + 1
                if index % 100 == 0:
                    print("%s/%s" % (index, count))
                author = Author.objects.get(pk=i_author)
                display_name = author.display_name
                matching = Author.objects.filter(display_name=display_name).exclude(pk=author.pk).exclude(display_name=None).all()
                seen[author.email] = 1
                if matching.count():
                    results = []
                    for match in matching:
                        if match.email not in seen:
                            clones = clones + 1
                            results.append(match.email)
                            print("MATCHED CLONE:", (author.email, match.display_name, match.email))
                            seen[match.email] = 1

                    if len(results):
                        results.append(author.email)
                        (primary, aliases) = self.pick_best(results)
                        if primary is not None:
                            report[primary] = aliases

            report = toml.dumps(report)
            print("total number of addresses to prune: %s" % clones)
            print("writing: %s" % file)
            fh = open(file,"w")
            fh.write(report)
            fh.close()

        if execute:

            fh = open(file, "r")
            data = fh.read()
            fh.close()

            data = toml.loads(data)

            print(data)

            for (k,v) in data.items():
                author = Author.objects.get(email=k)
                for alias in v:
                    print("processing email aliases: (%s) <= (%s)" % (author, alias))
                    alias_obj = Author.objects.get(email=alias)
                    alias_obj.alias_for = author
                    alias_obj.save()



