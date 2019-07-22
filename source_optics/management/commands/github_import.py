from django.core.management.base import BaseCommand, CommandError
from github import Github
from ... models import Organization, Repository
import fnmatch

class Command(BaseCommand):
    help = 'creates repo objects from a github API endpoint'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--organization', dest='org', type=str, help='add repositories to this organization', default=None)

    def handle(self, *args, **kwargs):

        org = kwargs['org']
        if not org:
            raise CommandError("-o <organization name> is required")

        org = Organization.objects.get(name=org)

        credential = org.credential
        if credential is None:
            raise CommandError("no credential is associated with this organization")

        handle = None


        if credential.api_endpoint:
            handle = Github(credential.username, credential.unencrypt_password(), base_url=credential.api_endpoint)
        else:
            handle = Github(credential.username, credential.unencrypt_password())
        github_org = handle.get_organization(credential.organization_identifier)

        github_repos = github_org.get_repos(type='all')
        for github_repo in github_repos:
            #print(github_repo)
            #print(dir(github_repo))
            #print(github_repo.name)
            #print(github_repo.ssh_url)

            filter = credential.import_filter
            if filter and not fnmatch.fnmatch(github_repo.name, filter):
                print("repo (%s) doesn't match fnmatch filter (%s), skipping" % (github_repo.name, filter))
                continue

            (repo, created) = Repository.objects.get_or_create(
                name=github_repo.name,
                organization=org,
                defaults=dict(
                    url=github_repo.ssh_url
                )
            )
            if created:
                print("created: %s" % repo)
            else:
                print("already existed: %s" % repo)



    #def fix_scm_url(self, repo, username):

        # Adds the username and password into the repo URL before checkout, if possible
        # This isn't needed if we are using SSH keys, and that's already handled by SshManager

    #    for prefix in ['https://', 'http://']:
    #        if repo.startswith(prefix):
    #            repo = repo.replace(prefix, "")
    #            return "%s%s@%s" % (prefix, username, repo)
    #    return repo