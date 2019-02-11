import os
import subprocess
import json
import getpass

from srcOptics.models import Commit, Repository, Author, Organization

class Scanner:
    # ------------------------------------------------------------------
    def clone_repo(repo_url, work_dir, repo_name, cred):

        flag = 0

        options = ""
        if cred is not None:
            options += ' --config core.username=\'' + cred.username + '\''
            options += ' --config core.askpass=\'' + cred.password + '\''

        #TODO: Need to pull all branches
        #TODO: Even if database is clean, if directory exists, it will pull
        if os.path.isdir(work_dir + '/' + repo_name) and os.path.exists(work_dir + '/' + repo_name):
            cmd = subprocess.Popen('cd ' + work_dir + '/' + repo_name + ';git pull', shell=True, stdout=subprocess.PIPE)
            # TODO: Need to find a better solution for checking if its up to date
            for line in cmd.stdout:
                line = line.decode('utf-8')
                if "Already up to date." in line:
                    flag = 1
                    break
            print('git pull ' + repo_url + ' ' + work_dir)
        else:
            os.system('git clone ' + repo_url + ' ' + work_dir + '/' + repo_name + options)
            print('git clone ' + repo_url + ' ' + work_dir)

        # TODO: Using literal string root for now...
        repo_instance = Scanner.create_repo('root', repo_url, repo_name, cred)
        return repo_instance, flag

    # ------------------------------------------------------------------
    def log_repo(repo_url, work_dir, repo_name, repo_instance):
        json_log = '\'{"commit":"%H","author_name":"%an","author_date":"%ad","commit_date":"%cd","author_email":"%ae"}\''
        cmd = subprocess.Popen('cd ' + work_dir + '/' + repo_name + ';git log --pretty=format:' + json_log, shell=True, stdout=subprocess.PIPE)

        for line in cmd.stdout:
            line = line.decode('utf-8')
            #print(line)
            data = json.loads(line)

            author_instance = Scanner.create_author(data['author_email'], data['author_name'])
            #TODO: Using 0 for lines added/removed
            commit_instance = Scanner.create_commit(repo_instance, author_instance, data['commit'], data['commit_date'], data['author_date'], 0, 0)

    # ------------------------------------------------------------------
    def scan_repo(repo_url, cred):
        work_dir = os.path.abspath(os.path.dirname(__file__).rsplit("/", 2)[0]) + '/work'
        os.system('mkdir -p ' + work_dir)
        repo_name = repo_url.rsplit('/', 1)[1]

        repo_instance, flag = Scanner.clone_repo(repo_url, work_dir, repo_name, cred)
        if flag == 0:
            Scanner.log_repo(repo_url, work_dir, repo_name, repo_instance)
        else:
            print("Already up to date.")
            flag = 0

    # ------------------------------------------------------------------
    def create_repo(org_name, repo_url, repo_name, cred):
        org_parent = Organization.objects.get(name=org_name)
        try:
            repo_instance = Repository.objects.get(name=repo_name)
        except:
            repo_instance = Repository.objects.create(cred=cred, url=repo_url, name=repo_name)
        return repo_instance

    # ------------------------------------------------------------------
    def create_author(email_, username_):
        try:
            author_instance = Author.objects.get(email=email_)
        except:
            author_instance = Author.objects.create(email=email_, username=username_)
        return author_instance

    # ------------------------------------------------------------------
    def create_commit(repo_instance, author_instance, sha_, author_date_, commit_date_, added, removed):
        try:
            commit_instance = Commit.objects.get(sha=sha_)
        except:
            commit_instance = Commit.objects.create(repo=repo_instance, author=author_instance, sha=sha_, commit_date=commit_date_, author_date=author_date_, lines_added=added, lines_removed=removed)
        return commit_instance

    # ------------------------------------------------------------------
    
