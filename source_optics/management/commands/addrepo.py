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

# FIXME: the "add repo" command should be split from the github import command, and there
# will likely be a seperate management command for gitlab import.

from django.core.management.base import BaseCommand, CommandError

from ... scanner.checkout import Scanner
from ... models import *
import getpass
import requests
import json

#
# The addrepo management command is used to add a repository to the
# database. The user should pass in the URL as the only parameter
#
class Command(BaseCommand):
    help = 'Adds repositories and scans them'

    def add_arguments(self, parser):
        parser.add_argument('-r', '--repo_url', type=str, help='Scan a single repository')
        parser.add_argument('-f', '--repo_file', type=str, help='Scan repositories from a newline delimited list in a file')

        parser.add_argument('-g',
                            '--github_api',
                            type=str,
                            dest='github_url',
                            help='Scan all repositories in the api endpoint')
        
    def handle(self, *args, **kwargs):

        if len(kwargs) == 0:
            print('No options specified. Please see --help')
            print('  Ex: python manage.py addrepo -r <repo_url>')
            return

        # get the VC credentials and make a LoginCredential before cloning
        username = input('Username: ')
        password = getpass.getpass('Password: ')
        cred = LoginCredential.objects.create(username=username, password=password)

        if kwargs['repo_url']:
            # if the repo exists, grab its name in case it is not standard
            try:
                repo_name = Repository.objects.get(url=kwargs['repo_url']).name
            except Repository.DoesNotExist:
                repo_name = None

            # Scan the repository, passing in the URL and LoginCredential
            Scanner.scan_repo(kwargs['repo_url'], repo_name, cred)


        # Grab a list of repository urls (html_url) from a github
        # API endpoint. The api returns a JSON string, which we can
        # iterate through to get url lists to add.
        #
        # You can use this command with any api point that has
        # a list of 'html_url' entries.
        #
        # Get repositories for a user: https://api.github.com/users/name/repos
        if kwargs['github_url']:
            # GET json data for the api url
            api = requests.get(kwargs['github_url'], auth=(username, password))
            # array of objects for each repo
            data = json.loads(api.text)

            for entry in data:
                Scanner.scan_repo(entry['html_url'], entry['name'], cred)


        # load repositories from a file and scan them
        if kwargs['repo_file']:
            with open(kwargs['repo_file']) as f:
                for line in f:
                    Scanner.scan_repo(line.strip(), None, cred)
