from django.core.management.base import BaseCommand, CommandError
from github import Github
import os


class Command(BaseCommand):
    help = 'creates repo objects from a github API endpoint'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--organization', dest='org', type=str, help='add repositories to this organization', default=None)

    def handle(self, *args, **kwargs):

        org = kwargs['org']
        if not org:
            raise CommandError("-o <organization name>" is required")

        org = Organization.get(name=org)

        if org.credential is None:
            raise CommandError("no credential is associated with this organization")

        handle = None
        if organization.credential.api_endpoint:
            handle = Github(scm_login.username, scm_login.password(), base_url=organization.credential.api_endpoint)
        else:
            handle = Github(scm_login.username, scm_login.get_password())


        github_repos = org.get_repos(type='all')
        for github_repo in github_repos:
            print(github_repo)


    #def fix_scm_url(self, repo, username):

        # Adds the username and password into the repo URL before checkout, if possible
        # This isn't needed if we are using SSH keys, and that's already handled by SshManager

    #    for prefix in ['https://', 'http://']:
    #        if repo.startswith(prefix):
    #            repo = repo.replace(prefix, "")
    #            return "%s%s@%s" % (prefix, username, repo)
    #    return repo