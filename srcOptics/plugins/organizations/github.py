import os
import subprocess
import re

class Repository:
    def clone_repo(repo_url, work_dir, repo_name):
        print('git clone ' + repo_url + ' ' + work_dir)
        os.system('git clone ' + repo_url + ' ' + work_dir + '/' + repo_name)

    def log_repo(repo_url, work_dir, repo_name):
        cmd = subprocess.Popen('cd ' + work_dir + '/' + repo_name + ';git log --all --stat', shell=True, stdout=subprocess.PIPE)
        regex = re.compile('^commit.*')
        for line in cmd.stdout:
            line = line.decode('utf-8')
            if regex.match(line):
                print(line)

    def scan_repo(repo_url):
        work_dir = os.path.abspath(os.path.dirname(__file__).rsplit("/", 2)[0]) + '/work'
        os.system('mkdir -p ' + work_dir)
        repo_name = repo_url.rsplit('/', 1)[1]
        Repository.clone_repo(repo_url, work_dir, repo_name)
        Repository.log_repo(repo_url, work_dir, repo_name)

