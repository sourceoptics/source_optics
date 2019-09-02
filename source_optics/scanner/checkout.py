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

import os
import traceback

from . import commands

GIT_TYPES = ["https://", "http://"]

#
# This class clones a repository (GIT) using a provided URL and credential
# and proceeds to execute git log on it to scan its data
#
class Checkout:

    @classmethod
    def fix_repo_url(cls, repo):
        """
        adds the github username into the URL
        """
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

    @classmethod
    def clone_repo(cls, repo, work_dir):
        """
        Clones the repo if it doesn't exist in the work folder and pulls if it does
        """

        key_mgmt = None
        options = ""
        cred = repo.organization.credential
        repo_url = cls.fix_repo_url(repo)
        dest_git = os.path.join(work_dir, ".git")

        if repo_url.startswith("ssh://"):
            key_mgmt = {
                "GIT_SSH_COMMAND": "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no",
            }
            if not cred or not cred.ssh_private_key:
                raise Exception(
                    "add one or more SSH keys to the repo's assigned credential object or use a http:// or https:// URL")

        if os.path.exists(dest_git):

            prev = os.getcwd()
            os.chdir(work_dir)
            # FIXME: command wrapper should take an optional cwd to make this cleaner

            try:
                commands.execute_command(repo, "git pull", timeout=200, env=key_mgmt)
            except Exception:
                # FIXME: finer grained catch here
                traceback.print_exc()
                print("checkout failure, possibly no commits yet?, skipping")
                return False

            os.chdir(prev)

        else:

            print("CREATING: %s" % work_dir)
            # os.makedirs can be a flakey in OS X, so shelling out
            commands.execute_command(repo, "mkdir -p %s" % work_dir, log=True, timeout=5)

            # on-disk repo doesn't exist yet, need to clone

            key_mgmt = None
            cmd = f"git clone {repo_url} {work_dir} {options}"

            commands.execute_command(repo, cmd, log=False, timeout=600, env=key_mgmt)

        return True
