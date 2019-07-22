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

import os
import subprocess
import getpass
import re
import datetime
import traceback

from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.conf import settings
from .. models import *
from .. create import Creator
from django.db import transaction
from . import commands

GIT_TYPES = ["https://", "http://"]

#
# This class clones a repository (GIT) using a provided URL and credential
# and proceeds to execute git log on it to scan its data
#
class Checkout:

    # -----------------------------------------------------------------
    # Adds the github username into the URL, taken from Vespene code

    @classmethod
    def fix_repo_url(cls, repo):
        cred = repo.organization.credential
        repo_url = repo.url
        if not cred or not cred.username:
            return repo_url
        if "@" not in repo_url:
            for prefix in GIT_TYPES:
                if repo_url.startswith(prefix):
                    repo_url = repo_url.replace(prefix, "")
                    return "%s%s@%s" % (prefix, cred.username, repo_url)
        return repo_url


    # ------------------------------------------------------------------
    # Clones the repo if it doesn't exist in the work folder and pulls if it does

    @classmethod
    def clone_repo(cls, repo, work_dir):


        key_mgmt = None
        options = ""
        repo_name = repo.name
        repo
        repo_url = repo.url # FIXME: remove these short variables
        cred = repo.organization.credential
        repo_name = repo.name
        repo_url = cls.fix_repo_url(repo)
        dest_path = os.path.join(work_dir, repo_name)
        dest_git = os.path.join(dest_path, ".git")

        if repo_url.startswith("ssh://"):
            key_mgmt = {
                "GIT_SSH_COMMAND": "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no",
            }
            if not cred or not cred.ssh_private_key:
                raise Exception(
                    "add one or more SSH keys to the repo's assigned credential object or use a http:// or https:// URL")

        if os.path.isdir(dest_path) and os.path.exists(dest_path) and os.path.exists(dest_git):

            prev = os.getcwd()
            os.chdir(dest_path)
            # FIXME: command wrapper should take an optional cwd
            commands.execute_command(repo, "git pull", timeout=200, env=key_mgmt)
            os.chdir(prev)

        else:

            print("CREATING: %s" % dest_path)
            # os.makedirs can be a flakey in OS X, so shelling out
            commands.execute_command(repo, "mkdir -p %s" % dest_path, log=True, timeout=5)

            # on-disk repo doesn't exist yet, need to clone
            # FIXME: refactor into smaller functions

            key_mgmt = None
            cmd = f"git clone {repo_url} {dest_path} {options}"

            commands.execute_command(repo, cmd, log=False, timeout=600, env=key_mgmt)

        return repo


