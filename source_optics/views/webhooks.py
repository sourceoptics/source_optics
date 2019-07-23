#  Copyright 2018, Michael DeHaan LLC
#  License: Apache License Version 2.0
#  -------------------------------------------------------------------------
#  webhooks.py - implementation of webhook support.  Right now this isn't
#  pluggable and contains an implementation tested for GitHub and some
#  code that *probably* works for GitLab. Upgrades welcome.
#  --------------------------------------------------------------------------

import json

from ..models import Repository

# ===============================================================================================

class Webhooks(object):

    def __init__(self, request, token):

        body = request.body.decode('utf-8')
        self.token = token
        self.content = json.loads(body)

    def handle(self):
        """
        Invoked by views.py, recieves all webhooks and attempts to find out what
        projects correspond with them by looking at the repo.  If the project
        is webhook enabled, it will create a QUEUED build for that project.
        """

        # FIXME: at some point folks will want to support testing commits on branches
        # not set on the project.  This is a good feature idea, and to do this we
        # should add a webhooks_trigger_any_branch type option, that creates a build
        # with any incoming branch specified.

        possibles = []

        # this fuzzy code looks for what may come in for webhook JSON for GitHub and GitLab
        # extension to support other SCM webhooks is welcome.
        for section in [ 'project', 'repository' ]:
            if section in self.content:
                for key in [ 'git_url', 'ssh_url', 'clone_url', 'git_ssh_url', 'git_http_url' ]:
                    repo = self.content[section].get(key, None)
                    if repo is not None:
                        possibles.append(repo)

        # find projects that match repos we have detected
        qs = Repository.objects.filter(organization__webhook_enabled=True, url__in=possibles)
        for repo in qs:
            if not repo.enabled:
                continue
            if repo.webhook_token is None or (repo.organization.webhook_token == self.token) or repo.webhook_token == self.token:
                repo.force_next_pull = True
                repo.save()
