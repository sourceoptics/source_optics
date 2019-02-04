import os
import subprocess
import json

from srcOptics.models import Commit, Repository, Author, Organization

class Scanner:
    def clone_repo(repo_url, work_dir, repo_name):

        flag = 0

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
            os.system('git clone ' + repo_url + ' ' + work_dir + '/' + repo_name)
            print('git clone ' + repo_url + ' ' + work_dir)

        # TODO: Using literal string root for now...
        repo_instance = Scanner.create_repo('root', repo_url, repo_name)
        return repo_instance, flag

    def log_repo(repo_url, work_dir, repo_name, repo_instance):
        json_log = '\'{"commit":"%H","author":"%an","date":"%cd","email":"%ce"}\''
        cmd = subprocess.Popen('cd ' + work_dir + '/' + repo_name + ';git log --pretty=format:' + json_log, shell=True, stdout=subprocess.PIPE)

        for line in cmd.stdout:
            line = line.decode('utf-8')
            #print(line)
            data = json.loads(line)

            author_instance = Scanner.create_author(data['author'], data['email'])
            #TODO: Using 0 for lines added/removed
            commit_instance = Scanner.create_commit(repo_instance, author_instance, data['commit'], 0, 0)

    def scan_repo(repo_url):
        work_dir = os.path.abspath(os.path.dirname(__file__).rsplit("/", 2)[0]) + '/work'
        os.system('mkdir -p ' + work_dir)
        repo_name = repo_url.rsplit('/', 1)[1]

        repo_instance, flag = Scanner.clone_repo(repo_url, work_dir, repo_name)
        if flag == 0:
            Scanner.log_repo(repo_url, work_dir, repo_name, repo_instance)
        else:
            print("Already up to date.")
            flag = 0

    def create_repo(org_name, repo_url, repo_name):
        org_parent = Organization.objects.get(name=org_name)
        try:
            repo_instance = Repository.objects.get(name=repo_name)
        except:
            repo_instance = Repository.objects.create(parent=org_parent, url=repo_url, name=repo_name)
        return repo_instance

    def create_author(email_, username_):
        try:
            author_instance = Author.objects.get(email=email_)
        except:
            author_instance = Author.objects.create(email=email_, username=username_)
        return author_instance

    def create_commit(repo_instance, author_instance, sha_, added, removed):
        try:
            commit_instance = Commit.objects.get(sha=sha_)
        except:
            commit_instance = Commit.objects.create(repo=repo_instance, author=author_instance, sha=sha_, lines_added=added, lines_removed=removed)
        return commit_instance
