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

from django.core.management.base import BaseCommand

from ...scanner.processor import RepoProcessor


#
# The scan management command is used to kick of the daemon job which
# checks for enabled repositories which should be scanned and parsed
# for statistics 
#
class Command(BaseCommand):

    help = 'Scans one or more repositories'

    def add_arguments(self, parser):

        parser.add_argument('-o', '--organization_pattern',
                            dest='org',
                            type=str,
                            help='Only process organizations with this substring',
                            default=None)
        parser.add_argument('-r', '--repo_pattern',
                            dest='repo',
                            type=str,
                            help='Only process repositories with this substring',
                            default=None)
        parser.add_argument('-F', '--force-nuclear-rescan',
                            dest='force_nuclear_rescan',
                            action='store_true',
                            help='DANGER: Delete all selected repos and do a full rescan')

    def handle(self, *args, **kwargs):

        organization_filter = kwargs['org']
        repository_filter = kwargs['repo']
        force_nuclear_rescan = kwargs['force_nuclear_rescan']

        RepoProcessor.scan(organization_filter=organization_filter,
                           repository_filter=repository_filter,
                           force_nuclear_rescan=force_nuclear_rescan)
