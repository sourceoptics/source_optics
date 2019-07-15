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

from django.core.management.base import BaseCommand, CommandError
from ... stats.rollup import Rollup
from ... models import *

#
# The stat management command is used to generate statistics for an
# already cloned repository. The user must provide the repository name
# as a single parameter.
#
class Command(BaseCommand):
    help = 'Generates tabular statistics off of the job queue'

    def add_arguments(self, parser):
        parser.add_argument('repo_name', type=str, help='Repository Name')

    def handle(self, *args, **kwargs):
        repo = Repository.objects.get(name=kwargs['repo_name'])
        Rollup.rollup_repo(repo=repo)
